"""녹음 파일에서 손뼉을 찾아 '손뼉 바로 앞 문장'을 버리고, 남은 문장만 이어 붙인다.

녹음 규칙 (CLAUDE.md)
- 문장 사이는 2초 쉰다.
- 틀리면 손뼉을 치고 그 문장을 다시 읽는다. 손뼉 앞의 그 문장은 버린다.

처리 순서
1. ffmpeg로 44.1kHz 모노로 읽는다.
2. 손뼉 찾기: 10ms 단위로 2kHz 위 대역 에너지를 보고, 갑자기 크게 튀고(직전보다 +18dB)
   고역 비율이 높으며 0.3초 안에 끝나는 소리를 찾는다. 말소리 속 센 자음·입소리와 헷갈리지
   않도록 소리 전체의 중심 주파수가 1.5kHz 이상이고, 앞 0.15초와 뒤 0.25초가 조용할(-40dBFS
   미만) 때만 손뼉으로 본다. 손뼉을 안 쳤으면 --no-clap으로 끈다.
3. 손뼉 구간을 뺀 나머지에서 말소리 조각을 찾고, 쉼이 --sentence-gap(기본 1.0초) 이상이거나
   사이에 손뼉이 있으면 다른 문장으로 나눈다.
4. 손뼉마다 그 직전 문장 하나를 버린다(연속으로 틀려도 손뼉 수만큼 하나씩).
5. 남은 문장을 --gap(기본 0.6초) 간격으로 이어 voice_clean.wav로 저장하고,
   문장별 wav, report.json, report.md(한국어 확인표)를 남긴다.
   --script를 주면 대본 문장 수와 맞는지, 문장마다 길이가 그럴듯한지(초당 음절) 확인한다.

사용법
  python3 tools/clap_cut.py 녹음.m4a --script docs/ep01_gak_grandeur_script.md
  python3 tools/clap_cut.py 녹음.m4a --expect 13 --out build/ep01_voice
"""
import argparse
import json
import os
import re
import subprocess
import sys
import wave

import numpy as np

SR = 44100
HOP = 441            # 10ms
WIN = 1024


def load(path):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                                   "-f", "f32le", "-"])
    return np.frombuffer(raw, np.float32).copy()


