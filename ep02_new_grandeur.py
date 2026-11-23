"""EP02 뉴 그랜저 1분 쇼츠 (대본 docs/ep02_new_grandeur_script.md, A안)

목소리: assets/voice/ep02/ep02_take1.* 가 있으면 tools/clap_cut.py로 정리해 그 시간에 맞춘다.
        없으면 EP01 녹음 속도(초당 약 3.8음절)로 길이를 추정한 **무음 미리보기**를 만든다.
화면: 위 고정 2줄 제목 / 가운데 실사진 카드와 그래픽 / 아래 큰 자막 / 오른쪽 아래 차형(움직임)
- 시리즈 번호·다음 편 예고 없음. 끝 화면을 첫 화면과 맞춰 반복 재생이 이어지게.
사용법: python3 ep02_new_grandeur.py [--preview 1 5 9]
"""
import argparse
import glob
import json
import math
import os
import re
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import audio as A
from tools.chahyung_motion import Chahyung
import ep_grandeur2 as G
from ep_grandeur2 import (CREAM, AMBER, RED, INK, CARD_W, CARD_H, CARD_Y, photo, card, put_card, shade_card, stamp,
                          bowl, rich_img, jolt, retro_bgm, calc_sfx, stamp_sfx, tick_sfx)
from video import (W, H, YEL, WHITE, prog, out_cubic, out_back, in_out, clamp, text_img, box, compose, paste, cover)

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(ROOT, "docs", "ep02_new_grandeur_script.md")
VOICE_GLOB = os.path.join(ROOT, "assets", "voice", "ep02", "ep02_take1.*")
VOICE_DIR = os.path.join(ROOT, "build", "ep02_take1")
BUILD = os.path.join(ROOT, "build", "ep02_video")
OUT = os.path.join(ROOT, "output", "ep02_new_grandeur_1min.mp4")
CUT_ARGS = ["--no-clap", "--gap", "0.3", "--inner-pause", "0.25"]   # 손뼉 없이 녹음, 54초대라 속도 1.0배
TITLE = ("신입 월급 *5년 치* 차?", "1992 회장님 차 *3,490만 원*")
FPS = 30
TAIL = 0.35
LX_PATH = os.path.join(ROOT, "assets", "images", "grandeur_lx.jpg")
LX_BOX = (60, 0, 1280, 711)            # 왼쪽 다른 차를 뺀 영역
LX_PLATE = (935, 520, 1110, 650)
# 사진 저작자·라이선스 확인 전 임시 표기 (확인되면 바꿈)
LX_CREDIT = "사진: Wikimedia Commons · Category:Hyundai Grandeur (LX) · 저작자·라이선스 확인 중"

CAPS = [
    ["신입사원 월급 *5년 치*"],
    ["이 차 *한 대 값*이었습니다"],
    ["1992년, 각이 사라진 *회장님 차*", "*뉴 그랜저*"],
    ["근데 이 차,", "*2년 뒤*엔 더 무서워집니다"],
    ["제일 비싼 3.0 골드가", "*3,490만 원*"],
    ["각그랜저 처음 값의", "*두 배*가 넘었죠"],
    ["그 시절엔 말이죠,", "대졸 신입 월급이 *55만 원*"],
    ["한 푼도 안 쓰고 *5년 넘게*", "…짜장면도 못 먹고요"],
    ["그리고 94년, *V6 3.5*", "*225마력*에 값은 *4,400만 원* 가까이"],
    ["여러분 *첫 차*는 뭐였어요?", "댓글로 알려 주세요"],
    ["구독해 두시면", "옛날 차 이야기, 계속 들려드릴게요", "그럼 이 차, 신입 월급 몇 년 치였냐면요,"],
]
# 문장별 차형 움직임 (자막 조각마다 바꾸려면 리스트)
MOTIONS = ["shock", "talk", "nod", "secret", "jump", "shock", "think", "awkward", ["key_spin", "wind"],
           "point_down", ["cheer", "talk", "idle"]]
CHAR_H, CHAR_X, CHAR_FOOT = 300, 950, 1405
TL = {}


