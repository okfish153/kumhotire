"""홍보용 쇼츠 01 · 제네시스 (세로 1080×1920, 약 40초) — 롱폼 01 요약, 빠른 컷 버전
대본: docs/short01_genesis_promo_script.md
목소리: python3 tools/tts_lines.py docs/short01_genesis_promo_script.md assets/voice/short01 --rate 1.12
사용법: python3 short01_genesis.py [--preview 0 3 10]
"""
import argparse
import math
import os
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

import audio as A
import long01_genesis as L
from ep_grandeur2 import CREAM, AMBER, RED, INK, stamp, option_chip, retro_bgm, stamp_sfx, tick_sfx
from tools.chahyung_motion import Chahyung
from video import YEL, WHITE, prog, out_cubic, out_back, in_out, clamp, text_img, rich_img, box, compose, paste, cover

ROOT = L.ROOT
W, H, FPS = 1080, 1920, 30
VW, VH, VY = 1080, 1100, 300                 # 가운데 화면 영역
VOICE = os.path.join(ROOT, "assets", "voice", "short01")
BUILD = os.path.join(ROOT, "build", "short01")
OUT = os.path.join(ROOT, "output", "short01_genesis_promo.mp4")
GAP, HEAD, TAIL = 0.22, 0.1, 0.15
QUIZ = 9
TITLE = ("여러 번 *구르고도*", "*운전자는 살았다*?")
CAPS = [
    "차가 *여러 번* 굴렀는데, | *운전자는 살았습니다*",
    "2021년, *타이거 우즈*의 | 제네시스 *GV80*",
    "제한속도 *72km* 길을, | *140km* 가까이로",
    "보안관은 말했죠 | 실내가 *거의 온전*했다고",
    "그리고 *5년 뒤*",
    "제네시스 *GV90*",
    "*세계 최초*, | *지붕 에어백*",
    "차가 *구르는 순간*, | 유리 지붕을 *덮어 버립니다*",
    "자, 퀴즈! | GV90 *제일 비싼 모델*은 | 얼마일까요?",
    "정답, *2억 3,950만 원*",
    "근데 이 모든 이야기의 시작, | *그 커브길*에서요,",
]
MOTIONS = ["shock", "nod", "shock", "think", "secret", "jump", "shock", "point_down", "think", "cheer", "secret"]
SHAKE = {1: 0.0, 3: 0.4, 7: 0.1}             # 문장 번호: 흔들기 시작(문장 시작 기준 초)
TL = {}


def load_timeline():
    parts, lines, t = [np.zeros(int(HEAD * A.SR))], [], HEAD
    count = []
    for k in range(1, len(CAPS) + 1):
        a = L.trim(A.read_wav(os.path.join(VOICE, f"line_{k:02d}.wav")))
        st = t
        parts.append(a)
        t += len(a) / A.SR
        if k == QUIZ:
            parts.append(np.zeros(int(0.35 * A.SR)))
            t += 0.35
            cw = L.trim(A.read_wav(os.path.join(VOICE, "count.wav")))
            count = [(round(t + x, 3), round(t + y, 3)) for x, y in L.runs(cw)]
            assert len(count) == 3, count
            parts.append(cw)
            t += len(cw) / A.SR
        lines.append((round(st, 3), round(t, 3)))
        parts.append(np.zeros(int(GAP * A.SR)))
        t += GAP
    voice = np.concatenate(parts[:-1])
    chunks = []
    for k, ((st, en), cap) in enumerate(zip(lines, CAPS), 1):
        segs = [x.strip() for x in cap.split("|")]
        if k == QUIZ:
            en = count[0][0] - 0.2
        w = [max(4, len(s.replace("*", ""))) for s in segs]
        acc = st
        for s, q in zip(segs, w):
            d = (en - st) * q / sum(w)
            chunks.append((acc, acc + d, s, k))
            acc += d
        if k == QUIZ:
            for j, s in enumerate(["*하나*", "하나, *둘*", "하나, 둘, *셋!*"]):
                chunks.append((count[j][0] - 0.1, count[j + 1][0] - 0.1 if j < 2 else lines[k - 1][1], s, k))
    total = round(len(voice) / A.SR + TAIL, 2)
    hop = A.SR // FPS
    n = int(total * FPS) + 1
    rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(voice) else 0.0
                    for i in range(n)])
    rms = np.convolve(rms, np.ones(3) / 3, mode="same")
    energy = np.clip(rms / (np.percentile(rms[rms > 0], 95) + 1e-9), 0, 1).round(3).tolist()
    TL.update(lines=lines, chunks=chunks, total=total, energy=energy, count=count)
    return voice


def Ls(k):
    return TL["lines"][k - 1][0]