def save_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def frame_feats(x):
    n = max(0, (len(x) - WIN) // HOP + 1)
    idx = np.arange(WIN)[None, :] + HOP * np.arange(n)[:, None]
    fr = x[idx] * np.hanning(WIN)
    S = np.abs(np.fft.rfft(fr, axis=1)) ** 2
    f = np.fft.rfftfreq(WIN, 1 / SR)
    tot = S.sum(1) + 1e-12
    hf = S[:, f >= 2000].sum(1)
    db = 10 * np.log10(tot / WIN + 1e-12)          # 프레임 전체 에너지(dB, 상대값)
    hf_db = 10 * np.log10(hf / WIN + 1e-12)
    ratio = hf / tot
    rms_db = 20 * np.log10(np.sqrt((x[idx] ** 2).mean(1)) + 1e-9)   # dBFS
    return rms_db, hf_db, ratio


def centroid(x, i, j):
    seg = x[i * HOP:(j * HOP + WIN)]
    S = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
    f = np.fft.rfftfreq(len(seg), 1 / SR)
    return (S * f).sum() / (S.sum() + 1e-12)


def find_claps(x, rms_db, hf_db, ratio, min_level=-35.0, jump=18.0, min_ratio=0.25, max_len=0.30,
               quiet=-40.0, min_cent=1500.0):
    """손뼉 시작 프레임 목록과 [시작, 끝) 프레임 구간."""
    claps = []
    n = len(rms_db)
    i = 3
    while i < n:
        before = hf_db[max(0, i - 4):i - 1].max() if i >= 2 else -120
        if hf_db[i] - before >= jump and ratio[i] >= min_ratio and rms_db[i:i + 3].max() >= min_level:
            # 끝: 고역 에너지가 시작보다 25dB 떨어지거나 max_len 초과
            peak = hf_db[i:i + 3].max()
            j = i + 1
            while j < n and hf_db[j] > peak - 25 and (j - i) * HOP / SR < max_len + 0.05:
                j += 1
            length = (j - i) * HOP / SR
            # 말소리 위 순간 잡음과 구분: 짧고, 고역 비율이 높은 상태로 끝나야 한다
            q = int(0.15 * SR / HOP)
            quiet_before = rms_db[max(0, i - q - 1):max(0, i - 1)].max(initial=-120) < quiet
            quiet_after = rms_db[j + 1:j + 1 + int(0.25 * SR / HOP)].max(initial=-120) < quiet
            if length <= max_len and quiet_before and quiet_after and centroid(x, i, j) >= min_cent:
                claps.append((i, j))
                i = j + 5
                continue
        i += 1
    return claps


def speech_runs(rms_db, mask, thresh, merge=0.15, min_len=0.06):
    on = (rms_db > thresh) & ~mask
    runs, i, n = [], 0, len(on)
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            runs.append([i, j])
            i = j
        else:
            i += 1
    merged = []
    for r in runs:
        if merged and (r[0] - merged[-1][1]) * HOP / SR < merge and not mask[merged[-1][1]:r[0]].any():
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [r for r in merged if (r[1] - r[0]) * HOP / SR >= min_len]


def group_sentences(runs, claps, gap):
    clap_starts = [c[0] for c in claps]
    sents = []
    for r in runs:
        if sents:
            last = sents[-1]
            between = any(last[1] <= c < r[0] for c in clap_starts)
            if not between and (r[0] - last[1]) * HOP / SR < gap:
                last[1] = r[1]
                continue
        sents.append([r[0], r[1]])
    return sents


def atempo(seg, tempo):
    """음 높이는 그대로, 속도만 tempo배 (ffmpeg atempo)."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", f"atempo={tempo}", "-f", "f32le", "-"], input=seg.astype(np.float32).tobytes(),
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


def align(kept, sents, syl, max_join=3, max_skip=0.6, target=4.0):
    """조각들을 대본 문장에 순서대로 배정한다. 한 문장에 연속 조각 1~max_join개,
    max_skip초 미만 조각은 잡음으로 건너뛸 수 있다. 초당 음절이 target에 가깝게."""
    import math
    from functools import lru_cache
    N, M = len(kept), len(syl)
    st = [sents[k][0] * HOP / SR for k in kept]
    en = [sents[k][1] * HOP / SR for k in kept]
    INF = float("inf")

    @lru_cache(None)
    def f(i, m):
        if m == M:                          # 문장을 다 배정한 뒤 남은 짧은 잡음은 건너뜀
            if i == N:
                return (0.0, ())
            if en[i] - st[i] < max_skip:
                v, p = f(i + 1, m)
                return (v + 0.3, (("skip", i),) + p)
            return (INF, ())
        if i >= N:
            return (INF, ())
        best = (INF, ())
        if en[i] - st[i] < max_skip:
            v, p = f(i + 1, m)
            best = min(best, (v + 0.3, (("skip", i),) + p))
        for j in range(i + 1, min(N, i + max_join) + 1):
            v, p = f(j, m + 1)
            dur = en[j - 1] - st[i]
            c = math.log(syl[m] / dur / target) ** 2 + 0.05 * (j - i - 1)
            # 문장 사이 쉼(규칙상 2초)만큼 떨어진 조각은 같은 문장으로 묶지 않는다
            if any(st[q + 1] - en[q] > 1.8 for q in range(i, j - 1)):
                c += 5
            best = min(best, (v + c, (("line", i, j),) + p))
        return best

    v, path = f(0, 0)
    if v == INF:
        return None
    groups, skipped = [], []
    for step in path:
        if step[0] == "skip":
            skipped.append(kept[step[1]])
        else:
            groups.append([kept[q] for q in range(step[1], step[2])])
    return groups, set(skipped)


def script_lines(path):
    """대본 md의 '녹음용 대본' 표에서 대사 열을 읽는다."""
    lines = []
    for ln in open(path, encoding="utf-8"):
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0].isdigit():
            lines.append(cells[2])
    return lines


def syllables(s):
    return len(re.findall("[가-힣]", s))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--out", default=None, help="결과 폴더 (기본: build/<파일 이름>)")
    ap.add_argument("--script", help="대본 md (녹음용 대본 표)")
    ap.add_argument("--expect", type=int, help="기대 문장 수 (--script 대신)")
    ap.add_argument("--thresh", type=float, default=-38.0, help="말소리 판정 dBFS (기본 -38)")
    ap.add_argument("--sentence-gap", type=float, default=1.0, help="이 이상 쉬면 다음 문장 (기본 1.0초)")
    ap.add_argument("--gap", type=float, default=0.6, help="이어 붙일 때 문장 사이 쉼 (기본 0.6초)")
    ap.add_argument("--no-clap", action="store_true", help="손뼉 감지를 끄고 쉼으로만 문장을 나눈다")
    ap.add_argument("--inner-pause", type=float, default=0.35, help="문장 안 쉼의 최대 길이 (기본 0.35초)")
    ap.add_argument("--tempo", type=float, default=1.0, help="말 속도 배율, 음 높이 유지 (예: 1.12)")
    ap.add_argument("--limit", type=float, default=58.0, help="이 길이를 넘으면 경고 (기본 58초)")
    ap.add_argument("--pre", type=float, default=0.08)
    ap.add_argument("--post", type=float, default=0.15)
    a = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    name = os.path.splitext(os.path.basename(a.input))[0]
    out = a.out or os.path.join(root, "build", name)
    os.makedirs(out, exist_ok=True)

    x = load(a.input)
    rms_db, hf_db, ratio = frame_feats(x)
    claps = [] if a.no_clap else find_claps(x, rms_db, hf_db, ratio)
    mask = np.zeros(len(rms_db), bool)
    for s, e in claps:
        mask[max(0, s - 2):e + 3] = True
    runs = speech_runs(rms_db, mask, a.thresh)
    sents = group_sentences(runs, claps, a.sentence_gap)

    dropped = set()
    for cs, _ in claps:
        before = [k for k, (s, e) in enumerate(sents) if e <= cs + 1 and k not in dropped]
        if before:
            dropped.add(before[-1])
    kept = [k for k in range(len(sents)) if k not in dropped]

    t = lambda f: round(f * HOP / SR, 2)
    expected = script_lines(a.script) if a.script else None
    n_expect = len(expected) if expected else a.expect

    # 대본 문장 수와 다르면, 길이로 맞춰 본다(문장 안에서 오래 쉰 조각은 합치고, 짧은 잡음은 건너뜀)
    groups = [[k] for k in kept]
    skipped, aligned = [], False
    if expected and len(kept) != len(expected):
        res = align(kept, sents, [syllables(l) for l in expected])
        if res:
            groups, skipped = res
            aligned = True

    # 이어 붙이기: 문장 안의 긴 쉼은 --inner-pause로 줄이고, --tempo배로 빠르게(음 높이 유지)
    pieces, timeline, cur = [], [], 0.0
    fade = int(0.01 * SR)
    for i, g in enumerate(groups):
        s0, e0 = sents[g[0]][0], sents[g[-1]][1]
        inner = [r for r in runs if r[0] >= s0 and r[1] <= e0]
        parts = []
        for j, (rs, re_) in enumerate(inner):
            lo = int(rs * HOP - (a.pre * SR if j == 0 else 0.04 * SR))
            hi = int(re_ * HOP + WIN + (a.post * SR if j == len(inner) - 1 else 0.04 * SR))
            seg = x[max(0, lo):min(len(x), hi)].copy()
            if j:
                pause = (rs - inner[j - 1][1]) * HOP / SR
                parts.append(np.zeros(int(min(pause, a.inner_pause) * SR), np.float32))
            parts.append(seg)
        seg = np.concatenate(parts)
        if abs(a.tempo - 1) > 1e-3:
            seg = atempo(seg, a.tempo)
        seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
        save_wav(os.path.join(out, f"sentence_{i + 1:02d}.wav"), seg)
        d = len(seg) / SR
        timeline.append({"no": i + 1, "start": round(cur, 3), "end": round(cur + d, 3),
                         "source": [t(s0), t(e0)],
                         "line": expected[i] if expected and len(groups) == len(expected) else None})
        pieces.append(seg)
        cur += d + a.gap
    if pieces:
        gz = np.zeros(int(a.gap * SR), np.float32)
        voice = np.concatenate(sum(([p, gz] for p in pieces), [])[:-1])
        save_wav(os.path.join(out, "voice_clean.wav"), voice)
        total = len(voice) / SR
    else:
        total = 0.0

    # 확인표
    rows, warn = [], []
    gid = {k: i + 1 for i, g in enumerate(groups) for k in g}
    for k, (s, e) in enumerate(sents):
        if k in dropped:
            state = "버림(손뼉 앞)"
        elif k in skipped:
            state = "건너뜀(짧은 잡음)"
        else:
            state = f"사용 → 대본 {gid[k]}번" if aligned else "사용"
        rows.append((k + 1, t(s), t(e), round(t(e) - t(s), 2), state))
    if n_expect is not None and len(groups) != n_expect:
        warn.append(f"남은 문장 {len(groups)}개 ≠ 대본 {n_expect}문장. 쉼이 짧았거나 손뼉을 못 찾았을 수 있습니다.")
    if aligned:
        warn.append("조각 수가 대본과 달라 길이로 자동으로 맞췄습니다. 문장별 파일을 들어 보고 확인해 주세요.")
    checks = []
    if expected and len(groups) == len(expected):
        for i, (g, line) in enumerate(zip(groups, expected)):
            dur = t(sents[g[-1]][1]) - t(sents[g[0]][0])
            rate = syllables(line) / dur if dur > 0 else 0
            ok = 2.3 <= rate <= 9.0
            checks.append({"no": i + 1, "line": line, "sec": round(dur, 2), "syll_per_sec": round(rate, 1), "ok": ok})
            if not ok:
                warn.append(f"{i + 1}번 문장 길이가 대본과 안 맞아 보입니다(초당 {rate:.1f}음절): {line}")
    if a.limit and total > a.limit:
        warn.append(f"이어 붙인 길이 {total:.1f}초가 {a.limit:.0f}초를 넘습니다. --tempo를 올리거나 --gap·--inner-pause를 줄이세요.")

    report = {"input": a.input, "claps": [t(c[0]) for c in claps],
              "sentences": [{"no": r[0], "start": r[1], "end": r[2], "state": r[4]} for r in rows],
              "settings": {"gap": a.gap, "inner_pause": a.inner_pause, "tempo": a.tempo},
              "kept_timeline": timeline, "total_sec": round(total, 2), "checks": checks, "warnings": warn}
    json.dump(report, open(os.path.join(out, "report.json"), "w"), ensure_ascii=False, indent=1)

    md = [f"# 녹음 정리 결과: {os.path.basename(a.input)}", "",
          f"- 손뼉 {len(claps)}번: " + (", ".join(f"{t(c[0])}초" for c in claps) or ("감지 끔" if a.no_clap else "없음")),
          f"- 찾은 조각 {len(sents)}개 → 버림 {len(dropped)}개, 건너뜀 {len(skipped)}개, 문장 {len(groups)}개"
          + (f" (대본 {n_expect}문장)" if n_expect else ""),
          f"- 이어 붙인 길이: **{total:.1f}초** (문장 사이 {a.gap}초, 문장 안 쉼 최대 {a.inner_pause}초, 속도 {a.tempo}배)", "",
          "| 조각 | 원본 시작 | 원본 끝 | 길이 | 처리 |", "|---|---|---|---|---|"]
    md += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |" for r in rows]
    if checks:
        md += ["", "| 대본 # | 대사 | 원본 길이(초) | 초당 음절 | 확인 |", "|---|---|---|---|---|"]
        md += [f"| {c['no']} | {c['line']} | {c['sec']} | {c['syll_per_sec']} | {'✓' if c['ok'] else '확인 필요'} |"
               for c in checks]
    if warn:
        md += ["", "## 확인할 것"] + [f"- {w}" for w in warn]
    open(os.path.join(out, "report.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\n결과 폴더: {out}")
    return 1 if warn else 0


if __name__ == "__main__":
    sys.exit(main())
