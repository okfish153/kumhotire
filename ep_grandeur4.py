"""그랜저로 보는 대한민국 40년 4/8 · 3세대 그랜저 XG (정보형 30초 세로 영상)

유튜브 쇼츠 · 네이버 클립 · 인스타그램 릴스 공용 (1080x1920, 30fps, 정확히 30.0초)
사용법: python3 ep_grandeur4.py                       # output/grandeur40_04_grandeur_xg.mp4
        python3 ep_grandeur4.py --preview 1 4 9 13     # 지정 초 프레임 PNG만

실차 사진(선택): assets/images/grandeur_xg.jpg (주 화면용 큰 사진)이 있으면 1·2·8장면을 사진 카드로,
                 없으면 직접 그린 설명용 그래픽으로 만든다. 사진을 넣으면 PHOTO_CREDIT도 고칠 것.

장면
 S1 퀴즈       : 1998 · IMF 한파 + 3지선다
 S2 정답       : 2,200만~2,700만 원대, '정답' 도장
 S3 비교       : 뉴 그랜저 3.0 골드 3,490만 vs XG 출시가 2,200만~2,700만 → '오히려 ↓' 도장
 S4 금 모으기  : 금괴가 쌓임 → '문짝부터 달랐다'
 S5 프레임리스 : 창틀이 사라지고 문이 열리며 유리만 쏙
 S6 귀환       : 1998 XG ↔ 요즘 그랜저, 같은 프레임리스 도어
 S7 이름       : X · G 알파벳 두 글자가 쾅쾅
 S8 정리·예고  : '회장님 차' 도장 → 시리즈 카드, 다음 편 5/8 그랜저 TG

팩트
 - 1998년 9월 발표, 10월 1일 판매 시작, 가격 2,200만~2,700만 원대: 한국일보 1998-09-24
 - 2세대 뉴 그랜저 3.0 골드 3,490만 원: 한국일보 1992-09-17
 - 프레임리스 도어(최신 그랜저의 프레임리스 도어가 XG를 떠올리게 함): 현대자동차그룹 스토리
 - 1998년 금 모으기 운동, 1997~98 외환위기
BGM·효과음: ep_grandeur2.py 의 자체 합성 음원 재사용 (외부 음원 없음).
"""
import argparse
import math
import os
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

import audio as A
import narration
import ep_grandeur2 as G
import ep_grandeur3 as E3
from ep_grandeur2 import (CREAM, AMBER, RED, INK, CARD_W, CARD_H, CARD_Y, option_chip, stamp,
                          key_caption, jolt, panel, card_shadow, card_mask, retro_bgm, calc_sfx,
                          stamp_sfx, tick_sfx)
from ep_grandeur3 import catmull, small, polaroid
from video import (W, H, YEL, WHITE, prog, out_cubic, out_back, in_out, clamp,
                   text_img, box, compose, paste, cover)

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build", "grandeur4")
OUT = os.path.join(ROOT, "output")
OUT_NAME = "grandeur40_04_grandeur_xg"
PHOTO_PATH = os.path.join(ROOT, "assets", "images", "grandeur_xg.jpg")
PHOTO_CREDIT = ""      # 예: '사진: "파일명" by 저작자 · CC BY 2.0 · Wikimedia Commons (크롭)'
FPS = 30
TOTAL = 30.0
TEMPO = 1.08
GAP = 0.24
TEAL = (20, 46, 52)
GOLD = (236, 186, 64)

