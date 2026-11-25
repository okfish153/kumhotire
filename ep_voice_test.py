"""직접 녹음 음성 시험 영상 (각그랜저 1분 버전의 앞부분, 약 25초)

녹음 파일: assets/voice/test/test_take1.aac
- 무음 구간으로 문장 조각을 찾고, 긴 쉼은 줄이고(연출용 쉼은 남김), 음 높이 그대로 속도만 TEMPO배.
- 시리즈 표시·다음 편 카드 없음. 첫 프레임부터 훅.
사용법: python3 ep_voice_test.py [--preview 1 5 9]
"""
import argparse
import math
import os
import re
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import audio as A
import ep_grandeur2 as G
from ep_grandeur2 import (CREAM, AMBER, RED, INK, CARD_W, CARD_H, CARD_Y, photo, bg_photo, card, put_card,
                          shade_card, memo_card, option_chip, stamp, bowl, won_bill, rich_img, jolt,
                          retro_bgm, calc_sfx, stamp_sfx, tick_sfx, credit)
from video import (W, H, YEL, WHITE, prog, out_cubic, out_back, in_out, clamp, text_img, box, compose, paste)

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "assets", "voice", "test", "test_take1.aac")
BUILD = os.path.join(ROOT, "build", "voice_test")
OUT = os.path.join(ROOT, "output", "voice_test_title_layout.mp4")
TITLE = ("짜장면 *28,000그릇* 값?", "지금 짜장면 값으론 *2억!*")
FPS = 30
TEMPO = 1.10
PRE, POST = 0.08, 0.14

# 녹음 순서대로 말 조각 (무음 -38dB/0.35s 기준으로 찾은 조각 순서와 대응)
# (화면 자막, 큐 이름, 이 조각 뒤 쉼 초)
CUES = [
    ("그거 아세요?", "hook", 0.15),
    ("이 차 한 대 값이면,", "hook2", 0.25),
    ("짜장면이… *2만 8천 그릇*", "bowls", 0.05),
    ("이었습니다", "bowls_end", 0.45),
    ("때는 *1986년*", "year", 0.20),
    ("짜장면 한 그릇이 *600원*이던 시절이죠", "memo", 0.25),
    ("이 차 값은 얼마였을까요?", "quiz", 0.30),
    ("하나", "c1", 0.30),
    ("둘", "c2", 0.30),
    ("셋", "c3", 0.55),
    ("*1,690만 원*", "reveal", 0.25),
    ("출시 초기 가격입니다", "reveal2", 0.45),
    ("당시 대기업 신입 월급이 *31만 원*", "salary", 0.20),
    ("한 푼도 안 쓰고", "save", 0.15),
    ("*4년 반*을 모아야 했죠", "years", 0.55),
    ("…짜장면도 못 먹고요", "joke", 0.0),
]
TL = {"cues": []}   # [(start, end, caption, cue)]


def speech_segments(path):
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
                          "silencedetect=noise=-38dB:d=0.35", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: (-?[\d.e-]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", path]).decode())
    segs = []
    for i, e in enumerate(en):
        s_next = st[i + 1] if i + 1 < len(st) else dur
        if s_next - e > 0.12:          # 0.12초 미만은 잡음
            segs.append((e, s_next))
    return segs


def build_voice():
    os.makedirs(BUILD, exist_ok=True)
    clean = os.path.join(BUILD, "voice_clean.wav")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", SRC, "-af",
                           "highpass=f=80,afftdn=nf=-60,equalizer=f=3200:t=q:w=1.2:g=2.5,"
                           "acompressor=threshold=-20dB:ratio=3:attack=5:release=90:makeup=4",
                           "-ar", "44100", "-ac", "1", clean])
    segs = speech_segments(SRC)
    assert len(segs) == len(CUES), f"말 조각 {len(segs)}개 ≠ 큐 {len(CUES)}개: {segs}"
    x = A.read_wav(clean)
    sr = A.SR
    out, t = [], 0.12
    pieces = []
    for (s, e), (cap, cue, gap) in zip(segs, CUES):
        a, b = max(0, int((s - PRE) * sr)), min(len(x), int((e + POST) * sr))
        p = os.path.join(BUILD, f"seg_{len(pieces):02d}.wav")
        q = os.path.join(BUILD, f"seg_{len(pieces):02d}_t.wav")
        A.write_wav(p, np.stack([x[a:b], x[a:b]], 1))
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-af", f"atempo={TEMPO}", "-ac", "1", q])
        y = A.read_wav(q)
        d = len(y) / sr
        pieces.append((t, y))
        out.append((round(t, 3), round(t + d, 3), cap, cue))
        t += d + gap
    total = round(t + 1.4, 2)
    voice = np.zeros(int(total * sr))
    for st, y in pieces:
        i = int(st * sr)
        voice[i:i + len(y)] += y[: len(voice) - i]
    TL["cues"], TL["total"] = out, total
    return voice