# ------------------------------------------------------------------ 목소리·타임라인
def script_lines():
    out = []
    for ln in open(SCRIPT, encoding="utf-8"):
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if len(c) >= 3 and c[0].isdigit():
            out.append(c[2])
    return out


def load_timeline():
    lines_txt = script_lines()
    assert len(lines_txt) == len(CAPS) == len(MOTIONS)
    takes = sorted(glob.glob(VOICE_GLOB))
    if takes:
        rep = os.path.join(VOICE_DIR, "report.json")
        if not os.path.exists(rep):
            subprocess.check_call(["python3", os.path.join(ROOT, "tools", "clap_cut.py"), takes[0], "--script",
                                   SCRIPT, "--out", VOICE_DIR] + CUT_ARGS)
        r = json.load(open(rep, encoding="utf-8"))
        lines = [(x["start"], x["end"]) for x in r["kept_timeline"]]
        voice = A.read_wav(os.path.join(VOICE_DIR, "voice_clean.wav"))
        preview = False
    else:                                   # 무음 미리보기: 길이 추정
        lines, t = [], 0.15
        for s in lines_txt:
            d = len(re.findall("[가-힣]", s)) / 3.8
            lines.append((round(t, 3), round(t + d, 3)))
            t += d + 0.3
        voice = np.zeros(int((t + 0.2) * A.SR))
        preview = True
    assert len(lines) == len(CAPS), f"문장 {len(lines)}개 ≠ 자막 {len(CAPS)}개"
    chunks = []
    for (st, en), caps in zip(lines, CAPS):
        w = [max(4, len(c.replace("*", ""))) for c in caps]
        acc = st
        for c, k in zip(caps, w):
            d = (en - st) * k / sum(w)
            chunks.append((acc, acc + d, c))
            acc += d
    total = round(len(voice) / A.SR + TAIL, 2)
    hop = A.SR // FPS
    n = int(total * FPS) + 1
    if preview:                             # 말하는 구간에 가짜 말소리 크기
        energy = [0.0] * n
        for st, en in lines:
            for i in range(int(st * FPS), min(n, int(en * FPS))):
                energy[i] = round(0.55 + 0.35 * math.sin(i * 0.9), 3)
    else:
        rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(voice) else 0.0
                        for i in range(n)])
        rms = np.convolve(rms, np.ones(3) / 3, mode="same")
        energy = np.clip(rms / (np.percentile(rms[rms > 0], 95) + 1e-9), 0, 1).round(3).tolist()
    TL.update(lines=lines, chunks=chunks, total=total, energy=energy, preview=preview)
    return voice


def Ls(i):
    return TL["lines"][i - 1][0]


def Le(i):
    return TL["lines"][i - 1][1]


def chunk_start(i, k):
    return TL["chunks"][sum(len(c) for c in CAPS[:i - 1]) + k][0]


