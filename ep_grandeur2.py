"""그랜저로 보는 대한민국 40년 2/8 · 1세대 각그랜저 (정보형 30초 세로 영상)

유튜브 쇼츠 · 네이버 클립 · 인스타그램 릴스 공용 (1080x1920, 30fps, 정확히 30.0초)
사용법: python3 ep_grandeur2.py                       # output/grandeur40_02_gak_grandeur.mp4
        python3 ep_grandeur2.py --preview 1 4 9 13     # 지정 초 프레임 PNG만

장면
 S1 퀴즈      : 실차 사진 + '짜장면 600원' 메모 + 3지선다(169만/1,690만/1억)
 S2 정답      : 숫자 롤링 → 1,690만 원, '정답' 도장
 S3 월급 환산 : 1986 대기업 신입 기본급 31만 원 x 54칸 → 4년 반
 S4 짜장면 환산 : 그릇이 쏟아지며 약 2만 8천 그릇 → 매일 한 그릇 77년
 S5 디자인    : 크롬 라인 → 후면 램프 → '각!' 도장 3개
 S6 오페라 글라스 : 설명용 그래픽 → 뒷유리 너머 뒷좌석(원본 사진)
 S7 회장님 차 : 낙관 도장 '회장님 차' 쾅 → 노을빛 여운
 S8 예고      : 네모가 둥글게 변하며 '그 각이 사라집니다' → 다음 편 3/8

팩트: 1986년 출시 · 초기 1,690만 원 · 짜장면 600원 · 대기업 초임 기본급 평균 31만 원 (오토뷰 보도)
      오페라 글라스·크롬 몰딩 (현대자동차그룹 공식 스토리)
      16,900,000/310,000 = 54.5개월(약 4년 반), 16,900,000/600 = 28,167그릇, /365 = 77.2년
사진: "1986-1989 Hyundai grandeur rear" by Sim1992, CC BY-SA 3.0 (Wikimedia Commons)
      -> 번호판 흐림·크롭·색보정. 편집한 사진은 같은 CC BY-SA 3.0을 따름.
BGM·효과음: audio.py 와 이 스크립트에서 직접 합성 (외부 음원 없음).
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
from video import (W, H, YEL, WHITE, prog, out_cubic, out_back, in_out, clamp,
                   text_img, rich_img, box, compose, paste, cover)

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build", "grandeur2")
OUT = os.path.join(ROOT, "output")
OUT_NAME = "grandeur40_02_gak_grandeur"
PHOTO_PATH = os.path.join(ROOT, "assets", "images", "grandeur_l_rear_sim1992.jpg")
FPS = 30
TOTAL = 30.0
TEMPO = 1.08          # 내레이션 배속
GAP = 0.24            # 대사 사이 호흡

CREAM = (246, 236, 214)
AMBER = (255, 176, 59)
RED = (205, 28, 28)
INK = (24, 22, 20)
BG = (18, 16, 15)

# (대사, 화면 아래 자막 조각들, 이 대사에서 새 장면이 시작되면 장면 함수 이름)
LINES = [
    ("짜장면이 육백 원이던 시절, 이 차는 얼마였을까요?", ["짜장면이 600원이던 시절,", "이 차는 얼마였을까요?"], "s1"),
    ("정답은 천육백구십만 원!", ["정답은 1,690만 원!"], "s2"),
    ("그때 대기업 신입 월급을 사 년 반 꼬박 모아야 했죠.", ["그때 대기업 신입 월급을", "4년 반 꼬박 모아야 했죠"], "s3"),
    ("짜장면으로 치면 이만 팔천 그릇. 매일 한 그릇씩 칠십칠 년!", ["짜장면으로 치면 2만 8천 그릇", "매일 한 그릇씩 77년!"], "s4"),
    ("네모 반듯한 차체에 번쩍이는 크롬. 별명부터 각그랜저.", ["네모 반듯한 차체에 번쩍이는 크롬", "별명부터 각그랜저"], "s5"),
    ("뒷좌석 옆엔 뒷자리 손님을 위한 작은 창, 오페라 글라스까지.", ["뒷좌석 옆엔 뒷자리 손님을 위한 작은 창,", "오페라 글라스까지"], "s6"),
    ("그러니 그 시절 별명은 단 하나, 회장님 차!", ["그러니 그 시절 별명은 단 하나,", "회장님 차!"], "s7"),
    ("동네에 한 대만 서 있어도 다들 돌아봤죠.", ["동네에 한 대만 서 있어도 다들 돌아봤죠"], None),
    ("다음 편, 그 각이 사라집니다.", ["다음 편, 그 각이 사라집니다"], "s8"),
]
TL = {"lines": [], "scenes": []}   # lines: [(start, end)], scenes: [(start, fn_name)]


def L(i):
    return TL["lines"][i]


# ------------------------------------------------------------------ 사진
@lru_cache(None)
def photo(grade=0.0):
    """원본 사진: 번호판 흐림 + 아주 약한 보정. grade>0 이면 노을빛."""
    im = Image.open(PHOTO_PATH).convert("RGB")
    plate = (338, 618, 535, 760)
    im.paste(im.crop(plate).filter(ImageFilter.GaussianBlur(16)), plate[:2])
    im = ImageEnhance.Color(im).enhance(1.06)
    if grade:
        arr = np.asarray(im, dtype=np.float32)
        warm = arr * np.array([1.12, 0.98, 0.82]) + np.array([16, 4, -8])
        arr = arr * (1 - grade) + warm * grade
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return im.convert("RGBA")


@lru_cache(None)
def bg_photo():
    im = cover(photo(), W, H, 1.0, 0.55, 0.5).filter(ImageFilter.GaussianBlur(40))
    return ImageEnhance.Brightness(im).enhance(0.32)


@lru_cache(None)
def bg_dark():
    a = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array((40, 32, 28)) * (1 - a) + np.array((12, 10, 10)) * a) * np.ones((1, W, 1))
    return Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")


CARD_W, CARD_H, CARD_Y = 1000, 860, 905
MAIN_BOX = (200, 30, 1282, 875)      # 왼쪽 다른 차량을 대부분 뺀 영역


@lru_cache(None)
def card_mask(r=30):
    m = Image.new("L", (CARD_W, CARD_H), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, CARD_W - 1, CARD_H - 1), r, fill=255)
    return m


def card(src, zoom=1.0, fx=0.5, fy=0.5, box_=MAIN_BOX):
    inner = cover(src, CARD_W, CARD_H, zoom, fx, fy, box_)
    inner.putalpha(card_mask())
    return inner


@lru_cache(None)
def card_shadow():
    return box(CARD_W, CARD_H, 30, (0, 0, 0, 0))


def put_card(c, im, alpha=1.0, dx=0, dy=0, scale=1.0, rot=0.0):
    paste(c, card_shadow(), W / 2 + dx, CARD_Y + dy, scale, rot, alpha * 0.9)
    paste(c, im, W / 2 + dx, CARD_Y + dy, scale, rot, alpha)


def panel(c, color=(36, 30, 26), alpha=1.0):
    paste(c, box(CARD_W, CARD_H, 30, color, shadow=True), W / 2, CARD_Y, 1, 0, alpha)


def shade_card(c, a):
    lay = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
    lay.putalpha(card_mask().point(lambda v: int(v * a)))
    paste(c, lay, W / 2, CARD_Y)


# ------------------------------------------------------------------ 그래픽
@lru_cache(None)
def memo_card():
    w, h = 430, 260
    im = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((34, 40, 30 + w, 36 + h), fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    g = ImageDraw.Draw(im)
    g.rectangle((30, 30, 30 + w, 30 + h), fill=(236, 214, 170))
    for k in range(0, h, 9):
        g.line((30, 30 + k, 30 + w, 30 + k), fill=(228, 204, 158), width=1)
    g.rectangle((30 + w // 2 - 55, 18, 30 + w // 2 + 55, 50), fill=(250, 245, 230, 220))
    t1 = text_img("1986년 짜장면", 40, (120, 60, 30), "Bold", shadow=0)
    t2 = text_img("600원", 104, RED, "Black", shadow=0)
    im.alpha_composite(t1, ((im.width - t1.width) // 2, 62))
    im.alpha_composite(t2, ((im.width - t2.width) // 2, 118))
    return im.rotate(-6, Image.BICUBIC, expand=True)


@lru_cache(None)
def option_chip(no, txt, state=0):
    """state 0=보통, 1=정답 강조, 2=오답 흐림"""
    fill = [(250, 246, 236), YEL, (90, 86, 82)][state]
    fg = [INK, INK, (170, 165, 160)][state]
    b = box(560, 120, 60, fill, INK if state == 1 else None, 6 if state == 1 else 0, True)
    circ = Image.new("RGBA", (84, 84), (0, 0, 0, 0))
    ImageDraw.Draw(circ).ellipse((0, 0, 83, 83), fill=RED if state != 2 else (120, 116, 110))
    n = text_img(no, 50, WHITE, "Black", shadow=0)
    tx = text_img(txt, 64, fg, "Black", shadow=0)
    return compose((b, 0, 0), (circ, -210, 0), (n, -210, -2), (tx, 40, -3))


@lru_cache(None)
def stamp(txt, size=120, color=RED, w=None, h=None, rot=-8):
    t = text_img(txt, size, color, "Black", shadow=0)
    w = w or t.width + 70
    h = h or t.height + 40
    im = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    g.rounded_rectangle((10, 10, 10 + w, 10 + h), 22, outline=color, width=12)
    im.alpha_composite(t, ((im.width - t.width) // 2, (im.height - t.height) // 2 - 4))
    # 도장 잉크 얼룩 (구멍)
    rng = np.random.default_rng(len(txt) * 7 + size)
    a = np.asarray(im.getchannel("A"), dtype=np.float32)
    holes = (rng.random(a.shape) > 0.93).astype(np.float32)
    holes = np.asarray(Image.fromarray((holes * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)),
                       dtype=np.float32) / 255
    im.putalpha(Image.fromarray(np.clip(a * (1 - holes * 1.6), 0, 255).astype(np.uint8)))
    return im.rotate(rot, Image.BICUBIC, expand=True)


@lru_cache(None)
def bowl(d=80):
    S = d * 3
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    c = S / 2
    g.ellipse((c - S * .48, c - S * .30, c + S * .48, c + S * .44), fill=(250, 250, 248), outline=(180, 40, 40), width=S // 30)
    g.ellipse((c - S * .40, c - S * .24, c + S * .40, c + S * .30), fill=(58, 34, 18))
    for k in range(7):
        x = c - S * .30 + k * S * .09
        g.arc((x - S * .08, c - S * .10, x + S * .08, c + S * .14), 200, 340, fill=(236, 206, 140), width=S // 40)
    g.ellipse((c + S * .05, c - S * .14, c + S * .17, c - S * .04), fill=(110, 170, 70))
    return im.resize((d, d), Image.LANCZOS)


@lru_cache(None)
def won_bill(w=150):
    h = int(w * 0.5)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    g.rounded_rectangle((0, 0, w - 1, h - 1), 8, fill=(206, 222, 196), outline=(90, 120, 80), width=3)
    g.ellipse((w * .62, h * .18, w * .9, h * .82), outline=(90, 120, 80), width=3)
    t = text_img("31만", 30, (50, 80, 40), "Black", shadow=0)
    im.alpha_composite(t, (int(w * .08), (h - t.height) // 2))
    return im


@lru_cache(None)
def side_illustration():
    """1세대 그랜저 측면을 단순화한 설명용 그래픽 (실차 사진 아님)."""
    w, h, S = 1000, 600, 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)

    def P(pts):
        return [(x * S, y * S) for x, y in pts]
    g.polygon(P([(40, 380), (60, 300), (230, 285), (330, 190), (650, 185), (770, 280), (950, 292),
                 (965, 380), (930, 420), (70, 420)]), fill=(70, 74, 82), outline=(220, 222, 228))
    g.line(P([(60, 330), (950, 330)]), fill=(225, 228, 235), width=6 * S)
    g.line(P([(50, 400), (955, 400)]), fill=(150, 152, 160), width=10 * S)
    g.polygon(P([(345, 205), (470, 203), (470, 280), (262, 283)]), fill=(150, 175, 200))
    g.polygon(P([(482, 203), (600, 202), (600, 280), (482, 280)]), fill=(150, 175, 200))
    g.polygon(P([(615, 203), (642, 203), (705, 270), (615, 272)]), fill=(255, 214, 120))
    for cx in (215, 790):
        g.ellipse(P([(cx - 70, 350), (cx + 70, 490)]), fill=(28, 28, 30), outline=(190, 190, 196), width=4 * S)
        g.ellipse(P([(cx - 36, 384), (cx + 36, 456)]), fill=(170, 172, 180))
    return im.resize((w, h), Image.LANCZOS)


# ------------------------------------------------------------------ 공통 화면 요소
def key_caption(c, markup, t0, t1, t, y=385, size=88):
    if not (t0 <= t < t1):
        return
    p = out_back(prog(t, t0, 0.22), 2.2)
    q = 1 - prog(t, t1 - 0.12, 0.12)
    im = rich_img(markup, size, 10)
    if im.width > 1010:
        im = im.resize((1010, int(im.height * 1010 / im.width)), Image.BICUBIC)
    paste(c, im, W / 2, y, 0.8 + 0.2 * p, 0, clamp(p * 1.6) * q)


@lru_cache(None)
def series_pill():
    t1 = text_img("그랜저로 보는 대한민국 40년", 34, CREAM, "Bold", shadow=0)
    t2 = text_img("2/8 · 1세대 각그랜저", 34, INK, "Black", shadow=0)
    w = t1.width + t2.width + 40
    b = box(w + 40, 74, 37, (0, 0, 0, 160), shadow=False)
    hi = box(t2.width + 30, 58, 29, AMBER, shadow=False)
    return compose((b, 0, 0), (t1, -(w // 2) + t1.width // 2 + 10, 0),
                   (hi, w // 2 - t2.width // 2 - 5, 0), (t2, w // 2 - t2.width // 2 - 5, 0))


@lru_cache(None)
def credit():
    return text_img("사진: Sim1992 · CC BY-SA 3.0 · Wikimedia Commons (번호판 흐림·크롭·보정)", 23,
                    (225, 225, 225), "SemiBold", shadow=3)


@lru_cache(None)
def source_tag(txt):
    return text_img(txt, 27, (215, 205, 190), "SemiBold", shadow=3)


def subtitle(c, t):
    for i, (st, en) in enumerate(TL["lines"]):
        if LINES[i][2] == "s8":     # 마지막 장면은 화면 문구가 대사와 같아 자막 생략
            continue
        parts = LINES[i][1]
        if not (st - 0.05 <= t < en + 0.2):
            continue
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


def jolt(t, t0, amp=18, dur=0.3):
    """t0 순간 카드가 쿵 흔들리는 오프셋"""
    p = (t - t0) / dur
    if not 0 <= p < 1:
        return 0, 0
    a = amp * (1 - p) ** 2
    return a * math.sin(p * 55), a * math.cos(p * 47) * 0.6


# ------------------------------------------------------------------ 장면
def s1(c, t, t0):
    lt = t - t0
    z = 1.0 + 0.08 * in_out(prog(lt, 0, 3.2))
    put_card(c, card(photo(), z, 0.45, 0.55))
    p = out_back(prog(lt, 0.15, 0.35))
    paste(c, memo_card(), 290, 600, 0.5 + 0.5 * p, 0, clamp(p * 1.5))
    shade_card(c, 0.45 * prog(lt, 0.8, 0.3))
    for k, (no, txt) in enumerate([("1", "169만 원"), ("2", "1,690만 원"), ("3", "1억 원")]):
        pk = out_back(prog(lt, 1.0 + 0.4 * k, 0.3))
        paste(c, option_chip(no, txt), W / 2 + 120, 930 + k * 150, pk, 0, clamp(pk * 1.4))
    key_caption(c, "짜장면 *600원* 시절, 이 차는?", t0 + 0.15, t0 + 9, t, size=84)


def s2(c, t, t0):
    lt = t - t0
    hit = t0 + 0.42
    dx, dy = jolt(t, hit, 22)
    put_card(c, card(photo(), 1.08, 0.45, 0.55), dx=dx, dy=dy)
    shade_card(c, 0.62)
    # 보기 → 2번만 남고 위로
    for k, (no, txt) in enumerate([("1", "169만 원"), ("2", "1,690만 원"), ("3", "1억 원")]):
        if k == 1:
            continue
        paste(c, option_chip(no, txt, 2), W / 2 + 120, 930 + k * 150, 1, 0, 1 - prog(lt, 0, 0.25))
    pr = clamp(lt / 0.42)
    if t < hit:
        val = int(16_900_000 * out_cubic(pr) + (np.random.default_rng(int(t * 60)).integers(0, 9999)))
        txt = f"{val // 10000:,}만 원"
        sc = 1.0
    else:
        txt = "1,690만 원"
        sc = 1.0 + 0.15 * (1 - out_cubic(prog(t, hit, 0.25)))
    num = text_img(txt, 170, YEL if t >= hit else WHITE, "Black", stroke=6, sfill=(0, 0, 0), shadow=10)
    paste(c, num, W / 2 + dx, 860 + dy, sc)
    if t >= hit:
        ps = prog(t, hit + 0.15, 0.18)
        paste(c, stamp("정답", 92), W / 2 + 290, 1080, 2.2 - 1.2 * ps, 0, clamp(ps * 3))
        paste(c, source_tag("1986년 출시 초기 가격 · 오토뷰 보도"), W / 2, 1290, 1, 0, prog(t, hit, 0.3))
    key_caption(c, "정답은 *1,690만 원!*", hit, t0 + 9, t, size=92)


def s3(c, t, t0):
    lt = t - t0
    panel(c, (32, 38, 34))
    # 1986 신입 월급 카드
    p0 = out_back(prog(lt, 0.0, 0.3))
    head = compose((box(760, 110, 26, (250, 246, 236), shadow=False), 0, 0),
                   (text_img("1986 대기업 신입 기본급 월 31만 원", 44, INK, "Black", shadow=0), 0, -3))
    paste(c, head, W / 2, 560, p0, 0, clamp(p0 * 1.4))
    # 54칸 달력 (지폐가 하나씩 채워짐)
    n = int(54 * out_cubic(prog(lt, 0.3, 2.0)))
    cols, dxs, dys = 9, 100, 66
    x0, y0 = W / 2 - (cols - 1) * dxs / 2, 680
    for k in range(54):
        r_, q = divmod(k, cols)
        x, y = x0 + q * dxs, y0 + r_ * dys
        ImageDraw.Draw(c).rounded_rectangle((x - 44, y - 26, x + 44, y + 26), 8, outline=(110, 130, 110), width=2)
        if k < n:
            paste(c, won_bill(), x, y, 0.58)
    cnt = n
    lab = compose((box(620, 140, 30, RED, CREAM, 5, True), 0, 0),
                  (text_img(f"{cnt}개월" if lt < 2.3 else "꼬박 4년 반!", 84, WHITE, "Black", shadow=0), 0, -4))
    ps = out_back(prog(lt, 2.3, 0.25))
    paste(c, lab, W / 2, 1150, 1 + 0.15 * (1 - ps) if lt >= 2.3 else 1, -2, 1)
    paste(c, source_tag("1,690만 원 ÷ 31만 원 ≈ 54.5개월 · 기본급 기준, 한 푼도 안 쓸 때"), W / 2, 1290, 1, 0, prog(lt, 0.6, 0.3))
    key_caption(c, "신입 월급 *4년 반* 치", t0 + 0.1, t0 + 9, t, size=92)


def s4(c, t, t0):
    lt = t - t0
    panel(c, (40, 30, 24))
    # 그릇이 위에서 쏟아져 쌓임
    cols, d = 11, 82
    x0 = W / 2 - (cols - 1) * d / 2
    rng = np.random.default_rng(3)
    delays = rng.random(77) * 1.6
    for k in range(77):
        r_, q = divmod(k, cols)
        ty = 1180 - r_ * 72
        p = out_cubic(prog(lt, delays[k], 0.35))
        if p <= 0:
            continue
        paste(c, bowl(), x0 + q * d + (r_ % 2) * 18, 480 + (ty - 480) * p, 1, (k * 37) % 20 - 10)
    cnt = int(28_000 * out_cubic(prog(lt, 0.0, 1.9)))
    if lt < 2.1:
        lab = compose((box(660, 150, 30, RED, CREAM, 5, True), 0, 0),
                      (text_img(f"약 {cnt:,}그릇", 90, WHITE, "Black", shadow=0), 0, -4))
        paste(c, lab, W / 2, 800, 1, -2, clamp(lt * 4))
    else:
        shade_card(c, 0.55 * prog(lt, 2.1, 0.2))
        ps = prog(lt, 2.15, 0.2)
        paste(c, stamp("매일 1그릇 x 77년", 92, YEL, rot=-5), W / 2, 820, 2.0 - 1.0 * ps, 0, clamp(ps * 3))
    paste(c, source_tag("1,690만 원 ÷ 600원 ≈ 28,167그릇 ÷ 365일 ≈ 77년"), W / 2, 1290, 1, 0, prog(lt, 0.5, 0.3))
    key_caption(c, "짜장면 *2만 8천 그릇* 값", t0 + 0.1, t0 + 9, t, size=88)


def s5(c, t, t0):
    lt = t - t0
    seg = [0, 1.4, 2.5]
    if lt < seg[1]:        # 크롬 라인 팬 + 반사광
        im = card(photo(), 2.3, 0.25 + 0.42 * in_out(clamp(lt / seg[1])), 0.43)
        put_card(c, im)
        sx = -200 + 1500 * prog(lt, 0.3, 0.6)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(lay).polygon([(sx, 480), (sx + 70, 480), (sx - 160, 1330), (sx - 230, 1330)],
                                    fill=(255, 255, 255, 80))
        c.alpha_composite(lay.filter(ImageFilter.GaussianBlur(8)))
    elif lt < seg[2]:      # 후면 램프 각
        put_card(c, card(photo(), 2.4 - 0.15 * prog(lt, seg[1], 1.1), 0.66, 0.60))
    else:                  # 전체 + '각!' 도장 3개
        z = 1.0 + 0.03 * prog(lt, seg[2], 1.6)
        hits = [seg[2] + 0.15, seg[2] + 0.5, seg[2] + 0.85]
        dx, dy = (0, 0)
        for h in hits:
            jx, jy = jolt(lt, h, 14, 0.25)
            dx += jx; dy += jy
        put_card(c, card(photo(), z, 0.5, 0.5), dx=dx, dy=dy)
        for h, (x, y, r) in zip(hits, [(300, 700, -12), (800, 760, 9), (560, 1110, -4)]):
            ps = prog(lt, h, 0.14)
            if ps > 0:
                paste(c, stamp("각!", 96, YEL, rot=r), x + dx, y + dy, 2.0 - 1.0 * ps, 0, clamp(ps * 3))
    paste(c, credit(), W / 2, 1362)
    key_caption(c, "번쩍이는 *크롬*", t0 + 0.1, t0 + seg[1], t)
    key_caption(c, "네모 반듯한 *차체*", t0 + seg[1], t0 + seg[2], t)
    key_caption(c, "별명부터 *‘각그랜저’*", t0 + seg[2], t0 + 9, t, size=96)


def s6(c, t, t0):
    lt = t - t0
    sw = 2.3
    if lt < sw:
        panel(c, (30, 32, 38))
        paste(c, side_illustration(), W / 2, CARD_Y + 10, 0.94, 0, clamp(lt * 5))
        p = out_cubic(prog(lt, 0.5, 0.35))
        cx, cy = W / 2 + 150 * 0.94, CARD_Y + 10 - 62 * 0.94
        if p > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            r = 105 + 8 * math.sin(lt * 10)
            ImageDraw.Draw(lay).arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * p, fill=YEL + (255,), width=10)
            c.alpha_composite(lay)
            paste(c, text_img("오페라 글라스", 48, YEL, "Black", stroke=5, sfill=(0, 0, 0), shadow=3),
                  cx - 40, cy - 165, 1, 0, p)
        paste(c, source_tag("설명용 그래픽 · 실제 차량 사진 아님 · 출처: 현대자동차그룹"), W / 2, CARD_Y + 380, 1, 0, 0.95)
    else:
        fy = 0.14 + 0.10 * in_out(prog(lt, sw, 1.9))
        put_card(c, card(photo(), 2.1, 0.50, fy))
        pk = out_back(prog(lt, sw + 0.3, 0.3))
        tag = compose((box(430, 96, 48, YEL, INK, 5, True), 0, 0),
                      (text_img("여기가 상석", 52, INK, "Black", shadow=0), 0, -3))
        paste(c, tag, W / 2 + 230, 1180, pk, 4, clamp(pk * 1.5))
        paste(c, credit(), W / 2, 1362)
    key_caption(c, "C필러의 작은 창 *오페라 글라스*", t0 + 0.1, t0 + sw, t, size=74)
    key_caption(c, "*뒷자리 손님*을 위한 창", t0 + sw, t0 + 9, t)


def s7(c, t, t0):
    lt = t - t0
    i_next = 7
    t_warm = L(i_next)[0]
    g = clamp((t - t_warm + 0.2) / 0.8)
    z = 1.06 - 0.06 * in_out(prog(lt, 0, 5.5))
    hit = L(6)[1] - 0.62                   # '회장님 차!' 에 맞춰 쾅
    dx, dy = jolt(t, hit, 26)
    a = 1 - prog(t, TL["scenes"][-1][0] - 0.4, 0.4)
    put_card(c, card(photo(round(g * 8) / 8), z, 0.5, 0.5), a, dx, dy)
    if t >= hit:
        ps = prog(t, hit, 0.16)
        fade = 1 - prog(t, t_warm - 0.1, 0.3)
        paste(c, stamp("회장님 차", 130, RED, rot=-9), W / 2 + dx, 900 + dy, 2.4 - 1.4 * ps, 0, clamp(ps * 3) * fade * a)
    if t >= t_warm:
        for k, (x, y) in enumerate([(250, 700), (840, 660), (700, 1130)]):
            pk = out_back(prog(t, t_warm + 0.3 + 0.25 * k, 0.25))
            bub = compose((box(250, 92, 46, (250, 246, 236), INK, 4, True), 0, 0),
                          (text_img(["우와…", "누구 차야?", "회장님?"][k], 44, INK, "Black", shadow=0), 0, -3))
            paste(c, bub, x, y, pk, (-6, 5, -3)[k], clamp(pk * 1.5) * a)
    if a > 0.05:
        paste(c, credit(), W / 2, 1362, 1, 0, a)
    key_caption(c, "그 시절 별명은 단 하나", t0 + 0.1, hit, t, size=84)
    key_caption(c, "*회장님 차!*", hit, t_warm, t, size=110)
    key_caption(c, "동네에서 *다들 돌아보던 차*", t_warm, TL["scenes"][-1][0], t, size=80)


@lru_cache(None)
def morph_box(r):
    s = 300
    im = Image.new("RGBA", (s + 40, s + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((20, 20, 20 + s, 20 + s), r, outline=YEL, width=16)
    return im


def s8(c, t, t0):
    lt = t - t0
    a = clamp(lt / 0.35)
    # 네모(각) -> 둥근 모양으로
    r = int(150 * in_out(prog(lt, 0.9, 1.0)))
    paste(c, morph_box(r // 6 * 6), W / 2, 760, 1, 0, a)
    lab = "각" if r < 75 else "곡선"
    paste(c, text_img(lab, 120 if lab == "각" else 96, YEL, "Black", shadow=4), W / 2, 760, 1, 0, a)
    paste(c, text_img("그 각이 사라집니다", 76, WHITE, "Black", stroke=6, sfill=(0, 0, 0), shadow=4),
          W / 2, 1010, 1, 0, prog(lt, 0.25, 0.3))
    ps = out_back(prog(lt, 2.0, 0.3))
    if lt >= 2.0:
        nb = compose((box(680, 190, 40, AMBER, INK, 6, True), 0, 0),
                     (text_img("다음 편 3/8", 80, INK, "Black", shadow=0), 0, -36),
                     (text_img("2세대 뉴 그랜저", 50, INK, "Bold", shadow=0), 0, 50))
        paste(c, nb, W / 2, 1220, 0.6 + 0.4 * ps, -2, clamp(ps * 1.5))


FN = {"s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5, "s6": s6, "s7": s7, "s8": s8}


def frame(i):
    t = i / FPS
    sc = TL["scenes"]
    k = max(j for j in range(len(sc)) if sc[j][0] <= t)
    t0, name = sc[k]
    last = sc[-1][0]
    if t < last - 0.4:
        c = bg_photo().copy()
    elif t < last:
        c = Image.blend(bg_photo(), bg_dark(), prog(t, last - 0.4, 0.4))
    else:
        c = bg_dark().copy()
    FN[name](c, t, t0)
    if name in ("s1", "s2", "s7") and not (name == "s7" and t > last - 0.4):
        paste(c, credit(), W / 2, 1362)
    paste(c, series_pill(), W / 2, 262)
    subtitle(c, t)
    # 장면 전환 0.1초 흰 플래시
    if k > 0 and t - t0 < 0.1:
        c.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(120 * (1 - (t - t0) / 0.1)))))
    ImageDraw.Draw(c).rectangle((0, 0, int(W * t / TOTAL), 7), fill=AMBER)
    return c.convert("RGB")


# ------------------------------------------------------------------ 오디오
def retro_bgm(total):
    """100BPM 레트로 시티팝 풍 인스트루멘털 (일렉트릭 피아노 + 베이스 + 드럼머신)"""
    sr, bpm = A.SR, 100
    beat = 60 / bpm
    n = int(total * sr) + sr
    Lb, Rb = np.zeros(n), np.zeros(n)

    def add(x, t, gl, gr=None):
        i = int(t * sr)
        if i >= n:
            return
        x = x[: n - i]
        Lb[i:i + len(x)] += x * gl
        Rb[i:i + len(x)] += x * (gl if gr is None else gr)

    def ep(m, sec):
        tt = A._t(sec)
        f = A.note(m)
        x = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt * 6)
             + 0.12 * np.sin(2 * np.pi * 3 * f * tt) * np.exp(-tt * 9))
        return x * np.exp(-tt * 1.6) * (1 + 0.25 * np.sin(2 * np.pi * 5 * tt))

    def bass(m, sec):
        tt = A._t(sec)
        f = A.note(m)
        return (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) * np.exp(-tt * 3.5)

    def snare():
        tt = A._t(0.22)
        nz = A._filt(A.rng.standard_normal(len(tt)), "bandpass", [1200, 5000])
        return (nz * 0.6 + np.sin(2 * np.pi * 190 * tt) * 0.5) * np.exp(-tt * 18)

    def lead(m, sec):
        tt = A._t(sec)
        f = A.note(m) * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * tt))
        x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / sr)) * 0.5 + np.sin(2 * np.pi * np.cumsum(f) / sr)
        return A._filt(x, "lowpass", 2600) * np.minimum(1, tt * 30) * np.exp(-tt * 2.2)

    kk, sn = A.kick() * 0.8, snare()
    prog_ = [(41, [57, 60, 64, 69]), (40, [55, 59, 62, 67]), (38, [53, 57, 60, 65]), (43, [55, 59, 62, 65])]
    melody = [(0, 81), (1, 79), (1.5, 76), (2.5, 77), (4, 79), (5, 76), (5.5, 74), (6.5, 72),
              (8, 74), (9, 76), (9.5, 77), (10.5, 81), (12, 79), (13, 77), (13.5, 76), (14.5, 74)]
    bars = int(total / (beat * 4)) + 2
    for b in range(bars):
        root, ch = prog_[b % 4]
        t0 = b * 4 * beat
        for off in (0, 1.5, 2.5):
            for j, m in enumerate(ch):
                add(ep(m, beat * 1.8), t0 + off * beat + j * 0.012, 0.055, 0.045)
        for off, mm in [(0, 0), (1.5, 0), (2, 12), (3, 7), (3.5, 10)]:
            add(bass(root + mm, beat * 0.9), t0 + off * beat, 0.30)
        for q in range(4):
            tb = t0 + q * beat
            if q in (0, 2):
                add(kk, tb, 0.55)
            if q in (1, 3):
                add(sn, tb, 0.22, 0.26)
            for e in range(2):
                add(A.hat(), tb + e * beat / 2, 0.20 if e else 0.12, 0.14 if e else 0.20)
        if b >= 4:   # 두 번째 반복부터 신스 리드 멜로디
            for off, m in melody:
                if b * 4 <= (b // 4) * 16 + off < b * 4 + 4:
                    add(lead(m, beat * 0.9), (b // 4) * 16 * beat + off * beat, 0.05, 0.06)
    out = np.stack([Lb, Rb], 1)[: int(total * sr)]
    out[:, 0] = A._filt(out[:, 0], "lowpass", 7500)
    out[:, 1] = A._filt(out[:, 1], "lowpass", 7500)
    return out


def calc_sfx():
    """계산기 '탁' + 영수증 '촤르륵' + 벨"""
    sr = A.SR
    clk = A.sfx_click() * 1.2
    rt = A._t(0.35)
    roll = A._filt(A.rng.standard_normal(len(rt)), "bandpass", [2500, 7000])
    roll *= (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 38 * rt))) * np.exp(-rt * 5) * 0.35
    bt = A._t(0.7)
    bell = (np.sin(2 * np.pi * 2093 * bt) + 0.5 * np.sin(2 * np.pi * 3136 * bt)) * np.exp(-bt * 7) * 0.3
    out = np.zeros(int(1.0 * sr))
    out[:len(clk)] += clk
    i = int(0.05 * sr); out[i:i + len(roll)] += roll
    i = int(0.12 * sr); out[i:i + len(bell)] += bell
    return out


def stamp_sfx():
    """도장 '쾅'"""
    t = A._t(0.3)
    thump = np.sin(2 * np.pi * (70 + 90 * np.exp(-t * 30)) * t) * np.exp(-t * 14)
    slap = A._filt(A.rng.standard_normal(len(t)), "bandpass", [300, 2500]) * np.exp(-t * 40) * 0.6
    return thump * 0.9 + slap


def tick_sfx():
    t = A._t(0.04)
    return np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 120) * 0.35


def sfx_events():
    ev = []
    sc = dict((name, st) for st, name in TL["scenes"])
    for st, name in TL["scenes"][1:]:
        ev.append((st - 0.12, A.sfx_whoosh(0.35), 0.45))
    t1 = sc["s1"]
    ev += [(t1 + 0.2, A.sfx_pop(), 0.6)] + [(t1 + 1.0 + 0.4 * k, A.sfx_pop(), 0.7) for k in range(3)]
    hit = sc["s2"] + 0.42
    ev += [(hit - 0.02, calc_sfx(), 1.0), (hit + 0.15, stamp_sfx(), 0.8)]
    s3 = sc["s3"]
    for k in range(0, 54, 3):     # 월급 칸 채우는 틱
        tt = s3 + 0.3 + 2.0 * (1 - (1 - k / 54) ** (1 / 3))
        ev.append((tt, tick_sfx(), 0.7))
    ev += [(s3 + 2.3, A.sfx_ding(), 0.6)]
    s4 = sc["s4"]
    rng = np.random.default_rng(5)
    for k in range(10):
        ev.append((s4 + rng.random() * 1.6, A.sfx_pop(), 0.35))
    ev += [(s4 + 2.15, stamp_sfx(), 0.8)]
    s5 = sc["s5"]
    ev += [(s5 + 0.35, A.sfx_ding(), 0.35)]
    for h in (2.65, 3.0, 3.35):
        ev.append((s5 + h, stamp_sfx(), 0.75))
    s6 = sc["s6"]
    ev += [(s6 + 0.5, A.sfx_pop(), 0.5), (s6 + 2.6, A.sfx_pop(), 0.6)]
    hit7 = L(6)[1] - 0.62
    ev += [(hit7 - 0.02, stamp_sfx(), 1.0), (hit7, A.sfx_impact(), 0.5)]
    for k in range(3):
        ev.append((L(7)[0] + 0.3 + 0.25 * k, A.sfx_pop(), 0.5))
    s8 = sc["s8"]
    ev += [(s8 + 0.9, A.sfx_riser(1.0), 0.35), (s8 + 2.0, A.sfx_ding(), 0.6)]
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
    music = retro_bgm(TOTAL)
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


# ------------------------------------------------------------------ 타임라인
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
        gap = 0.5 if line[2] == "s8" else GAP
        if i:
            t += gap
        TL["lines"].append((round(t, 3), round(t + d, 3)))
        if line[2]:
            TL["scenes"].append((0.0 if i == 0 else round(t - 0.1, 3), line[2]))
        t += d
        paths.append(q)
    assert TL["lines"][-1][1] < TOTAL - 1.6, f"내레이션이 너무 깁니다: {TL['lines'][-1]}"
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