LINES = [
    ("외환위기 한파 속 천구백구십팔 년, 새 그랜저 값은 얼마였을까요?", ["외환위기 한파 속 1998년,", "새 그랜저 값은 얼마였을까요?"], "s1"),
    ("정답은 이천이백만에서 이천칠백만 원대!", ["정답은 2,200만~2,700만 원대!"], "s2"),
    ("뉴 그랜저 최고급보다 오히려 낮게 시작했죠.", ["뉴 그랜저 최고급보다", "오히려 낮게 시작했죠"], "s3"),
    ("금 모으기 운동의 해, 문짝부터 달랐습니다.", ["금 모으기 운동의 해,", "문짝부터 달랐습니다"], "s4"),
    ("창틀 없는 문, 프레임리스 도어! 문을 열면 유리만 쏙.", ["창틀 없는 문, 프레임리스 도어!", "문을 열면 유리만 쏙"], "s5"),
    ("이 프레임리스 도어는 요즘 그랜저에 다시 돌아왔죠.", ["이 프레임리스 도어는", "요즘 그랜저에 다시 돌아왔죠"], "s6"),
    ("이름도 처음으로 알파벳 두 글자, XG.", ["이름도 처음으로 알파벳 두 글자, XG"], "s7"),
    ("어려운 시절에도 사랑받은 그 시절 회장님 차.", ["어려운 시절에도 사랑받은", "그 시절 회장님 차"], "s8"),
    ("다음 편, 그랜저 TG.", ["다음 편, 그랜저 TG"], None),
]
TL = {"lines": [], "scenes": []}


def L(i):
    return TL["lines"][i]


def has_photo():
    return os.path.exists(PHOTO_PATH)


@lru_cache(None)
def photo():
    return ImageEnhance.Color(Image.open(PHOTO_PATH).convert("RGB")).enhance(1.05).convert("RGBA")


def put_photo(c, zoom=1.0, fx=0.5, fy=0.5, dx=0, dy=0, alpha=1.0):
    inner = cover(photo(), CARD_W, CARD_H, zoom, fx, fy)
    inner.putalpha(card_mask())
    paste(c, card_shadow(), W / 2 + dx, CARD_Y + dy, 1, 0, 0.9 * alpha)
    paste(c, inner, W / 2 + dx, CARD_Y + dy, 1, 0, alpha)
    if PHOTO_CREDIT:
        paste(c, small(PHOTO_CREDIT, 22, (225, 225, 225)), W / 2, 1362, 1, 0, alpha)


# ------------------------------------------------------------------ 그래픽
@lru_cache(None)
def bg():
    if has_photo():
        im = cover(photo(), W, H, 1.0).filter(ImageFilter.GaussianBlur(40))
        return ImageEnhance.Brightness(im).enhance(0.34)
    a = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array((24, 58, 64)) * (1 - a) + np.array((8, 14, 16)) * a) * np.ones((1, W, 1))
    im = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    for k in range(-H, W, 90):
        g.line((k, H, k + H * 0.6, 0), fill=(255, 255, 255, 8), width=26)
    im.alpha_composite(lay)
    return im


@lru_cache(None)
def xg_side(color=(196, 200, 206)):
    """3세대 그랜저 XG 측면을 단순화한 설명용 그래픽 (실차 사진 아님). 창틀 없는 옆창."""
    w, h, S = 1000, 560, 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)

    def P(pts):
        return [(x * S, y * S) for x, y in pts]
    body = catmull([(24, 366), (40, 312), (150, 288), (300, 272), (400, 192), (520, 172), (650, 178),
                    (770, 248), (910, 266), (976, 300), (980, 368), (930, 402), (70, 402)])
    g.polygon(P(body), fill=color, outline=(238, 240, 246))
    glass = catmull([(416, 202), (520, 184), (642, 188), (742, 254), (408, 258)])
    g.polygon(P(glass), fill=(48, 62, 80))
    g.line(P(catmull([(36, 336), (520, 330), (968, 338)], closed=False)), fill=(230, 232, 238), width=4 * S)
    g.line(P([(560, 300), (560, 396)]), fill=(140, 144, 152), width=2 * S)
    for cx in (215, 795):
        g.ellipse(P([(cx - 70, 326), (cx + 70, 466)]), fill=(24, 24, 28), outline=(205, 205, 210), width=4 * S)
        for k in range(5):
            a = 2 * math.pi * k / 5
            g.line(P([(cx, 396), (cx + 30 * math.cos(a), 396 + 30 * math.sin(a))]), fill=(190, 192, 200), width=5 * S)
    return im.resize((w, h), Image.LANCZOS)