# ------------------------------------------------------------------ 화면 부품
@lru_cache(None)
def title_band():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    for k, line in enumerate(TITLE):
        tx = rich_img(line, 98, 9)
        if tx.width > 1040:
            tx = tx.resize((1040, int(tx.height * 1040 / tx.width)), Image.LANCZOS)
        im.alpha_composite(tx, ((W - tx.width) // 2, 228 + k * 118 - tx.height // 2 + 40))
    return im


@lru_cache(None)
def lx_photo():
    im = Image.open(LX_PATH).convert("RGB")
    im.paste(im.crop(LX_PLATE).filter(ImageFilter.GaussianBlur(14)), LX_PLATE[:2])
    return im.convert("RGBA")


def lx_card(zoom=1.0, fx=0.55, fy=0.55):
    inner = cover(lx_photo(), CARD_W, CARD_H, zoom, fx, fy, LX_BOX)
    inner.putalpha(G.card_mask())
    return inner


def big(c, txt, t0, t, y=700, size=110, color=YEL, rot=0, x=W / 2):
    p = out_back(prog(t, t0, 0.18), 2.2)
    if p > 0:
        paste(c, text_img(txt, size, color, "Black", stroke=8, sfill=(0, 0, 0), shadow=8), x, y, 1.6 - 0.6 * p, rot,
              clamp(p * 2))


def label(txt, w, fill=RED, fg=WHITE, size=72):
    return compose((box(w, int(size * 1.7), 30, fill, CREAM, 5, True), 0, 0),
                   (text_img(txt, size, fg, "Black", shadow=0), 0, -4))


@lru_cache(None)
def envelope(w=150, txt="월급"):
    h = int(w * 0.62)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    g.rectangle((0, 0, w - 1, h - 1), fill=(246, 236, 214), outline=INK, width=4)
    g.line((0, 0, w / 2, h * 0.55, w - 1, 0), fill=INK, width=4)
    t = text_img(txt, 30, RED, "Black", shadow=0)
    im.alpha_composite(t, ((w - t.width) // 2, int(h * 0.58)))
    return im


@lru_cache(None)
def bill(w=150, txt="55만"):
    h = int(w * 0.5)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    g.rounded_rectangle((0, 0, w - 1, h - 1), 8, fill=(206, 222, 196), outline=(90, 120, 80), width=3)
    g.ellipse((w * .62, h * .18, w * .9, h * .82), outline=(90, 120, 80), width=3)
    t = text_img(txt, 30, (50, 80, 40), "Black", shadow=0)
    im.alpha_composite(t, (int(w * .08), (h - t.height) // 2))
    return im


@lru_cache(None)
def bubble(txt, w=760):
    b = box(w, 170, 60, (250, 246, 236), INK, 6, True)
    tail = Image.new("RGBA", (90, 70), (0, 0, 0, 0))
    ImageDraw.Draw(tail).polygon([(0, 0), (90, 0), (70, 70)], fill=(250, 246, 236), outline=INK)
    return compose((b, 0, 0), (tail, w // 2 - 150, 112), (text_img(txt, 62, INK, "Black", shadow=0), 0, -4))


@lru_cache(None)
def polaroid(which, w=260):
    src = photo() if which == "gak" else lx_photo()
    bx = G.MAIN_BOX if which == "gak" else LX_BOX
    inner = cover(src, w, int(w * 0.75), 1.0, 0.5, 0.55, bx)
    pad = 14
    im = Image.new("RGBA", (w + pad * 2, int(w * 0.75) + pad * 2 + 40), (250, 248, 242, 255))
    im.alpha_composite(inner, (pad, pad))
    t = text_img("1986 각그랜저" if which == "gak" else "1992 뉴 그랜저", 28, INK, "Black", shadow=0)
    im.alpha_composite(t, ((im.width - t.width) // 2, int(w * 0.75) + pad + 4))
    return im


def gauge(c, cx, cy, r, val, vmax=260):
    d = ImageDraw.Draw(c)
    d.arc((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=(90, 90, 96), width=26)
    a1 = 180 + 180 * min(1, val / vmax)
    d.arc((cx - r, cy - r, cx + r, cy + r), 180, a1, fill=AMBER, width=26)
    for k in range(0, vmax + 1, 20):
        a = math.radians(180 + 180 * k / vmax)
        d.line((cx + math.cos(a) * (r - 40), cy + math.sin(a) * (r - 40), cx + math.cos(a) * (r - 18),
                cy + math.sin(a) * (r - 18)), fill=(200, 200, 205), width=4)
    a = math.radians(a1)
    d.line((cx, cy, cx + math.cos(a) * (r - 30), cy + math.sin(a) * (r - 30)), fill=RED, width=12)
    d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=INK, outline=WHITE, width=4)


def caption(c, t):
    for st, en, cap in TL["chunks"]:
        if st - 0.05 <= t < en + 0.12:
            p = out_back(prog(t, st - 0.05, 0.14), 2.2)
            im = rich_img(cap, 84, 10)
            if im.width > 1040:
                im = im.resize((1040, int(im.height * 1040 / im.width)), Image.BICUBIC)
            paste(c, im, W / 2, 1480, 0.9 + 0.1 * p, 0, clamp(p * 1.6))
            return


@lru_cache(None)
def rig():
    return Chahyung(height=CHAR_H)


def char_react(c, t):
    k = 0
    for i in range(len(TL["lines"])):
        if t >= Ls(i + 1) - 0.05:
            k = i
    m = MOTIONS[k]
    t0 = Ls(k + 1)
    if isinstance(m, list):                 # 자막 조각마다 다른 동작
        j = 0
        for q in range(len(m)):
            if q < len(CAPS[k]) and t >= chunk_start(k + 1, q) - 0.05:
                j = q
        t0 = chunk_start(k + 1, j) if j < len(CAPS[k]) else t0
        m = m[j]
    e = TL["energy"][min(len(TL["energy"]) - 1, int(t * FPS))]
    im = rig().frame(m, max(0.0, t - t0), e)
    c.alpha_composite(im, (int(CHAR_X - im.width / 2), int(CHAR_FOOT - (im.height - rig().pad))))


def credit_line(c, txt):
    im = text_img(txt, 23, (225, 225, 225), "SemiBold", shadow=3)
    paste(c, im, 40 + im.width / 2 * 0.9, 1362, 0.9)


# ------------------------------------------------------------------ 장면
def frame(i):
    t = i / FPS
    c = title_band().copy()
    cred = LX_CREDIT
    if t < Ls(2) - 0.05:                                        # 1 신입 월급 5년 치
        lt = t
        put_card(c, lx_card(1.0 + 0.05 * in_out(prog(t, 0, Ls(2))), 0.55, 0.55))
        shade_card(c, 0.45 * prog(lt, 0.05, 0.3))
        n = int(63 * out_cubic(prog(lt, 0.1, max(0.8, Le(1) - 0.2))))
        for k in range(n):                                       # 월급 봉투가 왼쪽에 탑처럼 쌓임
            col, row = k % 4, k // 4
            x = 150 + col * 82 + (row % 2) * 20
            y = 1290 - row * 46
            paste(c, envelope(), x, y, 0.62, ((k * 37) % 9) - 4)
        paste(c, label(f"월급 봉투 {n}장", 500, size=60), W / 2 + 230, 640, 1, -2, clamp((lt - 0.15) * 5))
    elif t < Ls(3) - 0.05:                                      # 2 이 차 한 대 값
        dx, dy = jolt(t, Ls(2), 22)
        put_card(c, lx_card(1.08), dx=dx, dy=dy)
        paste(c, label("신입 월급 5년 치", 640, size=70), W / 2, 700, 0.9)
        big(c, "= 이 차 한 대 값", Ls(2) + 0.1, t, 1150, 96, YEL)
    elif t < Ls(4) - 0.05:                                      # 3 1992 뉴 그랜저, 각이 사라짐
        lt = t - Ls(3)
        put_card(c, lx_card(1.0 + 0.06 * in_out(prog(lt, 0, 3)), 0.6, 0.6))
        p = in_out(prog(lt, 0.2, 0.8))                           # 네모 → 둥글게
        r = int(10 + 70 * p)
        sq = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
        ImageDraw.Draw(sq).rounded_rectangle((15, 15, 205, 205), int(r * 1.3), outline=YEL, width=16)
        paste(c, box(300, 340, 36, (20, 20, 22, 200), shadow=True), 250, 700, 1, 0, clamp(lt * 4))
        paste(c, sq, 250, 660, 1, 0, clamp(lt * 4))
        paste(c, text_img("각 → 곡선", 48, WHITE, "Black", stroke=5, sfill=(0, 0, 0)), 250, 820, 1, 0, clamp(lt * 4))
        big(c, "1992 뉴 그랜저", chunk_start(3, 1), t, 1180, 100, YEL)
    elif t < Ls(5) - 0.05:                                      # 4 2년 뒤엔 더 무서워집니다
        lt = t - Ls(4)
        put_card(c, lx_card(1.12, 0.55, 0.5))
        shade_card(c, 0.72)
        big(c, "2년 뒤…?", chunk_start(4, 1), t, 860, 150, YEL, -3)
        paste(c, text_img("끝까지 보세요", 54, CREAM, "Black", stroke=5, sfill=(0, 0, 0)), W / 2, 1040, 1, 0,
              prog(t, chunk_start(4, 1) + 0.3, 0.3))
    elif t < Ls(6) - 0.05:                                      # 5 3,490만 원
        hit = chunk_start(5, 1)
        dx, dy = jolt(t, hit, 24)
        put_card(c, lx_card(1.06), dx=dx, dy=dy)
        shade_card(c, 0.62)
        val = int(34_900_000 * out_cubic(clamp((t - Ls(5)) / max(0.3, hit - Ls(5)))))
        txt = "3,490만 원" if t >= hit else f"{val // 10000:,}만 원"
        sc = 1.0 + 0.15 * (1 - out_cubic(prog(t, hit, 0.25)))
        paste(c, text_img(txt, 160, YEL, "Black", stroke=6, sfill=(0, 0, 0), shadow=10), W / 2 + dx, 800 + dy, sc)
        ps = prog(t, hit + 0.15, 0.16)
        if ps > 0:
            paste(c, stamp("3.0 골드", 56), W / 2 + 170, 960, 2.2 - 1.2 * ps, -6, clamp(ps * 3))
        paste(c, text_img("1992년 출시 때 최고 모델 · 한국일보 보도", 36, CREAM, "Bold", stroke=4, sfill=(0, 0, 0),
                          shadow=3), W / 2, 1080, 1, 0, prog(t, hit + 0.3, 0.25))
    elif t < Ls(7) - 0.05:                                      # 6 각그랜저의 두 배
        lt = t - Ls(6)
        cred = "사진: Sim1992 · CC BY-SA 3.0 / Wikimedia Commons LX(확인 중)"
        G.panel(c, (34, 32, 30))
        base_y = 1250
        for k, (which, v, x) in enumerate([("gak", 1690, 300), ("lx", 3490, 780)]):
            hgt = int(400 * v / 3490 * out_cubic(prog(lt, 0.1 + 0.25 * k, 0.6)))
            ImageDraw.Draw(c).rectangle((x - 90, base_y - hgt, x + 90, base_y), fill=(AMBER if k else (150, 150, 155)))
            paste(c, text_img(f"{v:,}만", 52, WHITE, "Black", stroke=5, sfill=(0, 0, 0)), x, base_y - hgt - 40, 1, 0,
                  clamp(lt * 3))
            paste(c, polaroid(which, 220), x, base_y - hgt - 190, 0.9, -4 if k == 0 else 4, clamp(lt * 3))
        ps = prog(t, chunk_start(6, 1) + 0.1, 0.16)
        if ps > 0:
            paste(c, stamp("2배 넘게!", 58), 400, 600, 2.2 - 1.2 * ps, -6, clamp(ps * 3))
    elif t < Ls(9) - 0.05:                                      # 7·8 대졸 신입 월급 55만 × 63칸
        cred = None
        lt = t - Ls(7)
        G.panel(c, (32, 38, 34))
        head = compose((box(820, 110, 26, (250, 246, 236), shadow=False), 0, 0),
                       (text_img("1992 대졸 신입 월급 55만 원", 46, INK, "Black", shadow=0), 0, -3))
        paste(c, head, W / 2, 560, 1, 0, clamp(lt * 5))
        n = int(63 * out_cubic(prog(t, Ls(8) - 0.2, max(0.8, chunk_start(8, 1) - Ls(8)))))
        cols, dxs, dys = 9, 100, 58
        x0, y0 = W / 2 - (cols - 1) * dxs / 2, 660
        for k in range(63):
            r_, q = divmod(k, cols)
            x, y = x0 + q * dxs, y0 + r_ * dys
            ImageDraw.Draw(c).rounded_rectangle((x - 44, y - 24, x + 44, y + 24), 8, outline=(110, 130, 110), width=2)
            if k < n:
                paste(c, bill(), x, y, 0.58)
        if t >= Ls(8):
            if n >= 63:
                ps = out_back(prog(t, chunk_start(8, 1) - 0.25, 0.25))
                up = 300 * in_out(prog(t, chunk_start(8, 1) + 0.05, 0.3))
                paste(c, label("꼬박 5년 넘게!", 640, size=76), W / 2, 1140 - up, ps, -2, clamp(ps * 1.5))
            else:
                paste(c, text_img(f"{n}개월", 84, YEL, "Black", stroke=6, sfill=(0, 0, 0), shadow=4), W / 2, 1140)
        paste(c, text_img("3,490만 ÷ 55.7만 ≈ 62.6개월 · 1992 대한상의 조사(제조업 대졸 사무직 초임)", 26,
                          (215, 205, 190), "SemiBold", shadow=2), W / 2, 1295)
        pj = prog(t, chunk_start(8, 1) + 0.1, 0.3)
        if pj > 0:
            bx, by = W / 2, 1110
            paste(c, box(420, 300, 40, (32, 38, 34), shadow=True), bx, by, out_back(pj))
            paste(c, bowl(240), bx, by, out_back(pj))
            q = out_cubic(prog(t, chunk_start(8, 1) + 0.35, 0.2))
            if q > 0:
                d = ImageDraw.Draw(c)
                d.line((bx - 110, by - 110, bx - 110 + 220 * q, by - 110 + 220 * q), fill=RED, width=20)
                d.line((bx + 110, by - 110, bx + 110 - 220 * q, by - 110 + 220 * q), fill=RED, width=20)
    elif t < Ls(10) - 0.05:                                     # 9 1994 V6 3.5, 225마력
        cred = None
        lt = t - Ls(9)
        G.panel(c, (22, 22, 26))
        paste(c, label("1994 · V6 3.5", 560, AMBER, INK, 64), W / 2, 600, 1, -2, clamp(lt * 4))
        hp = int(225 * out_cubic(prog(t, chunk_start(9, 1) - 0.1, 0.9)))
        gauge(c, W / 2, 1010, 260, hp)
        paste(c, text_img(f"{hp}마력", 96, YEL, "Black", stroke=6, sfill=(0, 0, 0)), W / 2, 1110)
        pp = out_back(prog(t, chunk_start(9, 1) + 0.9, 0.25))
        paste(c, label("4,380만 원 육박", 600, size=66), W / 2, 1230, pp, 2, clamp(pp * 2))
        paste(c, text_img("오토뷰 보도", 26, (200, 200, 205), "SemiBold", shadow=2), W / 2, 1300, 1, 0, clamp(pp))
    elif t < Ls(11) - 0.05:                                     # 10 첫 차 댓글
        lt = t - Ls(10)
        put_card(c, lx_card(1.02))
        shade_card(c, 0.5)
        pb = out_back(prog(lt, 0.1, 0.3))
        paste(c, bubble("내 첫 차는…?"), W / 2, 760, pb, 0, clamp(pb * 2))
        pc = out_back(prog(t, chunk_start(10, 1), 0.3))
        paste(c, label("댓글로 알려 주세요", 640, size=60), W / 2, 1000, pc, 0, clamp(pc * 2))
    else:                                                       # 11 구독 → 첫 화면으로
        lt = t - Ls(11)
        back = in_out(prog(t, chunk_start(11, 2), 0.8))
        put_card(c, lx_card(1.0 + 0.02 * (1 - back)))
        shade_card(c, 0.4 * (1 - back))
        p = out_back(prog(lt, 0.05, 0.3)) * (1 - prog(t, chunk_start(11, 2), 0.3))
        sub = compose((box(420, 130, 65, RED, shadow=True), 0, 0), (text_img("구독", 76, WHITE, "Black", shadow=0), 0, -4))
        paste(c, sub, W / 2, 900, p, 0, clamp(p * 2))
    if cred:
        credit_line(c, cred)
    char_react(c, t)
    caption(c, t)
    if TL["preview"]:
        paste(c, text_img("녹음 전 미리보기 (무음)", 34, (255, 255, 255), "Bold", stroke=4, sfill=(200, 0, 0)), W / 2, 1640)
    ImageDraw.Draw(c).rectangle((0, 0, int(W * t / TL["total"]), 7), fill=AMBER)
    return c.convert("RGB")


# ------------------------------------------------------------------ 오디오
def build_audio(voice):
    sr = A.SR
    n = int(TL["total"] * sr)
    v = np.zeros(n)
    v[:len(voice)] = voice[:n]
    if np.abs(v).max() > 0:
        v = v / np.abs(v).max() * 0.92
    music = retro_bgm(TL["total"] + 1.0)[:n]
    act = np.convolve((np.abs(v) > 0.02).astype(float), np.ones(int(0.3 * sr)) / int(0.3 * sr), mode="same")
    duck = 1 - 0.55 * np.clip(act * 4, 0, 1)
    music = music * duck[:, None] * 0.7
    ev = []
    for k in range(0, 63, 4):
        ev.append((0.1 + max(0.8, Le(1) - 0.2) * (1 - (1 - k / 63) ** (1 / 3)), A.sfx_pop(), 0.3))
    ev += [(Ls(2) - 0.02, stamp_sfx(), 0.6), (chunk_start(3, 1), A.sfx_whoosh(0.35), 0.4),
           (chunk_start(4, 1), A.sfx_riser(0.8), 0.35)]
    hit = chunk_start(5, 1)
    ev += [(hit - 0.02, calc_sfx(), 1.0), (hit + 0.15, stamp_sfx(), 0.8), (chunk_start(6, 1) + 0.1, stamp_sfx(), 0.8),
           (Ls(7) - 0.12, A.sfx_whoosh(0.35), 0.4)]
    s8, e8 = Ls(8) - 0.2, chunk_start(8, 1)
    for k in range(0, 63, 3):
        ev.append((s8 + max(0.8, e8 - Ls(8)) * (1 - (1 - k / 63) ** (1 / 3)), tick_sfx(), 0.6))
    ev += [(chunk_start(8, 1) - 0.25, A.sfx_ding(), 0.5), (chunk_start(8, 1) + 0.35, stamp_sfx(), 0.6),
           (Ls(9) - 0.1, A.sfx_whoosh(0.4), 0.4), (chunk_start(9, 1) - 0.1, A.sfx_riser(0.9), 0.4),
           (chunk_start(9, 1) + 0.9, A.sfx_impact(), 0.6), (Ls(10) + 0.1, A.sfx_pop(), 0.5),
           (Ls(11) + 0.05, A.sfx_pop(), 0.5)]
    fx = np.zeros(n)
    for t0, snd, g in ev:
        i = int(max(0, t0) * sr)
        if i < n:
            snd = snd[: n - i]
            fx[i:i + len(snd)] += snd * g
    mix = music + (v + fx * 0.5)[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    os.makedirs(BUILD, exist_ok=True)
    p = os.path.join(BUILD, "mix.wav")
    A.write_wav(p, mix)
    return p


def write_srt(path):
    def ts(x):
        h, r = divmod(x, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s % 1) * 1000)) % 1000:03d}"
    with open(path, "w", encoding="utf-8") as f:
        for k, (st, en, cap) in enumerate(TL["chunks"], 1):
            f.write(f"{k}\n{ts(st)} --> {ts(en)}\n{cap.replace('*', '')}\n\n")


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
    voice = load_timeline()
    os.makedirs(BUILD, exist_ok=True)
    for k, (st, en) in enumerate(TL["lines"], 1):
        print(f"{k:2d} {st:6.2f}-{en:6.2f}")
    print("[total]", TL["total"], "(무음 미리보기)" if TL["preview"] else "")
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
    out = OUT.replace(".mp4", "_preview.mp4") if TL["preview"] else OUT
    af = [] if TL["preview"] else ["-af", "loudnorm=I=-14:TP=-1.5:LRA=9"]
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", mix] + af +
                          ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{TL['total']}",
                           "-movflags", "+faststart", out])
    write_srt(out.replace(".mp4", ".srt"))
    print("[done]", out)


if __name__ == "__main__":
    main()