def cs(k, j):
    return [c[0] for c in TL["chunks"] if c[3] == k][j]


def line_at(t):
    k = 1
    for i, (st, _) in enumerate(TL["lines"], 1):
        if t >= st - 0.08:
            k = i
    return k


# ------------------------------------------------------------------ 부품
@lru_cache(None)
def title_band():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    for j, line in enumerate(TITLE):
        tx = rich_img(line, 96, 9)
        if tx.width > 1040:
            tx = tx.resize((1040, int(tx.height * 1040 / tx.width)), Image.LANCZOS)
        im.alpha_composite(tx, ((W - tx.width) // 2, 105 + j * 108 - tx.height // 2))
    return im


def vphoto(v, key, t, t0, zoom=(1.05, 1.18), fx=0.5, fy=0.5, dark=0.25, gray=False):
    p = clamp((t - t0) / 3.0)
    im = cover(L.photo(key), VW, VH, zoom[0] + (zoom[1] - zoom[0]) * p, fx, fy)
    if gray:
        im = Image.blend(im, im.convert("L").convert("RGBA"), 0.85)
    v.alpha_composite(im)
    if dark:
        v.alpha_composite(Image.new("RGBA", (VW, VH), (0, 0, 0, int(255 * dark))))
    return L.CREDIT[key]


def vpanel(v, color=(26, 24, 30)):
    v.alpha_composite(Image.new("RGBA", (VW, VH), color + (255,)))
    d = ImageDraw.Draw(v)
    for x in range(-VH, VW, 54):
        d.line((x, 0, x + VH, VH), fill=(color[0] + 7, color[1] + 7, color[2] + 7), width=2)


def kinetic(v, txt, x, y, t0, t, size=150, color=YEL, rot=-3):
    p = out_back(prog(t, t0, 0.18), 2.4)
    if p > 0:
        paste(v, text_img(txt, size, color, "Black", stroke=9, sfill=(0, 0, 0), shadow=10), x, y, 1.8 - 0.8 * p, rot,
              clamp(p * 2))


def hook_visual(v, t, a=1.0):
    vphoto(v, "gv80_white", t, 0, (1.25, 1.32), 0.42, 0.5, dark=0.35)
    if a > 0:
        paste(v, L.tag("2021 · 미국 LA · 제네시스 GV80", (250, 246, 236), INK, 46), VW / 2, 120, 1, -2, a)
        paste(v, L.tag("여러 번 전복", (60, 60, 66), WHITE, 84), VW / 2, 720, 1, -4, a)
        paste(v, L.tag("운전자 생존", RED, WHITE, 96), VW / 2, 890, 1 + 0.05 * math.sin(t * 8), 3, a)


def scene(v, k, t):
    lt = t - Ls(k)
    cr = None
    if k == 1:
        cr = L.CREDIT["gv80_white"]
        hook_visual(v, t)
    elif k == 2:
        cr = vphoto(v, "gv80_front", t, Ls(2), (1.25, 1.1), 0.42, 0.5, 0.2)
        L.pop(v, L.tag("운전석: 타이거 우즈", AMBER, INK, 60), VW / 2, 180, Ls(2) + 0.15, t, -3)
        kinetic(v, "GV80", VW / 2, 860, cs(2, 1), t, 210)
    elif k == 3:
        vpanel(v, (22, 26, 30))
        val = 72 + (140 - 72) * out_cubic(prog(t, Ls(3) + 0.2, 1.2))
        L.gauge(v, VW / 2, 470, 330, val, 200, mark=72)
        L.stamp_at(v, "거의 2배", VW / 2, 920, cs(3, 1) + 0.2, t, 96)
    elif k == 4:
        vpanel(v, (32, 28, 24))
        L.pop(v, text_img("“", 240, YEL, "Black", shadow=0), 160, 200, Ls(4), t)
        L.pop(v, L.tag("LA 카운티 보안관", (250, 246, 236), INK, 50), VW / 2, 300, Ls(4) + 0.1, t)
        L.pop(v, text_img("실내가", 130, WHITE, "Black", stroke=8, sfill=(0, 0, 0)), VW / 2, 520, cs(4, 1), t)
        L.pop(v, text_img("거의 온전했다", 130, YEL, "Black", stroke=8, sfill=(0, 0, 0)), VW / 2, 690, cs(4, 1) + 0.3, t)
    elif k == 5:
        v.alpha_composite(Image.new("RGBA", (VW, VH), (0, 0, 0, 255)))
        kinetic(v, "5년 뒤", VW / 2, VH / 2, Ls(5), t, 220, WHITE, 0)
    elif k == 6:
        cr = vphoto(v, "gv90_gray_front", t, Ls(6), (1.4, 1.15), 0.32, 0.55, 0.15)
        kinetic(v, "GV90", VW / 2, 200, Ls(6) + 0.15, t, 240)
    elif k == 7:
        cr = vphoto(v, "gv90_neolun_rear", t, Ls(7), (1.3, 1.2), 0.35, 0.5, 0.5)
        L.stamp_at(v, "세계 최초", VW / 2, 360, Ls(7) + 0.05, t, 110)
        L.pop(v, L.tag("지붕 에어백", AMBER, INK, 96), VW / 2, 640, cs(7, 1), t, 3)
    elif k == 8:
        vpanel(v, (30, 26, 24))
        ImageDraw.Draw(v).line([(x, 780) for x in range(0, VW + 1, 40)], fill=(90, 90, 96), width=70)
        L.car_roll(v, t, Ls(8) - 0.1, 160, 900, 600, dur=2.2, w=520, roofbag_at=0.15)
        L.pop(v, L.tag("구르는 순간 펼침", (250, 246, 236), INK, 56), VW / 2, 180, Ls(8) + 0.3, t)
    elif k == 9:
        vpanel(v, (30, 30, 34))
        L.pop(v, L.tag("자, 퀴즈!", RED, WHITE, 70), VW / 2, 120, Ls(9), t)
        L.pop(v, text_img("GV90 제일 비싼 모델은?", 60, CREAM, "Black", stroke=5, sfill=(0, 0, 0)), VW / 2, 250, cs(9, 1), t)
        beat = countdown(v, t, VW / 2, 860)
        for q, txt in enumerate(["1억 원대", "2억 원대", "3억 원대"]):
            pk = out_back(prog(t, cs(9, 1) + 0.12 * q, 0.25))
            paste(v, option_chip(str(q + 1), txt), VW / 2 - 40, 400 + q * 135, (pk + 0.001) * beat * 0.95, 0, clamp(pk * 2))
    elif k == 10:
        cr = vphoto(v, "gv90_white_front", t, Ls(10), (1.15, 1.05), 0.5, 0.5, 0.5)
        n = int(23950 * out_cubic(prog(t, Ls(10) + 0.2, 0.9)))
        txt = "2억 3,950만 원" if n >= 23950 else f"{n // 10000}억 {n % 10000:,}만" if n >= 10000 else f"{n:,}만"
        paste(v, text_img(txt, 130, YEL, "Black", stroke=8, sfill=(0, 0, 0), shadow=10), VW / 2, 480)
        L.pop(v, L.tag("네오룬 이그제큐티브 스위트 4인승", (250, 246, 236), INK, 44), VW / 2, 650, Ls(10) + 1.0, t)
    else:                                              # 11 → 첫 화면으로
        cr = L.CREDIT["gv80_white"]
        a = in_out(prog(t, Ls(11) + 0.1, 1.0))
        hook_visual(v, t, a)
    return cr


def countdown(v, t, x, y):
    cnt = TL["count"]
    j = max([q for q, (st, _) in enumerate(cnt) if t >= st - 0.08] or [-1])
    if j < 0:
        return 1
    p = out_back(prog(t, cnt[j][0] - 0.08, 0.22))
    fill = YEL if j == 2 else (250, 246, 236)
    disk = compose((box(240, 240, 120, fill, INK, 8, True), 0, 0),
                   (text_img(["하나", "둘", "셋!"][j], 96, INK, "Black", shadow=0), 0, -4))
    paste(v, disk, x, y, 0.6 + 0.4 * p, (j - 1) * 8)
    return 1 + 0.06 * (1 - p)


def caption(c, t):
    for st, en, cap, k in TL["chunks"]:
        if st - 0.05 <= t < en + 0.1:
            p = out_back(prog(t, st - 0.05, 0.12), 2.6)
            im = rich_img(cap, 88, 10)
            if im.width > 1040:
                im = im.resize((1040, int(im.height * 1040 / im.width)), Image.BICUBIC)
            paste(c, im, W / 2, 1490, 0.85 + 0.15 * p, 0, clamp(p * 1.6))
            return


@lru_cache(None)
def rig():
    return Chahyung(height=300)


def frame(i):
    t = i / FPS
    c = title_band().copy()
    k = line_at(t)
    v = Image.new("RGBA", (VW, VH), (0, 0, 0, 255))
    cr = scene(v, k, t)
    # 도파민 효과: 문장마다 펀치 줌 + 번쩍, 충격 문장은 흔들림
    lt = t - Ls(k)
    punch = 1 + 0.10 * (1 - out_cubic(clamp(lt / 0.28)))
    if punch > 1.001:
        v = v.resize((int(VW * punch), int(VH * punch)), Image.BILINEAR).crop(
            (int(VW * (punch - 1) / 2), int(VH * (punch - 1) / 2), int(VW * (punch - 1) / 2) + VW,
             int(VH * (punch - 1) / 2) + VH))
    dx = dy = 0
    if k in SHAKE and 0 <= lt - SHAKE[k] < 0.45:
        amp = 22 * (1 - (lt - SHAKE[k]) / 0.45)
        dx, dy = int(amp * math.sin(lt * 90)), int(amp * math.cos(lt * 73))
    c.alpha_composite(v, (dx, VY + dy))
    fl = 1 - clamp(lt / 0.12)
    if fl > 0 and k > 1:
        c.alpha_composite(Image.new("RGBA", (VW, VH), (255, 255, 255, int(150 * fl))), (0, VY))
    if cr:
        im = text_img(cr, 22, (225, 225, 225), "SemiBold", shadow=3)
        paste(c, im, 30 + im.width / 2, VY + VH - 22)
    e = TL["energy"][min(len(TL["energy"]) - 1, int(t * FPS))]
    im = rig().frame(MOTIONS[k - 1], max(0.0, lt), e)
    c.alpha_composite(im, (int(950 - im.width / 2), int(1405 - (im.height - rig().pad))))
    caption(c, t)
    ImageDraw.Draw(c).rectangle((0, 0, int(W * t / TL["total"]), 8), fill=AMBER)
    return c.convert("RGB")


# ------------------------------------------------------------------ 오디오·렌더
def build_audio(voice):
    sr = A.SR
    n = int(TL["total"] * sr)
    v = np.zeros(n)
    v[:len(voice)] = voice[:n]
    v = v / max(1e-9, np.abs(v).max()) * 0.92
    music = retro_bgm(TL["total"] + 1.0)[:n]
    act = np.convolve((np.abs(v) > 0.02).astype(float), np.ones(int(0.25 * sr)) / int(0.25 * sr), mode="same")
    music = music * (1 - 0.45 * np.clip(act * 4, 0, 1))[:, None] * 0.8
    ev = [(Ls(k) - 0.06, A.sfx_whoosh(0.25), 0.45) for k in range(2, len(CAPS) + 1)]
    ev += [(0.05, A.sfx_impact(), 0.6), (Ls(3) + 0.4, A.sfx_impact(), 0.55), (cs(3, 1) + 0.2, stamp_sfx(), 0.8),
           (Ls(5) - 0.6, A.sfx_riser(0.6), 0.4), (Ls(6), A.sfx_impact(), 0.6), (Ls(7) + 0.05, stamp_sfx(), 0.9),
           (cs(7, 1), A.sfx_ding(), 0.6), (Ls(8) + 0.3, A.sfx_pop(), 0.6), (Ls(10) + 0.2, A.sfx_cash(), 0.6),
           (Ls(9), A.sfx_ding(), 0.5)]
    ev += [(st - 0.05, tick_sfx(), 0.9) for st, _ in TL["count"]]
    fx = np.zeros(n)
    for t0, snd, g in ev:
        i = int(max(0, t0) * sr)
        if i < n:
            snd = snd[: n - i]
            fx[i:i + len(snd)] += snd * g
    mix = music + (v + fx * 0.55)[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    os.makedirs(BUILD, exist_ok=True)
    p = os.path.join(BUILD, "mix.wav")
    A.write_wav(p, mix)
    return p


def write_srt(path):
    def ts(x):
        m, s = divmod(x, 60)
        return f"00:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"
    with open(path, "w", encoding="utf-8") as f:
        for k, (st, en, cap, _) in enumerate(TL["chunks"], 1):
            f.write(f"{k}\n{ts(st)} --> {ts(en)}\n{cap.replace('*', '')}\n\n")


def _render_part(args):
    i0, i1, path, tl = args
    TL.update(tl)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(frame(i).tobytes())
    p.stdin.close()
    p.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", nargs="*", type=float)
    a = ap.parse_args()
    voice = load_timeline()
    os.makedirs(BUILD, exist_ok=True)
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
    jobs_n = os.cpu_count() or 4
    step = math.ceil(n / jobs_n)
    jobs = [(j * step, min(n, (j + 1) * step), os.path.join(BUILD, f"part_{j}.mp4"), dict(TL))
            for j in range(jobs_n) if j * step < n]
    with Pool(len(jobs)) as pool:
        parts = pool.map(_render_part, jobs)
    lst = os.path.join(BUILD, "parts.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    vid = os.path.join(BUILD, "video_noaudio.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid])
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", mix, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
                           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{TL['total']}",
                           "-movflags", "+faststart", OUT])
    write_srt(OUT.replace(".mp4", ".srt"))
    print("[done]", OUT)


if __name__ == "__main__":
    main()