def main_visual(c, lt, dur=3.0, dx=0, dy=0, alpha=1.0, label=True):
    if has_photo():
        put_photo(c, 1.0 + 0.06 * in_out(prog(lt, 0, dur)), dx=dx, dy=dy, alpha=alpha)
    else:
        paste(c, box(CARD_W, CARD_H, 30, TEAL, shadow=True), W / 2 + dx, CARD_Y + dy, 1, 0, alpha)
        paste(c, xg_side(), W / 2 + dx, CARD_Y - 30 + dy, 0.92 + 0.04 * in_out(prog(lt, 0, dur)), 0, alpha)
        if label:
            paste(c, small("설명용 그래픽 · 실제 차량 사진 아님"), W / 2, CARD_Y - 380, 1, 0, alpha)


@lru_cache(None)
def series_pill():
    t1 = text_img("그랜저로 보는 대한민국 40년", 34, CREAM, "Bold", shadow=0)
    t2 = text_img("4/8 · 3세대 그랜저 XG", 34, INK, "Black", shadow=0)
    w = t1.width + t2.width + 40
    b = box(w + 40, 74, 37, (0, 0, 0, 160), shadow=False)
    hi = box(t2.width + 30, 58, 29, AMBER, shadow=False)
    return compose((b, 0, 0), (t1, -(w // 2) + t1.width // 2 + 10, 0),
                   (hi, w // 2 - t2.width // 2 - 5, 0), (t2, w // 2 - t2.width // 2 - 5, 0))


def subtitle(c, t):
    for i, (st, en) in enumerate(TL["lines"]):
        if not (st - 0.05 <= t < en + 0.2):
            continue
        parts = LINES[i][1]
        ws = [len(p) for p in parts]
        acc, k = st, 0
        for k, wv in enumerate(ws):
            acc += (en - st) * wv / sum(ws)
            if t < acc:
                break
        im = text_img(parts[k], 52, WHITE, "Bold", stroke=6, sfill=(0, 0, 0), shadow=4)
        if im.width > 1020:
            im = im.resize((1020, int(im.height * 1020 / im.width)), Image.BICUBIC)
        paste(c, im, W / 2, 1418)
        return


@lru_cache(None)
def gold_bar(w=150):
    h = int(w * 0.42)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    g.polygon([(w * .14, 0), (w * .86, 0), (w - 1, h - 1), (0, h - 1)], fill=GOLD, outline=(150, 110, 20))
    g.polygon([(w * .2, h * .12), (w * .8, h * .12), (w * .88, h * .78), (w * .12, h * .78)], fill=(250, 214, 110))
    t = text_img("金", int(h * .55), (170, 120, 20), "Black", shadow=0)
    im.alpha_composite(t, ((w - t.width) // 2, int(h * .12)))
    return im


# ------------------------------------------------------------------ 장면
OPTS = [("1", "3,500만 ↑"), ("2", "2,200만 ~"), ("3", "5,000만 원")]


def s1(c, t, t0):
    lt = t - t0
    main_visual(c, lt, 3.0)
    G.shade_card(c, 0.4 * prog(lt, 0.6, 0.3))
    # 'IMF' 한파 눈송이
    rng = np.random.default_rng(11)
    for k in range(26):
        x = rng.random() * W
        y = (rng.random() * 900 + lt * (80 + 60 * rng.random())) % 900 + 480
        paste(c, text_img("❄" if False else "*", 44, (220, 236, 255), "Black", shadow=0), x, y, 1, lt * 40, 0.55)
    pk = out_back(prog(lt, 0.15, 0.3))
    tag = compose((box(420, 110, 55, (40, 120, 200), WHITE, 5, True), 0, 0),
                  (text_img("1998 · IMF", 58, WHITE, "Black", shadow=0), 0, -3))
    paste(c, tag, 300, 610, pk, -4, clamp(pk * 1.5))
    for k, (no, txt) in enumerate(OPTS):
        pk = out_back(prog(lt, 1.0 + 0.4 * k, 0.3))
        paste(c, option_chip(no, txt), W / 2 + 100, 900 + k * 140, pk * 0.9, 0, clamp(pk * 1.4))
    key_caption(c, "외환위기 한파 속 *새 그랜저* 값은?", t0 + 0.1, t0 + 9, t, size=80)


def s2(c, t, t0):
    lt = t - t0
    hit = t0 + 0.45
    dx, dy = jolt(t, hit, 22)
    main_visual(c, 1.0, dx=dx, dy=dy, label=False)
    G.shade_card(c, 0.66)
    for k in (0, 2):
        no, txt = OPTS[k]
        paste(c, option_chip(no, txt, 2), W / 2 + 100, 900 + k * 140, 0.9, 0, 1 - prog(lt, 0, 0.25))
    if t < hit:
        val = int(22_000_000 * out_cubic(clamp(lt / 0.45)) + np.random.default_rng(int(t * 60)).integers(0, 9999))
        txt, sc, size = f"{val // 10000:,}만", 1.0, 160
    else:
        txt, sc, size = "2,200만~2,700만", 1.0 + 0.15 * (1 - out_cubic(prog(t, hit, 0.25))), 120
    paste(c, text_img(txt, size, YEL if t >= hit else WHITE, "Black", stroke=6, sfill=(0, 0, 0), shadow=10),
          W / 2 + dx, 800 + dy, sc)
    if t >= hit:
        paste(c, text_img("원대 · 1998년 출시 발표", 60, CREAM, "Bold", stroke=4, sfill=(0, 0, 0), shadow=4),
              W / 2, 930, 1, 0, prog(t, hit, 0.3))
        ps = prog(t, hit + 0.15, 0.18)
        paste(c, stamp("정답", 92), W / 2 + 300, 1110, 2.2 - 1.2 * ps, 0, clamp(ps * 3))
        paste(c, small("한국일보 1998.9.24 보도 · 10월 1일 판매 시작", 26, (235, 230, 220)), W / 2, 1290, 1, 0,
              prog(t, hit + 0.3, 0.3))
    key_caption(c, "정답 *2,200만~2,700만 원대*", hit, t0 + 9, t, size=84)


def s3(c, t, t0):
    lt = t - t0
    panel(c, (30, 30, 36))
    base, maxh = 1150, 520
    d = ImageDraw.Draw(c)
    # 1992 뉴 그랜저 3.0 골드
    x1 = W / 2 - 210
    h1 = maxh * out_cubic(prog(lt, 0.1, 0.5))
    d.rounded_rectangle((x1 - 105, base - h1, x1 + 105, base), 18, fill=(150, 150, 160))
    if h1 > 5:
        paste(c, text_img("3,490만", 50, WHITE, "Black", stroke=5, sfill=(0, 0, 0), shadow=3), x1, base - h1 - 40)
    # 1998 XG: 2,200~2,700 범위 막대
    x2 = W / 2 + 210
    p2 = out_cubic(prog(lt, 0.45, 0.5))
    lo, hi = maxh * 2200 / 3490 * p2, maxh * 2700 / 3490 * p2
    d.rounded_rectangle((x2 - 105, base - lo, x2 + 105, base), 18, fill=AMBER)
    d.rounded_rectangle((x2 - 105, base - hi, x2 + 105, base - lo + 10), 18, fill=(255, 210, 140))
    if p2 > 0.05:
        paste(c, text_img("2,200만~2,700만", 44, WHITE, "Black", stroke=5, sfill=(0, 0, 0), shadow=3), x2, base - hi - 40)
    for x, yr, nm in [(x1, "1992", "뉴 그랜저 3.0 골드"), (x2, "1998", "그랜저 XG 출시가")]:
        paste(c, text_img(yr, 44, WHITE, "Black", shadow=0), x, base + 40)
        paste(c, small(nm, 30, CREAM), x, base + 86)
    ps = prog(lt, 1.1, 0.16)
    if ps > 0:
        paste(c, stamp("오히려 ↓", 96, RED, rot=-8), W / 2, 1010, (2.2 - 1.2 * ps) * 0.8, 0, clamp(ps * 3))
    paste(c, small("1992 3.0 골드: 한국일보 1992.9.17 · 1998 XG: 한국일보 1998.9.24 (트림 구성이 다름)"), W / 2, 1335,
          1, 0, prog(lt, 0.5, 0.3))
    key_caption(c, "값은 *오히려 낮게* 시작", t0 + 0.1, t0 + 9, t, size=88)


def s4(c, t, t0):
    lt = t - t0
    panel(c, (40, 32, 20))
    # 금괴가 하나씩 떨어져 피라미드로 쌓임
    slots = []
    for row, n in enumerate([5, 4, 3, 2, 1]):
        for k in range(n):
            slots.append((W / 2 + (k - (n - 1) / 2) * 156, 1150 - row * 66))
    for k, (x, y) in enumerate(slots):
        p = out_cubic(prog(lt, 0.05 + 0.09 * k, 0.25))
        if p > 0:
            paste(c, gold_bar(), x, 480 + (y - 480) * p, 1, 0, 1)
    pk = out_back(prog(lt, 1.2, 0.3))
    tag = compose((box(560, 110, 55, GOLD, INK, 5, True), 0, 0),
                  (text_img("1998 금 모으기 운동", 52, INK, "Black", shadow=0), 0, -3))
    paste(c, tag, W / 2, 640, pk, -3, clamp(pk * 1.5))
    key_caption(c, "그해, *문짝부터* 달랐다", t0 + 0.1, t0 + 9, t, size=88)


@lru_cache(None)
def door(frame_a, open_p):
    """옆문 그래픽: frame_a = 창틀 불투명도(1→0), open_p = 문 열림 0~1"""
    w, h = 760, 720
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    sx = 1 - 0.45 * open_p           # 열리면서 가로로 짧아 보이게
    def X(x):
        return 380 + (x - 380) * sx
    # 문 판넬
    g.polygon([(X(90), 330), (X(670), 330), (X(650), 680), (X(110), 680)], fill=(196, 200, 206), outline=(240, 242, 246))
    g.line((X(110), 470, X(660), 470), fill=(230, 232, 238), width=6)
    g.rounded_rectangle((X(540), 400, X(610), 420), 8, fill=(150, 154, 162))
    # 유리
    g.polygon([(X(130), 320), (X(640), 320), (X(560), 90), (X(210), 110)], fill=(120, 170, 210, 200))
    g.line((X(260), 140, X(330), 300), fill=(255, 255, 255, 120), width=10)
    # 창틀
    if frame_a > 0.02:
        a = int(255 * frame_a)
        g.line([(X(130), 320), (X(210), 110), (X(560), 90), (X(640), 320)], fill=(40, 40, 46, a), width=26, joint="curve")
    return im


def s5(c, t, t0):
    lt = t - t0
    panel(c, TEAL)
    fa = 1 - in_out(prog(lt, 0.4, 0.8))
    op = in_out(prog(lt, 1.6, 0.7))
    paste(c, door(round(fa * 10) / 10, round(op * 14) / 14), W / 2 + 200 * op, 900)
    if 0.4 < lt < 1.6:
        p = prog(lt, 0.4, 0.8)
        ImageDraw.Draw(c).line((330, 640, 330 + 420 * p, 640 + 220 * p), fill=RED, width=14)
        ImageDraw.Draw(c).line((750, 640, 750 - 420 * p, 640 + 220 * p), fill=RED, width=14)
    if lt >= 1.6:
        pk = out_back(prog(lt, 1.9, 0.3))
        tag = compose((box(420, 100, 50, YEL, INK, 5, True), 0, 0),
                      (text_img("유리만 쏙!", 56, INK, "Black", shadow=0), 0, -3))
        paste(c, tag, 300, 650, pk, -5, clamp(pk * 1.5))
    paste(c, small("창틀 없는 옆문 · 단순화한 설명용 그래픽"), W / 2, 1335)
    key_caption(c, "창틀 없는 *프레임리스 도어*", t0 + 0.1, t0 + 9, t, size=84)


def s6(c, t, t0):
    lt = t - t0
    panel(c, (24, 28, 36))
    for k, (yr, lab, x) in enumerate([("1998", "그랜저 XG", W / 2 - 230), ("요즘", "그랜저", W / 2 + 230)]):
        pk = out_back(prog(lt, 0.1 + 0.4 * k, 0.3))
        dv = door(0.0, 0.0).resize((380, 360), Image.LANCZOS)
        card = compose((box(420, 520, 30, (44, 50, 62), shadow=True), 0, 0), (dv, 0, -40),
                       (text_img(yr, 56, YEL, "Black", shadow=0), 0, 170), (text_img(lab, 40, CREAM, "Bold", shadow=0), 0, 225))
        paste(c, card, x, 880, pk, (-4, 4)[k], clamp(pk * 1.4))
    pe = out_back(prog(lt, 1.1, 0.3))
    paste(c, text_img("=", 140, WHITE, "Black", stroke=6, sfill=(0, 0, 0), shadow=4), W / 2, 860, pe, 0, clamp(pe * 1.5))
    pr = out_back(prog(lt, 1.5, 0.3))
    tag = compose((box(520, 100, 50, RED, CREAM, 4, True), 0, 0),
                  (text_img("다시 돌아왔다!", 54, WHITE, "Black", shadow=0), 0, -3))
    paste(c, tag, W / 2, 1220, pr, -2, clamp(pr * 1.5))
    paste(c, small("최신 그랜저의 프레임리스 도어는 XG를 떠올리게 함 · 현대자동차그룹 스토리"), W / 2, 1335)
    key_caption(c, "XG의 문, *요즘 그랜저*에 귀환", t0 + 0.1, t0 + 9, t, size=82)


def s7(c, t, t0):
    lt = t - t0
    panel(c, (18, 18, 22))
    hits = [0.45, 0.8]
    dx, dy = 0, 0
    for h in hits:
        jx, jy = jolt(lt, h, 16, 0.25)
        dx += jx; dy += jy
    for k, (ch, x) in enumerate([("X", W / 2 - 150), ("G", W / 2 + 150)]):
        p = prog(lt, hits[k], 0.14)
        if p > 0:
            paste(c, text_img(ch, 330, YEL if k else WHITE, "Black", stroke=10, sfill=(0, 0, 0), shadow=8),
                  x + dx, 860 + dy, 2.0 - 1.0 * p, 0, clamp(p * 3))
    names = [("1986", "그랜저"), ("1992", "뉴 그랜저"), ("1998", "그랜저 XG")]
    for k, (yr, nm) in enumerate(names):
        pk = out_cubic(prog(lt, 1.2 + 0.15 * k, 0.3))
        row = text_img(f"{yr}  {nm}", 44, YEL if k == 2 else (200, 200, 200), "Black" if k == 2 else "Bold", shadow=0)
        paste(c, row, W / 2, 1110 + k * 62, 1, 0, pk)
    key_caption(c, "이름도 처음으로 *알파벳 두 글자*", t0 + 0.1, t0 + 9, t, size=80)


def s8(c, t, t0):
    lt = t - t0
    t_next = L(8)[0] - 0.15
    a = 1 - prog(t, t_next - 0.3, 0.3)
    if a > 0:
        hit = t0 + 1.1
        dx, dy = jolt(t, hit, 22)
        main_visual(c, lt, 2.0, dx, dy, a, label=False)
        ps = prog(t, hit, 0.16)
        if ps > 0:
            paste(c, stamp("회장님 차", 130, RED, rot=-9), W / 2 + dx, 900 + dy, 2.4 - 1.4 * ps, 0, clamp(ps * 3) * a)
        key_caption(c, "어려운 시절에도 *사랑받은 차*", t0 + 0.1, t_next, t, size=82)
    if t >= t_next - 0.3:
        b = prog(t, t_next - 0.3, 0.3)
        c.alpha_composite(Image.new("RGBA", (W, H), (14, 14, 18, int(235 * b))))
        rows = [("3/8", "2세대 뉴 그랜저  ✓"), ("4/8", "3세대 그랜저 XG  ✓"), ("5/8", "4세대 그랜저 TG")]
        for k, (no, name) in enumerate(rows):
            pk = out_cubic(prog(t, t_next + 0.12 * k, 0.3))
            hi = k == 1
            bx = box(820, 116, 26, AMBER if hi else (44, 44, 52), None, 0, False)
            tn = text_img(no, 48, INK if hi else CREAM, "Black", shadow=0)
            tm = text_img(name, 50, INK if hi else CREAM, "Black" if hi else "Bold", shadow=0)
            row = compose((bx, 0, 0), (tn, -330, 0), (tm, -250 + tm.width // 2 + 20, 0))
            paste(c, row, W / 2 + (1 - pk) * 200, 620 + k * 150, 1, 0, pk * (0.55 if k == 0 else 1))
        pn = out_back(prog(t, t_next + 0.9, 0.3))
        if pn > 0:
            nb = compose((box(680, 190, 40, YEL, INK, 6, True), 0, 0),
                         (text_img("다음 편 5/8", 80, INK, "Black", shadow=0), 0, -36),
                         (text_img("그랜저 TG", 50, INK, "Bold", shadow=0), 0, 50))
            paste(c, nb, W / 2, 1150, 0.6 + 0.4 * pn, -2, clamp(pn * 1.5))


FN = {"s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5, "s6": s6, "s7": s7, "s8": s8}


def frame(i):
    t = i / FPS
    sc = TL["scenes"]
    k = max(j for j in range(len(sc)) if sc[j][0] <= t)
    t0, name = sc[k]
    c = bg().copy()
    FN[name](c, t, t0)
    paste(c, series_pill(), W / 2, 262)
    subtitle(c, t)
    if k > 0 and t - t0 < 0.1:
        c.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(120 * (1 - (t - t0) / 0.1)))))
    ImageDraw.Draw(c).rectangle((0, 0, int(W * t / TOTAL), 7), fill=AMBER)
    return c.convert("RGB")


# ------------------------------------------------------------------ 오디오
def clink_sfx():
    t = A._t(0.4)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in [(2400, 14), (3700, 18), (5200, 24)])
    return x * 0.25


def door_sfx():
    t = A._t(0.35)
    thud = np.sin(2 * np.pi * (90 + 40 * np.exp(-t * 20)) * t) * np.exp(-t * 18)
    latch = A._filt(A.rng.standard_normal(len(t)), "bandpass", [1500, 5000]) * np.exp(-t * 60) * 0.5
    return thud * 0.8 + latch


def sfx_events():
    ev = []
    sc = dict((name, st) for st, name in TL["scenes"])
    for st, name in TL["scenes"][1:]:
        ev.append((st - 0.12, A.sfx_whoosh(0.35), 0.45))
    t1 = sc["s1"]
    ev += [(t1 + 0.15, A.sfx_pop(), 0.6)] + [(t1 + 1.0 + 0.4 * k, A.sfx_pop(), 0.7) for k in range(3)]
    hit = sc["s2"] + 0.45
    ev += [(hit - 0.02, calc_sfx(), 1.0), (hit + 0.15, stamp_sfx(), 0.8)]
    s3 = sc["s3"]
    ev += [(s3 + 0.1, A.sfx_riser(0.5), 0.25), (s3 + 0.45, A.sfx_whoosh(0.4, False), 0.35), (s3 + 1.1, stamp_sfx(), 0.85)]
    s4 = sc["s4"]
    for k in range(15):
        ev.append((s4 + 0.05 + 0.09 * k + 0.22, clink_sfx(), 0.5))
    ev += [(s4 + 1.2, A.sfx_pop(), 0.6)]
    s5 = sc["s5"]
    ev += [(s5 + 0.4, A.sfx_whoosh(0.6), 0.35), (s5 + 1.6, door_sfx(), 0.9), (s5 + 1.9, A.sfx_ding(), 0.5)]
    s6 = sc["s6"]
    ev += [(s6 + 0.1, A.sfx_pop(), 0.6), (s6 + 0.5, A.sfx_pop(), 0.6), (s6 + 1.5, A.sfx_ding(), 0.6)]
    s7 = sc["s7"]
    ev += [(s7 + 0.43, stamp_sfx(), 0.9), (s7 + 0.78, stamp_sfx(), 0.9)]
    s8 = sc["s8"]
    ev += [(s8 + 1.08, stamp_sfx(), 1.0), (s8 + 1.1, A.sfx_impact(), 0.5)]
    tn = L(8)[0] - 0.15
    ev += [(tn + 0.9, A.sfx_ding(), 0.6)]
    return ev


def build_audio(narr):
    sr = A.SR
    n = int(TOTAL * sr)
    voice = np.zeros(n)
    for i, path in enumerate(narr):
        v = A.read_wav(path)
        s = int(L(i)[0] * sr)
        v = v[: n - s]
        voice[s:s + len(v)] += v
    voice = voice / max(1e-6, np.abs(voice).max()) * 0.92
    music = retro_bgm(TOTAL + 5.0)[int(4.8 * sr): int(4.8 * sr) + n]     # 2·3편과 다른 마디부터
    act = (np.abs(voice) > 0.02).astype(float)
    win = int(0.3 * sr)
    act = np.convolve(act, np.ones(win) / win, mode="same")
    duck = 1 - 0.5 * np.clip(act * 4, 0, 1)
    env = np.ones(n)
    fi, fo = int(0.3 * sr), int(1.5 * sr)
    env[:fi] = np.linspace(0, 1, fi)
    env[-fo:] = np.linspace(1, 0, fo)
    music = music * (duck * env)[:, None] * 0.75
    fx = np.zeros(n)
    for t0, s, g in sfx_events():
        i = int(max(0, t0) * sr)
        if i >= n:
            continue
        s = s[: n - i]
        fx[i:i + len(s)] += s * g
    mix = music + (voice + fx * 0.55)[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    path = os.path.join(BUILD, "mix.wav")
    A.write_wav(path, mix)
    return path


# ------------------------------------------------------------------ 타임라인·렌더
def make_narration():
    texts = [l[0] for l in LINES]
    narration.generate(BUILD, "supertonic", texts, "/nonexistent")
    paths, t = [], 0.12
    TL["lines"], TL["scenes"] = [], []
    for i, line in enumerate(LINES):
        p = os.path.join(BUILD, f"narr_{i:02d}.wav")
        q = os.path.join(BUILD, f"narr_{i:02d}_t.wav")
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-af", f"atempo={TEMPO}", q])
        d = narration.probe_duration(q)
        gap = 0.45 if i == len(LINES) - 1 else GAP
        if i:
            t += gap
        TL["lines"].append((round(t, 3), round(t + d, 3)))
        if line[2]:
            TL["scenes"].append((0.0 if i == 0 else round(t - 0.1, 3), line[2]))
        t += d
        paths.append(q)
    assert TL["lines"][-1][1] < TOTAL - 1.8, f"내레이션이 너무 깁니다: {TL['lines'][-1]}"
    return paths


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


def write_srt(path):
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(path, "w", encoding="utf-8") as f:
        for i, (st, en) in enumerate(TL["lines"]):
            f.write(f"{i + 1}\n{ts(st)} --> {ts(en + 0.2)}\n{' '.join(LINES[i][1])}\n\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", nargs="*", type=float)
    a = ap.parse_args()
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    narr = make_narration()
    print("[lines] ", TL["lines"])
    print("[scenes]", TL["scenes"])
    print("[photo] ", "사용" if has_photo() else "없음 → 설명용 그래픽")
    if a.preview is not None:
        for s in a.preview:
            out = os.path.join(BUILD, f"preview_{s:05.2f}.png")
            frame(int(s * FPS)).save(out)
            print(out)
        return
    mix = build_audio(narr)
    from multiprocessing import Pool
    n = int(TOTAL * FPS)
    k = 4
    step = math.ceil(n / k)
    jobs = [(j * step, min(n, (j + 1) * step), os.path.join(BUILD, f"part_{j}.mp4"), dict(TL)) for j in range(k)]
    with Pool(k) as pool:
        parts = pool.map(_render_part, jobs)
    lst = os.path.join(BUILD, "parts.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    vid = os.path.join(BUILD, "video_noaudio.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vid])
    final = os.path.join(OUT, OUT_NAME + ".mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", mix,
                           "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                           "-ar", "48000", "-t", f"{TOTAL}", "-movflags", "+faststart", final])
    write_srt(os.path.join(OUT, OUT_NAME + ".srt"))
    print("[done]", final)


if __name__ == "__main__":
    main()
