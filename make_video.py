"""금호타이어 송월점 유튜브 숏츠 / 인스타 릴스 자동 제작

사용법:
  python3 make_video.py                 # 전체 렌더 (output/kumho_songwol_shorts.mp4)
  python3 make_video.py --engine espeak # 나레이션 엔진 강제
  python3 make_video.py --preview 1.5 4 10   # 지정 초의 프레임만 PNG 로 미리보기
"""
import argparse
import json
import os
import subprocess

import audio
import narration
import video

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "output")

# 자막 청크 ( *강조* = 노란색 )
CHUNKS = [
    ["타이어 바꾸실 때,", "*가격*만 보세요?"],
    ["*잠깐!*", "타이어는 가격도 중요하지만", "*내 차에 맞는 선택*이", "더 중요합니다!"],
    ["타이어 *상태*부터 *마모*,", "*휠얼라인먼트*까지", "*꼼꼼하게!*"],
    ["*금호타이어 전문점!*", "내 차에 맞는 타이어를", "*합리적으로!*"],
    ["*교환*부터 *휠얼라인먼트*까지", "*한곳에서!*"],
    ["타이어 교환 고민 중이세요?", "나주 *금호타이어 송월점!*", "지금 *상담*해 보세요!"],
]
GAP = 0.42      # 대사 사이 호흡
LEAD = 0.30     # 첫 대사 시작
TAIL = 2.6      # 마지막 대사 후 엔딩 카드 유지


def weight(s):
    s = s.replace("*", "")
    return len(s.replace(" ", "")) + 2.5 * sum(s.count(p) for p in ",!?")


def build_timeline(durs):
    starts, t = [], LEAD
    for d in durs:
        starts.append(round(t, 3))
        t += d + GAP
    total = round(starts[-1] + durs[-1] + TAIL, 2)
    scene_starts = [0.0] + [round(s - 0.15, 3) for s in starts[1:]]
    chunks = []
    for i, (st, d) in enumerate(zip(starts, durs)):
        ws = [weight(c) for c in CHUNKS[i]]
        acc, cl = st, []
        for j, (c, w) in enumerate(zip(CHUNKS[i], ws)):
            dd = d * w / sum(ws)
            end = acc + dd
            # 다음 대사 직전까지 자막 유지 (마지막 대사는 영상 끝까지)
            if j == len(ws) - 1:
                end = (starts[i + 1] - 0.02) if i + 1 < len(starts) else total
            cl.append((round(acc, 3), round(end, 3), c))
            acc += dd
        chunks.append(cl)
    shakes = [(chunks[0][1][0], 1.0), (scene_starts[1], 1.0), (scene_starts[3], 0.8),
              (chunks[4][1][0], 0.8), (chunks[5][1][0], 0.9)]
    return dict(total=total, line_starts=starts, line_durs=durs, scene_starts=scene_starts,
                chunks=chunks, shakes=shakes)


def sfx_events(tl):
    c, s = tl["chunks"], tl["scene_starts"]
    ev = [
        (0.05, "whoosh", 0.8, -0.3),
        (c[0][1][0] - 0.05, "impact", 0.9, 0),
        (0.3, "pop", 0.6, 0.4),
        (c[0][1][0] + 0.35, "pop", 0.7, 0),
        (s[1] - 0.35, "riser", 0.5, 0),
        (s[1], "stop", 1.0, 0), (s[1], "impact", 0.7, 0),
        (c[1][1][0], "whoosh", 0.6, 0.4),
        (c[1][2][0], "pop", 0.8, 0), (c[1][3][0], "ding", 0.7, 0),
        (s[2] - 0.2, "whoosh", 0.8, 0),
        (s[2] + 0.05, "click", 0.7, 0),
    ]
    k0, k1, k2 = c[2][0][0], c[2][1][0], c[2][2][0]
    for tt in (k0 + 0.1, k0 + 0.55 * (k1 - k0), k1):
        ev += [(tt, "whoosh_down", 0.45, 0.5), (tt + 0.3, "pop", 0.8, 0)]
    ev += [(k2, "ding", 0.6, 0),
           (s[3] - 0.2, "whoosh", 0.8, 0), (s[3], "impact", 0.85, 0),
           (s[3] + 0.2, "whoosh", 0.5, 0),
           (c[3][2][0] - 0.1, "whoosh", 0.7, -0.4), (c[3][2][0] + 0.25, "cash", 0.8, 0),
           (s[4] - 0.2, "whoosh", 0.8, 0)]
    for i in range(4):
        ev.append((s[4] + 0.15 + 0.28 * i, "pop", 0.7, (-0.4, 0.4)[i % 2]))
    ev += [(c[4][1][0], "impact", 0.8, 0), (c[4][1][0] + 0.1, "ding", 0.5, 0),
           (s[5] - 0.6, "riser", 0.6, 0), (s[5] - 0.15, "whoosh", 0.8, 0),
           (c[5][1][0], "impact", 0.9, 0), (c[5][1][0] + 0.45, "pop", 0.8, 0),
           (c[5][1][0] + 0.8, "click", 0.6, 0),
           (c[5][2][0] - 0.3, "pop", 0.8, 0.3), (tl["total"] - 1.6, "ding", 0.55, 0)]
    return ev


def write_srt(tl, path):
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    rows = [c for line in tl["chunks"] for c in line]
    with open(path, "w", encoding="utf-8") as f:
        for i, (st, en, txt) in enumerate(rows, 1):
            f.write(f"{i}\n{ts(st)} --> {ts(en)}\n{txt.replace('*', '')}\n\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="auto", choices=["auto", "files", "openai", "espeak"])
    ap.add_argument("--preview", nargs="*", type=float)
    a = ap.parse_args()
    os.makedirs(BUILD, exist_ok=True); os.makedirs(OUT, exist_ok=True)

    tl_path = os.path.join(BUILD, "timeline.json")
    if a.preview is not None and os.path.exists(tl_path):
        tl = json.load(open(tl_path))
        video.TL = tl
        for s in a.preview:
            p = os.path.join(BUILD, f"preview_{s:05.2f}.png")
            video.frame(int(s * video.FPS)).save(p)
            print(p)
        return

    engine, durs = narration.generate(BUILD, a.engine)
    tl = build_timeline(durs)
    tl["engine"] = engine
    json.dump(tl, open(tl_path, "w"), ensure_ascii=False, indent=1)
    print(f"[timeline] total {tl['total']}s, lines at {tl['line_starts']}")

    mix = os.path.join(BUILD, "mix.wav")
    audio.build_mix(tl["total"], [os.path.join(BUILD, f"narr_{i:02d}.wav") for i in range(len(durs))],
                    tl["line_starts"], sfx_events(tl), mix)
    print("[audio] mix done")

    vid = video.render(tl, BUILD)
    print("[video] frames done")

    final = os.path.join(OUT, "kumho_songwol_shorts.mp4")
    subprocess.check_call([
        "ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", mix,
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-movflags", "+faststart", "-shortest", final])
    write_srt(tl, os.path.join(OUT, "kumho_songwol_shorts.srt"))
    print("[done]", final)


if __name__ == "__main__":
    main()
