"""녹음 파일에서 손뼉을 찾아 '손뼉 바로 앞 문장'을 버리고, 남은 문장만 이어 붙인다.

녹음 규칙 (CLAUDE.md)
- 문장 사이는 2초 쉰다.
- 틀리면 손뼉을 치고 그 문장을 다시 읽는다. 손뼉 앞의 그 문장은 버린다.

처리 순서
1. ffmpeg로 44.1kHz 모노로 읽는다.
2. 손뼉 찾기: 10ms 단위로 2kHz 위 대역 에너지를 보고, 갑자기 크게 튀고(직전보다 +18dB)
   고역 비율이 높으며 0.3초 안에 끝나는 소리를 손뼉으로 본다. 말소리는 에너지가 대부분
   1kHz 아래라 고역 비율이 낮다.
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


def find_claps(rms_db, hf_db, ratio, min_level=-35.0, jump=18.0, min_ratio=0.25, max_len=0.30):
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
            if length <= max_len:
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
    ap.add_argument("--pre", type=float, default=0.08)
    ap.add_argument("--post", type=float, default=0.15)
    a = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    name = os.path.splitext(os.path.basename(a.input))[0]
    out = a.out or os.path.join(root, "build", name)
    os.makedirs(out, exist_ok=True)

    x = load(a.input)
    rms_db, hf_db, ratio = frame_feats(x)
    claps = find_claps(rms_db, hf_db, ratio)
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

    # 이어 붙이기
    pieces, timeline, cur = [], [], 0.0
    for i, k in enumerate(kept):
        s, e = sents[k]
        lo = max(0, int((s * HOP / SR - a.pre) * SR))
        hi = min(len(x), int((e * HOP / SR + WIN / SR + a.post) * SR))
        seg = x[lo:hi].copy()
        fade = int(0.01 * SR)
        seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
        save_wav(os.path.join(out, f"sentence_{i + 1:02d}.wav"), seg)
        d = len(seg) / SR
        timeline.append({"no": i + 1, "start": round(cur, 3), "end": round(cur + d, 3),
                         "source": [t(s), t(e)]})
        pieces.append(seg)
        cur += d + a.gap
    if pieces:
        g = np.zeros(int(a.gap * SR), np.float32)
        voice = np.concatenate(sum(([p, g] for p in pieces), [])[:-1])
        save_wav(os.path.join(out, "voice_clean.wav"), voice)
        total = len(voice) / SR
    else:
        total = 0.0

    # 확인표
    rows, warn = [], []
    for k, (s, e) in enumerate(sents):
        state = "버림(손뼉 앞)" if k in dropped else "사용"
        rows.append((k + 1, t(s), t(e), round(t(e) - t(s), 2), state))
    if n_expect is not None and len(kept) != n_expect:
        warn.append(f"남은 문장 {len(kept)}개 ≠ 대본 {n_expect}문장. 쉼이 짧았거나 손뼉을 못 찾았을 수 있습니다.")
    checks = []
    if expected and len(kept) == len(expected):
        for i, (k, line) in enumerate(zip(kept, expected)):
            s, e = sents[k]
            dur = t(e) - t(s)
            rate = syllables(line) / dur if dur > 0 else 0
            ok = 3.0 <= rate <= 9.0
            checks.append({"no": i + 1, "line": line, "sec": round(dur, 2), "syll_per_sec": round(rate, 1), "ok": ok})
            if not ok:
                warn.append(f"{i + 1}번 문장 길이가 대본과 안 맞아 보입니다(초당 {rate:.1f}음절): {line}")

    report = {"input": a.input, "claps": [t(c[0]) for c in claps],
              "sentences": [{"no": r[0], "start": r[1], "end": r[2], "state": r[4]} for r in rows],
              "kept_timeline": timeline, "total_sec": round(total, 2), "checks": checks, "warnings": warn}
    json.dump(report, open(os.path.join(out, "report.json"), "w"), ensure_ascii=False, indent=1)

    md = [f"# 녹음 정리 결과: {os.path.basename(a.input)}", "",
          f"- 손뼉 {len(claps)}번: " + (", ".join(f"{t(c[0])}초" for c in claps) or "없음"),
          f"- 찾은 문장 {len(sents)}개 → 버림 {len(dropped)}개, 사용 {len(kept)}개"
          + (f" (대본 {n_expect}문장)" if n_expect else ""),
          f"- 이어 붙인 길이: {total:.1f}초 (문장 사이 {a.gap}초)", "",
          "| # | 원본 시작 | 원본 끝 | 길이 | 처리 |", "|---|---|---|---|---|"]
    md += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |" for r in rows]
    if checks:
        md += ["", "| 대본 # | 대사 | 길이(초) | 초당 음절 | 확인 |", "|---|---|---|---|---|"]
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