def C(name):
    for st, en, cap, cue in TL["cues"]:
        if cue == name:
            return st, en
    raise KeyError(name)


# ------------------------------------------------------------------ 화면
def caption(c, t):
    for st, en, cap, cue in TL["cues"]:
        if st - 0.05 <= t < en + 0.25:
            p = out_back(prog(t, st - 0.05, 0.14), 2.2)
            im = rich_img(cap, 84, 10)
            if im.width > 1040:
                im = im.resize((1040, int(im.height * 1040 / im.width)), Image.BICUBIC)
            paste(c, im, W / 2, 1450, 0.9 + 0.1 * p, 0, clamp(p * 1.6))
            return


def big(c, txt, t0, t, y=400, size=110, color=YEL, rot=0):
    p = out_back(prog(t, t0, 0.18), 2.2)
    if p > 0:
        paste(c, text_img(txt, size, color, "Black", stroke=8, sfill=(0, 0, 0), shadow=8), W / 2, y, 1.6 - 0.6 * p, rot, clamp(p * 2))


@lru_cache(None)
def title_band():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    for k, line in enumerate(TITLE):
        tx = rich_img(line, 98, 9)
        if tx.width > 1040:
            tx = tx.resize((1040, int(tx.height * 1040 / tx.width)), Image.LANCZOS)
        im.alpha_composite(tx, ((W - tx.width) // 2, 228 + k * 118 - tx.height // 2 + 40))
    return im


def frame(i):
    t = i / FPS
    c = title_band().copy()
    s_bowls = C("bowls")[0]
    s_year = C("year")[0]
    s_quiz = C("quiz")[0]
    s_rev = C("reveal")[0]
    s_sal = C("salary")[0]
    s_joke = C("joke")[0]
    if t < s_bowls - 0.05:                          # 훅: 사진 쾅 + 줌인
        dx, dy = jolt(t, C("hook2")[0], 16)
        z = 1.0 + 0.12 * in_out(prog(t, 0, s_bowls))
        put_card(c, card(photo(), z, 0.45, 0.55), dx=dx, dy=dy)
        big(c, "?", 0.1, t, 700, 220, YEL, 8 * math.sin(t * 5))
        big(c, "이 차 한 대 값 =", C("hook2")[0], t, 560, 80, WHITE)
    elif t < s_year - 0.05:                         # 짜장면이 쏟아짐
        lt = t - s_bowls
        put_card(c, card(photo(), 1.12, 0.45, 0.55))
        shade_card(c, 0.55)
        rng = np.random.default_rng(4)
        for k in range(60):
            x = 120 + rng.random() * 840
            y0 = 500 + rng.random() * 800
            p = out_cubic(prog(lt, rng.random() * 1.2, 0.35))
            if p > 0:
                paste(c, bowl(), x, 500 + (y0 - 500) * p, 1, (k * 37) % 30 - 15, clamp(p * 3))
        cnt = int(28_000 * out_cubic(prog(lt, 0.2, 1.4)))
        lab = compose((box(700, 160, 30, RED, CREAM, 5, True), 0, 0),
                      (text_img(f"짜장면 {cnt:,}그릇", 84, WHITE, "Black", shadow=0), 0, -4))
        paste(c, lab, W / 2, 900, 1, -2, clamp(lt * 4))
        big(c, "이 차 한 대 값 =", s_bowls, t, 560, 80, WHITE)
    elif t < s_quiz - 0.05:                         # 1986, 600원
        lt = t - s_year
        put_card(c, card(photo(), 1.0 + 0.05 * prog(lt, 0, 3), 0.5, 0.5))
        big(c, "1986", s_year, t, 1180, 150, CREAM)
        p = out_back(prog(t, C("memo")[0] + 0.1, 0.3))
        paste(c, memo_card(), 330, 720, 0.5 + 0.5 * p, 0, clamp(p * 1.5))
    elif t < s_rev - 0.05:                          # 퀴즈 + 카운트다운
        lt = t - s_quiz
        put_card(c, card(photo(), 1.05, 0.45, 0.55))
        shade_card(c, 0.45)
        paste(c, memo_card(), 290, 600, 0.75)
        for k, (no, txt) in enumerate([("1", "169만 원"), ("2", "1,690만 원"), ("3", "1억 원")]):
            pk = out_back(prog(lt, 0.2 + 0.25 * k, 0.25))
            paste(c, option_chip(no, txt), W / 2 + 120, 930 + k * 150, pk, 0, clamp(pk * 1.4))
        for name, n in (("c1", "1"), ("c2", "2"), ("c3", "3")):
            st, en = C(name)
            if st - 0.03 <= t < st + 0.6:
                p = out_back(prog(t, st - 0.03, 0.15), 2.5)
                ring = compose((box(260, 260, 130, YEL, INK, 8, True), 0, 0),
                               (text_img(n, 170, INK, "Black", shadow=0), 0, -8))
                paste(c, ring, 820, 640, 1.4 - 0.4 * p, 0, clamp(p * 2) * (1 - prog(t, st + 0.45, 0.15)))
        if t < C("c1")[0] - 0.1:
            big(c, "이 차 값은?", s_quiz, t, 800, 96, YEL)
    elif t < s_sal - 0.05:                          # 정답
        hit = s_rev + 0.05
        dx, dy = jolt(t, hit, 24)
        put_card(c, card(photo(), 1.08, 0.45, 0.55), dx=dx, dy=dy)
        shade_card(c, 0.62)
        val = int(16_900_000 * out_cubic(clamp((t - s_rev + 0.35) / 0.4)))
        txt = "1,690만 원" if t >= hit + 0.05 else f"{val // 10000:,}만 원"
        sc = 1.0 + 0.15 * (1 - out_cubic(prog(t, hit, 0.25)))
        paste(c, text_img(txt, 170, YEL, "Black", stroke=6, sfill=(0, 0, 0), shadow=10), W / 2 + dx, 840 + dy, sc)
        ps = prog(t, hit + 0.2, 0.16)
        if ps > 0:
            paste(c, stamp("정답", 92), W / 2 + 290, 1060, 2.2 - 1.2 * ps, 0, clamp(ps * 3))
        p2 = prog(t, C("reveal2")[0], 0.25)
        paste(c, text_img("1986년 출시 초기 가격 · 오토뷰 보도", 40, CREAM, "Bold", stroke=4, sfill=(0, 0, 0), shadow=3),
              W / 2, 1180, 1, 0, p2)
    elif t < s_joke - 0.05:                         # 월급 31만 원 × 54칸
        lt = t - s_sal
        G.panel(c, (32, 38, 34))
        head = compose((box(760, 110, 26, (250, 246, 236), shadow=False), 0, 0),
                       (text_img("1986 대기업 신입 기본급 월 31만 원", 44, INK, "Black", shadow=0), 0, -3))
        paste(c, head, W / 2, 560, 1, 0, clamp(lt * 5))
        s_save = C("save")[0]
        n = int(54 * out_cubic(prog(t, s_save, max(0.8, C("years")[1] - s_save - 0.2))))
        cols, dxs, dys = 9, 100, 66
        x0, y0 = W / 2 - (cols - 1) * dxs / 2, 680
        for k in range(54):
            r_, q = divmod(k, cols)
            x, y = x0 + q * dxs, y0 + r_ * dys
            ImageDraw.Draw(c).rounded_rectangle((x - 44, y - 26, x + 44, y + 26), 8, outline=(110, 130, 110), width=2)
            if k < n:
                paste(c, won_bill(), x, y, 0.58)
        if t >= C("years")[0]:
            ps = out_back(prog(t, C("years")[0], 0.25))
            lab = compose((box(620, 140, 30, RED, CREAM, 5, True), 0, 0),
                          (text_img("꼬박 4년 반!", 84, WHITE, "Black", shadow=0), 0, -4))
            paste(c, lab, W / 2, 1150, ps, -2, clamp(ps * 1.5))
        else:
            paste(c, text_img(f"{n}개월", 84, YEL, "Black", stroke=6, sfill=(0, 0, 0), shadow=4), W / 2, 1150)
        paste(c, text_img("1,690만 ÷ 31만 ≈ 54.5개월 · 기본급 기준", 28, (215, 205, 190), "SemiBold", shadow=2), W / 2, 1290)
    else:                                           # 짜장면도 못 먹고요
        lt = t - s_joke
        G.panel(c, (40, 30, 24))
        paste(c, bowl(380), W / 2, 860, 1 + 0.03 * math.sin(lt * 8))
        p = out_cubic(prog(lt, 0.25, 0.25))
        if p > 0:
            d = ImageDraw.Draw(c)
            d.line((W / 2 - 230, 640, W / 2 - 230 + 460 * p, 640 + 440 * p), fill=RED, width=26)
            d.line((W / 2 + 230, 640, W / 2 + 230 - 460 * p, 640 + 440 * p), fill=RED, width=26)
        ps = prog(lt, 0.55, 0.16)
        if ps > 0:
            paste(c, stamp("짜장면 금지", 92, RED, rot=-8), W / 2, 1180, 2.2 - 1.2 * ps, 0, clamp(ps * 3))
    if t < s_sal - 0.05:
        paste(c, credit(), W / 2, 1360)
    caption(c, t)
    ImageDraw.Draw(c).rectangle((0, 0, int(W * t / TL["total"]), 7), fill=AMBER)
    return c.convert("RGB")


# ------------------------------------------------------------------ 오디오
def build_audio(voice):
    sr = A.SR
    n = len(voice)
    voice = voice / max(1e-6, np.abs(voice).max()) * 0.92
    music = retro_bgm(TL["total"] + 1.0)[:n]
    act = np.convolve((np.abs(voice) > 0.02).astype(float), np.ones(int(0.3 * sr)) / int(0.3 * sr), mode="same")
    duck = 1 - 0.55 * np.clip(act * 4, 0, 1)
    env = np.ones(n)
    fo = int(1.2 * sr)
    env[-fo:] = np.linspace(1, 0, fo)
    music = music * (duck * env)[:, None] * 0.7
    ev = [(C("hook2")[0] - 0.02, stamp_sfx(), 0.6)]
    s, e = C("bowls")
    rng = np.random.default_rng(9)
    for k in range(12):
        ev.append((s + rng.random() * 1.2, A.sfx_pop(), 0.35))
    ev += [(C("year")[0] - 0.1, A.sfx_whoosh(0.35), 0.4), (C("memo")[0] + 0.1, A.sfx_pop(), 0.6),
           (C("quiz")[0] - 0.1, A.sfx_whoosh(0.35), 0.4)]
    for k in range(3):
        ev.append((C("quiz")[0] + 0.2 + 0.25 * k, A.sfx_pop(), 0.6))
    for name in ("c1", "c2", "c3"):
        ev.append((C(name)[0], tick_sfx(), 1.4))
    hit = C("reveal")[0] + 0.05
    ev += [(hit - 0.02, calc_sfx(), 1.0), (hit + 0.2, stamp_sfx(), 0.8),
           (C("salary")[0] - 0.12, A.sfx_whoosh(0.35), 0.4)]
    sv = C("save")[0]
    for k in range(0, 54, 3):
        ev.append((sv + (C("years")[1] - sv - 0.2) * (1 - (1 - k / 54) ** (1 / 3)), tick_sfx(), 0.6))
    ev += [(C("years")[0], A.sfx_ding(), 0.6), (C("joke")[0] - 0.1, A.sfx_whoosh(0.35), 0.4),
           (C("joke")[0] + 0.55, stamp_sfx(), 0.9)]
    fx = np.zeros(n)
    for t0, snd, g in ev:
        i = int(max(0, t0) * sr)
        if i < n:
            snd = snd[: n - i]
            fx[i:i + len(snd)] += snd * g
    mix = music + (voice + fx * 0.5)[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    p = os.path.join(BUILD, "mix.wav")
    A.write_wav(p, mix)
    return p


def _render_part(args):
    i0, i1, path, tl = args
    TL.update(tl)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                          "-crf", "18", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(frame(i).tobytes())
    p.stdin.close()
    p.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", nargs="*", type=float)
    a = ap.parse_args()
    voice = build_voice()
    for st, en, cap, cue in TL["cues"]:
        print(f"{st:6.2f}-{en:6.2f} {cue:9s} {cap}")
    print("[total]", TL["total"])
    if a.preview is not None:
        for s in a.preview:
            p = os.path.join(BUILD, f"preview_{s:05.2f}.png")
            frame(int(s * FPS)).save(p)
            print(p)
        return
    mix = build_audio(voice)
    from multiprocessing import Pool
    n = int(TL["total"] * FPS)
    step = math.ceil(n / 4)
    jobs = [(j * step, min(n, (j + 1) * step), os.path.join(BUILD, f"part_{j}.mp4"), dict(TL)) for j in range(4)]
    with Pool(4) as pool:
        parts = pool.map(_render_part, jobs)
    lst = os.path.join(BUILD, "parts.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    vid = os.path.join(BUILD, "video_noaudio.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid])
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", mix,
                           "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                           "-ar", "48000", "-t", f"{TL['total']}", "-movflags", "+faststart", OUT])
    print("[done]", OUT)


if __name__ == "__main__":
    main()
