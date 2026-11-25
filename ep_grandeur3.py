"""그랜저로 보는 대한민국 40년 3/8 · 2세대 뉴 그랜저 (정보형 30초 세로 영상)

유튜브 쇼츠 · 네이버 클립 · 인스타그램 릴스 공용 (1080x1920, 30fps, 정확히 30.0초)
사용법: python3 ep_grandeur3.py                       # output/grandeur40_03_new_grandeur.mp4
        python3 ep_grandeur3.py --preview 1 4 9 13     # 지정 초 프레임 PNG만

실차 사진(선택): assets/images/grandeur_lx.jpg 가 있으면 1·4·7장면에 사진 카드로 사용,
                 없으면 직접 그린 설명용 그래픽만 사용. PHOTO_CREDIT 문구도 함께 고칠 것.

장면
 S1 퀴즈      : 둥근 실루엣 + 3지선다(1,690만/2,490만/3,490만)
 S2 정답      : 숫자 롤링 → 3,490만 원(3.0 골드), '정답' 도장
 S3 비교      : 1986 각그랜저 초기 1,690만 vs 1992 3.0 골드 3,490만 막대 → '2배+' 도장
 S4 곡선·길이 : 네모가 둥글게 → 줄자가 4,980mm까지 → '5m - 2cm' 도장
 S5 블랙 B필러: 측면 그래픽에서 B필러가 까맣게 변하며 창이 이어져 보임
 S6 엠블럼    : 타원형 H 엠블럼이 그려짐
 S7 V6 3.5    : 1994년, 출력 게이지 225마력 + 4,380만 원 육박
 S8 정리·예고 : '회장님 차' 도장 → 시리즈 카드, 다음 편 4/8 그랜저 XG

팩트
 - 1992년 9월 출시, 전장 4,980mm: 현대자동차 브랜드 헤리티지 페이지
 - 출시 가격 3.0 소시알 2,590만 원 / 3.0 3,190만 원 / 3.0 골드 3,490만 원: 한국일보 1992-09-17
 - 각진 선 대신 유선형 곡선, 블랙 B필러로 길게 이어지는 차체: 현대자동차그룹 스토리
 - 타원형 H 엠블럼은 2세대 그랜저부터: 현대자동차그룹 스토리
 - 1994년 6월 V6 3.5(225마력) 추가, 4,380만 원에 육박: 오토뷰
 - 3,490 / 1,690 = 2.07배 (1세대 초기 가격 1,690만 원: 오토뷰)
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
from ep_grandeur2 import (CREAM, AMBER, RED, INK, CARD_W, CARD_H, CARD_Y, option_chip, stamp,
                          key_caption, jolt, panel, card_shadow, card_mask, retro_bgm, calc_sfx,
                          stamp_sfx, tick_sfx)
from video import (W, H, YEL, WHITE, prog, out_cubic, out_back, in_out, clamp,
                   text_img, box, compose, paste, cover)

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build", "grandeur3")
OUT = os.path.join(ROOT, "output")
OUT_NAME = "grandeur40_03_new_grandeur"
PHOTO_PATH = os.path.join(ROOT, "assets", "images", "grandeur_lx.jpg")
PHOTO_CREDIT = "사진: Wikimedia Commons · Category:Hyundai Grandeur (LX) · 파일별 저작자·라이선스는 설명란 (크롭)"
FPS = 30
TOTAL = 30.0
TEMPO = 1.08
GAP = 0.24
NAVY = (26, 34, 52)

LINES = [
    ("각이 사라진 새 그랜저, 얼마였을까요?", ["각이 사라진 새 그랜저,", "얼마였을까요?"], "s1"),
    ("최고급 삼 점 영 골드가 삼천사백구십만 원!", ["최고급 3.0 골드가", "3,490만 원!"], "s2"),
    ("각그랜저 초기 값의 두 배가 넘었죠.", ["각그랜저 초기 값의 두 배가 넘었죠"], "s3"),
    ("직선 대신 둥근 곡선. 길이는 오 미터에서 딱 이 센티 모자랐죠.", ["직선 대신 둥근 곡선,", "길이는 5m에서 딱 2cm 모자랐죠"], "s4"),
    ("까만 B필러로 창을 길게 이어 보이게 했고요.", ["까만 B필러로 창을 길게 이어 보이게 했고요"], "s5"),
    ("지금 익숙한 타원형 H 엠블럼도 이 차부터였습니다.", ["지금 익숙한 타원형 H 엠블럼도", "이 차부터였습니다"], "s6"),
    ("구십사 년엔 V6 삼 점 오까지 등장, 값은 사천사백만 원 가까이!", ["94년엔 V6 3.5까지 등장,", "값은 4,400만 원 가까이!"], "s7"),
    ("더 크고, 더 둥글어진 회장님 차.", ["더 크고, 더 둥글어진 회장님 차"], "s8"),
    ("다음 편, 그랜저 XG.", ["다음 편, 그랜저 XG"], None),
]
TL = {"lines": [], "scenes": []}


def L(i):
    return TL["lines"][i]


def has_photo():
    return os.path.exists(PHOTO_PATH)


MAIN_BOX = (70, 0, 1280, 711)        # 왼쪽 위 다른 차량을 대부분 뺀 영역


@lru_cache(None)
def photo():
    return ImageEnhance.Color(Image.open(PHOTO_PATH).convert("RGB")).enhance(1.06).convert("RGBA")


def cover_box(box_, zoom, fx, fy, w=CARD_W, h=CARD_H):
    """video.cover 와 같은 계산으로, 원본에서 잘라낼 영역(l, t, cw, ch)을 돌려줌"""
    bl, bt, br, bb = box_
    bw, bh = br - bl, bb - bt
    s = max(w / bw, h / bh) * zoom
    cw, ch = w / s, h / s
    l = bl + clamp(fx * bw - cw / 2, 0, bw - cw)
    t = bt + clamp(fy * bh - ch / 2, 0, bh - ch)
    return l, t, cw, ch


def photo_card(zoom=1.0, fx=0.6, fy=0.5, box_=MAIN_BOX):
    inner = cover(photo(), CARD_W, CARD_H, zoom, fx, fy, box_)
    inner.putalpha(card_mask())
    return inner


def src_to_screen(x, y, zoom, fx, fy, box_=MAIN_BOX, dx=0, dy=0):
    l, t, cw, ch = cover_box(box_, zoom, fx, fy)
    return (W / 2 - CARD_W / 2 + (x - l) * CARD_W / cw + dx, CARD_Y - CARD_H / 2 + (y - t) * CARD_H / ch + dy)


def put_photo(c, zoom=1.0, fx=0.6, fy=0.5, box_=MAIN_BOX, dx=0, dy=0, alpha=1.0):
    paste(c, card_shadow(), W / 2 + dx, CARD_Y + dy, 1, 0, 0.9 * alpha)
    paste(c, photo_card(zoom, fx, fy, box_), W / 2 + dx, CARD_Y + dy, 1, 0, alpha)


@lru_cache(None)
def polaroid(name, w=380, rot=0, box_=None):
    im = Image.open(os.path.join(ROOT, "assets", "images", name)).convert("RGBA")
    if name == "grandeur_l_rear_sim1992.jpg":      # 1편과 같은 번호판 흐림
        plate = (338, 618, 535, 760)
        im.paste(im.crop(plate).filter(ImageFilter.GaussianBlur(16)), plate[:2])
    if box_:
        im = im.crop(box_)
    h = int(im.height * w / im.width)
    im = im.resize((w, h), Image.LANCZOS)
    pad, bottom = 14, 40
    fr = Image.new("RGBA", (w + pad * 2, h + pad + bottom), (250, 248, 242, 255))
    fr.alpha_composite(im, (pad, pad))
    sh = Image.new("RGBA", (fr.width + 40, fr.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((24, 28, 24 + fr.width, 28 + fr.height), fill=(0, 0, 0, 140))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    sh.alpha_composite(fr, (20, 20))
    return sh.rotate(rot, Image.BICUBIC, expand=True)


# ------------------------------------------------------------------ 배경
@lru_cache(None)
def bg():
    if has_photo():
        im = cover(photo(), W, H, 1.0, 0.6, 0.5, MAIN_BOX).filter(ImageFilter.GaussianBlur(40))
        return ImageEnhance.Brightness(im).enhance(0.34)
    a = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array((34, 44, 66)) * (1 - a) + np.array((10, 12, 18)) * a) * np.ones((1, W, 1))
    im = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(lay)
    for k in range(-H, W, 90):
        g.line((k, H, k + H * 0.6, 0), fill=(255, 255, 255, 8), width=26)
    im.alpha_composite(lay)
    return im


# ------------------------------------------------------------------ 그래픽
def catmull(pts, n=14, closed=True):
    out = []
    P = pts + pts[:3] if closed else [pts[0]] + pts + [pts[-1]]
    for i in range(len(P) - 3):
        p0, p1, p2, p3 = [np.array(p, dtype=float) for p in P[i:i + 4]]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)))
    return out


@lru_cache(None)
def side_car(bpillar=0.0, color=(178, 182, 190)):
    """2세대 뉴 그랜저 측면을 단순화한 설명용 그래픽 (실차 사진 아님).
    bpillar 0~1: B필러가 차체색 → 검정으로 바뀌며 창이 이어져 보임"""
    w, h, S = 1000, 560, 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)

    def P(pts):
        return [(x * S, y * S) for x, y in pts]
    body = catmull([(26, 372), (44, 318), (130, 292), (290, 276), (392, 196), (500, 178), (640, 182),
                    (752, 250), (900, 270), (972, 306), (978, 372), (930, 404), (70, 404)])
    g.polygon(P(body), fill=color, outline=(235, 238, 244))
    g.line(P(catmull([(40, 342), (500, 336), (965, 344)], closed=False)), fill=(225, 228, 235), width=5 * S)
    glass = catmull([(408, 206), (500, 190), (632, 194), (734, 258), (400, 262)])
    g.polygon(P(glass), fill=(54, 66, 84))
    # 기둥: A·C는 차체색, B필러는 bpillar에 따라 검정으로
    bc = tuple(int(color[i] * (1 - bpillar) + 12 * bpillar) for i in range(3))
    g.polygon(P([(556, 190), (574, 190), (574, 264), (556, 264)]), fill=bc)
    g.line(P([(500, 340), (500, 400)]), fill=(140, 144, 152), width=2 * S)
    g.line(P([(612, 300), (612, 400)]), fill=(140, 144, 152), width=2 * S)
    for cx in (215, 790):
        g.ellipse(P([(cx - 68, 330), (cx + 68, 466)]), fill=(24, 24, 28), outline=(200, 200, 206), width=4 * S)
        g.ellipse(P([(cx - 36, 362), (cx + 36, 434)]), fill=(176, 178, 186))
    return im.resize((w, h), Image.LANCZOS)


def card_or_graphic(c, t, lt, zoom=(1.0, 1.06), dur=4.0, dx=0, dy=0, label=True):
    """사진이 있으면 사진 카드, 없으면 측면 그래픽 패널"""
    if has_photo():
        z = zoom[0] + (zoom[1] - zoom[0]) * in_out(prog(lt, 0, dur))
        paste(c, card_shadow(), W / 2 + dx, CARD_Y + dy, 1, 0, 0.9)
        paste(c, photo_card(z), W / 2 + dx, CARD_Y + dy)
        if PHOTO_CREDIT:
            paste(c, small(PHOTO_CREDIT, 22), W / 2, 1362)
    else:
        panel(c, NAVY)
        sc = 0.92 + 0.04 * in_out(prog(lt, 0, dur))
        paste(c, side_car(), W / 2 + dx, CARD_Y + 30 + dy, sc)
        if label:
            paste(c, small("설명용 그래픽 · 실제 차량 사진 아님"), W / 2, CARD_Y + 380)


@lru_cache(None)
def small(txt, size=27, color=(215, 210, 200)):
    return text_img(txt, size, color, "SemiBold", shadow=3)


@lru_cache(None)
def series_pill():
    t1 = text_img("그랜저로 보는 대한민국 40년", 34, CREAM, "Bold", shadow=0)
    t2 = text_img("3/8 · 2세대 뉴 그랜저", 34, INK, "Black", shadow=0)
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


# ------------------------------------------------------------------ 장면
OPTS = [("1", "1,690만 원"), ("2", "2,490만 원"), ("3", "3,490만 원")]


def credit_line(c, a=1.0):
    if PHOTO_CREDIT:
        paste(c, small(PHOTO_CREDIT, 22, (225, 225, 225)), W / 2, 1362, 1, 0, a)


def ring(c, x, y, r, p, width=10, color=YEL):
    if p <= 0:
        return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).arc((x - r, y - r, x + r, y + r), -90, -90 + 360 * p, fill=color + (255,), width=width)
    c.alpha_composite(lay)


def s1(c, t, t0):
    lt = t - t0
    put_photo(c, 1.0 + 0.08 * in_out(prog(lt, 0, 2.6)), 0.6, 0.5)
    shade_card = G.shade_card
    shade_card(c, 0.42 * prog(lt, 0.6, 0.3))
    pq = out_back(prog(lt, 0.1, 0.35))
    paste(c, text_img("?", 230, YEL, "Black", stroke=8, sfill=(0, 0, 0), shadow=6), 870, 620,
          pq, 8 * math.sin(lt * 6), clamp(pq * 1.5))
    for k, (no, txt) in enumerate(OPTS):
        pk = out_back(prog(lt, 0.7 + 0.35 * k, 0.3))
        paste(c, option_chip(no, txt), W / 2 + 120, 930 + k * 140, pk * 0.92, 0, clamp(pk * 1.4))
    credit_line(c)
    key_caption(c, "각이 사라진 *새 그랜저*, 얼마?", t0 + 0.1, t0 + 9, t, size=84)


def s2(c, t, t0):
    lt = t - t0
    hit = t0 + 0.45
    dx, dy = jolt(t, hit, 22)
    put_photo(c, 1.08, 0.6, 0.5, dx=dx, dy=dy)
    G.shade_card(c, 0.66)
    for k, (no, txt) in enumerate(OPTS[:2]):
        paste(c, option_chip(no, txt, 2), W / 2 + 120, 930 + k * 140, 0.92, 0, 1 - prog(lt, 0, 0.25))
    if t < hit:
        val = int(34_900_000 * out_cubic(clamp(lt / 0.45)) + np.random.default_rng(int(t * 60)).integers(0, 9999))
        txt, sc = f"{val // 10000:,}만 원", 1.0
    else:
        txt, sc = "3,490만 원", 1.0 + 0.15 * (1 - out_cubic(prog(t, hit, 0.25)))
    paste(c, text_img(txt, 170, YEL if t >= hit else WHITE, "Black", stroke=6, sfill=(0, 0, 0), shadow=10),
          W / 2 + dx, 820 + dy, sc)
    if t >= hit:
        paste(c, text_img("1992년 9월 · 3.0 골드", 60, CREAM, "Bold", stroke=4, sfill=(0, 0, 0), shadow=4),
              W / 2, 960, 1, 0, prog(t, hit, 0.3))
        ps = prog(t, hit + 0.15, 0.18)
        paste(c, stamp("정답", 92), W / 2 + 300, 1110, 2.2 - 1.2 * ps, 0, clamp(ps * 3))
        paste(c, small("3.0 소시알 2,590만 원 ~ 3.0 골드 3,490만 원 · 한국일보 1992.9.17 보도", 26, (235, 230, 220)),
              W / 2, 1290, 1, 0, prog(t, hit + 0.3, 0.3))
    credit_line(c)
    key_caption(c, "최고급 *3,490만 원!*", hit, t0 + 9, t, size=92)


def s3(c, t, t0):
    lt = t - t0
    panel(c, (30, 30, 36))
    base, maxh = 1170, 420
    items = [("1986", "각그랜저 초기", 1690, (150, 150, 160), ("grandeur_l_rear_sim1992.jpg", (200, 40, 1282, 840)), -6),
             ("1992", "뉴 그랜저 3.0 골드", 3490, AMBER, ("grandeur_lx.jpg", (300, 0, 1280, 711)), 5)]
    for k, (yr, name, val, col, (img, bx), rot) in enumerate(items):
        x = W / 2 - 210 + k * 420
        hh = maxh * val / 3490 * out_cubic(prog(lt, 0.1 + 0.35 * k, 0.6))
        ImageDraw.Draw(c).rounded_rectangle((x - 105, base - hh, x + 105, base), 18, fill=col)
        pp = out_back(prog(lt, 0.1 + 0.35 * k, 0.35))
        top = base - maxh * val / 3490
        paste(c, polaroid(img, 300, rot, bx), x, top - 120, 0.6 + 0.4 * pp, 0, clamp(pp * 1.5))
        if hh > 5:
            paste(c, text_img(f"{val:,}만", 50, WHITE, "Black", stroke=5, sfill=(0, 0, 0), shadow=3), x, base - hh / 2)
        paste(c, text_img(yr, 44, WHITE, "Black", shadow=0), x, base + 40)
        paste(c, small(name, 30, CREAM), x, base + 86)
    ps = prog(lt, 1.1, 0.16)
    if ps > 0:
        paste(c, stamp("2배+", 110, RED, rot=-10), W / 2, 1010, (2.2 - 1.2 * ps) * 0.8, 0, clamp(ps * 3))
    paste(c, small("1,690만 원: 오토뷰 보도 · 3,490 ÷ 1,690 ≈ 2.07배"), W / 2, 1335, 1, 0, prog(lt, 0.5, 0.3))
    key_caption(c, "각그랜저의 *두 배*가 넘었다", t0 + 0.1, t0 + 9, t, size=88)


@lru_cache(None)
def morph(r):
    s = 180
    im = Image.new("RGBA", (s + 30, s + 30), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((15, 15, 15 + s, 15 + s), r, outline=YEL, width=12)
    return im


def s4(c, t, t0):
    lt = t - t0
    if lt < 1.8:
        # 실차의 둥근 헤드램프·펜더 곡선 클로즈업 + 네모→곡선 아이콘
        z = 2.0 + 0.15 * prog(lt, 0, 1.8)
        put_photo(c, z, 0.55, 0.62)
        r = int(90 * in_out(prog(lt, 0.2, 0.8)))
        badge = compose((box(260, 260, 40, (0, 0, 0, 170), shadow=False), 0, 0), (morph(r // 5 * 5), 0, -18),
                        (text_img("직선" if r < 45 else "곡선", 44, YEL, "Black", shadow=0), 0, 92))
        paste(c, badge, 220, 640, 1, 0, clamp(lt * 4))
        credit_line(c)
    else:
        panel(c, NAVY)
        a2 = prog(lt, 1.8, 0.25)
        paste(c, side_car(), W / 2, 780, 0.92, 0, a2)
        L_ = out_cubic(prog(lt, 1.9, 1.3))
        x0, x1, y = 70, 70 + 940 * L_, 1060
        d = ImageDraw.Draw(c)
        d.rounded_rectangle((x0, y - 34, max(x0 + 10, x1), y + 34), 8, fill=YEL)
        for k in range(int(940 * L_ / 47) + 1):
            xx = x0 + k * 47
            d.line((xx, y - 34, xx, y - (6 if k % 2 else 18)), fill=INK, width=4)
        mm = int(4980 * L_)
        paste(c, text_img(f"{mm:,}mm", 66, INK, "Black", shadow=0), (x0 + x1) / 2, y + 2, 1, 0, clamp(L_ * 3))
        ps = prog(lt, 3.3, 0.16)
        if ps > 0:
            paste(c, stamp("5m - 2cm!", 92, RED, rot=-7), W / 2 + 180, 1200, 2.0 - 1.0 * ps, 0, clamp(ps * 3))
        paste(c, small("전장 4,980mm · 현대자동차 헤리티지 · 측면은 설명용 그래픽"), W / 2, 1335, 1, 0, a2)
    key_caption(c, "직선 대신 *둥근 곡선*", t0 + 0.1, t0 + 1.8, t)
    key_caption(c, "길이 *5m에서 2cm* 모자라", t0 + 1.8, t0 + 9, t)


B_VIEW = dict(zoom=1.0, fx=0.5, fy=0.5, box_=(40, 10, 360, 300))


def s5(c, t, t0):
    lt = t - t0
    z = 1.0 + 0.06 * prog(lt, 0, 2.5)
    v = dict(B_VIEW, zoom=z)
    put_photo(c, **v)
    bx, by = src_to_screen(200, 120, **v)
    p = out_back(prog(lt, 0.3, 0.3))
    if p > 0:
        paste(c, text_img("까만 B필러", 54, YEL, "Black", stroke=5, sfill=(0, 0, 0), shadow=3), bx + 60, by - 240, p, 0, clamp(p * 1.5))
        d = ImageDraw.Draw(c)
        d.line((bx, by - 200, bx, by - 50), fill=YEL, width=9)
        d.polygon([(bx - 20, by - 66), (bx + 20, by - 66), (bx, by - 34)], fill=YEL)
    pl = prog(lt, 1.1, 0.6)
    if pl > 0:   # 앞뒤 창이 하나로 이어져 보이는 화살표
        xa, ya = src_to_screen(105, 225, **v)
        xb, yb = src_to_screen(300, 210, **v)
        d = ImageDraw.Draw(c)
        xe, ye = xa + (xb - xa) * pl, ya + (yb - ya) * pl
        d.line((xa, ya, xe, ye), fill=WHITE, width=10)
        if pl >= 1:
            d.polygon([(xb, yb - 22), (xb, yb + 22), (xb + 36, yb)], fill=WHITE)
        pk = out_back(prog(lt, 1.7, 0.3))
        tag = compose((box(470, 100, 50, (250, 246, 236), INK, 4, True), 0, 0),
                      (text_img("창이 하나처럼 쭉~", 48, INK, "Black", shadow=0), 0, -3))
        paste(c, tag, W / 2 + 120, 1190, pk, -3, clamp(pk * 1.5))
    credit_line(c)
    key_caption(c, "*까만 B필러* = 길어 보이는 창", t0 + 0.1, t0 + 9, t, size=84)


E_VIEW = dict(fx=0.5, fy=0.5, box_=(800, 215, 1100, 470))


def s6(c, t, t0):
    lt = t - t0
    z = 1.0 + 0.10 * in_out(prog(lt, 0, 3.0))
    v = dict(E_VIEW, zoom=z)
    put_photo(c, **v)
    ex, ey = src_to_screen(948, 316, **v)
    ring(c, ex, ey, 120 + 6 * math.sin(lt * 8), out_cubic(prog(lt, 0.3, 0.6)), 12)
    pk = out_back(prog(lt, 1.1, 0.3))
    tag = compose((box(560, 110, 55, YEL, INK, 5, True), 0, 0),
                  (text_img("2세대 그랜저부터!", 56, INK, "Black", shadow=0), 0, -3))
    paste(c, tag, W / 2, 1180, pk, -3, clamp(pk * 1.5))
    paste(c, small("타원형 H 엠블럼 · 현대자동차그룹 스토리", 26, (235, 230, 220)), W / 2, 1290)
    credit_line(c)
    key_caption(c, "타원형 *H 엠블럼*의 시작", t0 + 0.1, t0 + 9, t)


def gauge(c, cx, cy, r, v, vmax=250):
    d = ImageDraw.Draw(c)
    d.arc((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=(70, 74, 86), width=34)
    d.arc((cx - r, cy - r, cx + r, cy + r), 180, 180 + 180 * v / vmax, fill=AMBER, width=34)
    for k in range(0, vmax + 1, 50):
        a = math.radians(180 + 180 * k / vmax)
        d.line((cx + (r - 55) * math.cos(a), cy + (r - 55) * math.sin(a),
                cx + (r - 30) * math.cos(a), cy + (r - 30) * math.sin(a)), fill=WHITE, width=5)
    a = math.radians(180 + 180 * v / vmax)
    d.line((cx, cy, cx + (r - 70) * math.cos(a), cy + (r - 70) * math.sin(a)), fill=RED, width=12)
    d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=WHITE)


def s7(c, t, t0):
    lt = t - t0
    panel(c, (34, 28, 26))
    pp = out_back(prog(lt, 0.05, 0.35))
    paste(c, polaroid("grandeur_lx_black_rear_thumb.jpg", 360, -6), 300, 650, 0.6 + 0.4 * pp, 0, clamp(pp * 1.5))
    paste(c, text_img("1994", 110, CREAM, "Black", shadow=4), 770, 640, 1, 0, clamp(lt * 4))
    v = 225 * out_cubic(prog(lt, 0.3, 1.2)) + (3 * math.sin(lt * 40) if lt > 1.5 else 0)
    gauge(c, W / 2, 1060, 270, v)
    paste(c, text_img(f"V6 3.5 · {int(min(v, 225))}마력", 60, WHITE, "Black", stroke=5, sfill=(0, 0, 0), shadow=3),
          W / 2, 1115)
    ps = out_back(prog(lt, 2.2, 0.3))
    if ps > 0:
        tag = compose((box(640, 130, 30, RED, CREAM, 5, True), 0, 0),
                      (text_img("4,380만 원 육박!", 72, WHITE, "Black", shadow=0), 0, -4))
        paste(c, tag, W / 2, 1230, ps, -2, clamp(ps * 1.5))
    paste(c, small("1994년 6월 V6 3.5(225마력) 추가 · 오토뷰 보도"), W / 2, 1335)
    key_caption(c, "*V6 3.5* 등장", t0 + 0.1, t0 + 9, t, size=96)


def s8(c, t, t0):
    lt = t - t0
    t_next = L(8)[0] - 0.15
    a = 1 - prog(t, t_next - 0.3, 0.3)
    if a > 0:
        hit = t0 + 0.75
        dx, dy = jolt(t, hit, 22)
        put_photo(c, 1.0 + 0.05 * prog(lt, 0, 2.0), 0.6, 0.5, dx=dx, dy=dy, alpha=a)
        for k, (img, x, y, r) in enumerate([("grandeur_lx_black_front_thumb.jpg", 250, 610, -8),
                                            ("grandeur_lx_green_rear_thumb.jpg", 830, 1180, 7)]):
            pk = out_back(prog(lt, 0.2 + 0.2 * k, 0.3))
            paste(c, polaroid(img, 300, r), x, y, 0.6 + 0.4 * pk, 0, clamp(pk * 1.5) * a)
        ps = prog(t, hit, 0.16)
        if ps > 0:
            paste(c, stamp("회장님 차", 130, RED, rot=-9), W / 2 + dx, 900 + dy, 2.4 - 1.4 * ps, 0, clamp(ps * 3) * a)
        credit_line(c, a)
        key_caption(c, "더 크고 더 둥근 *회장님 차*", t0 + 0.1, t_next, t, size=86)
    if t >= t_next - 0.3:
        b = prog(t, t_next - 0.3, 0.3)
        c.alpha_composite(Image.new("RGBA", (W, H), (14, 14, 18, int(235 * b))))
        rows = [("2/8", "1세대 각그랜저  ✓"), ("3/8", "2세대 뉴 그랜저  ✓"), ("4/8", "3세대 그랜저 XG")]
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
                         (text_img("다음 편 4/8", 80, INK, "Black", shadow=0), 0, -36),
                         (text_img("1998 그랜저 XG", 50, INK, "Bold", shadow=0), 0, 50))
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
def whir_sfx(sec=1.2):
    """엔진 회전 상승음"""
    t = A._t(sec)
    f = 60 + 160 * (t / sec) ** 0.7
    ph = 2 * np.pi * np.cumsum(f) / A.SR
    x = (np.sign(np.sin(ph)) * 0.4 + np.sin(2 * ph) * 0.3) * np.minimum(1, t * 8) * np.exp(-np.maximum(0, t - sec * 0.8) * 10)
    return A._filt(x, "lowpass", 1800) * 0.5


def sfx_events():
    ev = []
    sc = dict((name, st) for st, name in TL["scenes"])
    for st, name in TL["scenes"][1:]:
        ev.append((st - 0.12, A.sfx_whoosh(0.35), 0.45))
    t1 = sc["s1"]
    ev += [(t1 + 0.1, A.sfx_pop(), 0.6)] + [(t1 + 0.7 + 0.35 * k, A.sfx_pop(), 0.7) for k in range(3)]
    hit = sc["s2"] + 0.45
    ev += [(hit - 0.02, calc_sfx(), 1.0), (hit + 0.15, stamp_sfx(), 0.8)]
    s3 = sc["s3"]
    ev += [(s3 + 0.1, A.sfx_riser(0.6), 0.25), (s3 + 0.45, A.sfx_riser(0.6), 0.3), (s3 + 1.1, stamp_sfx(), 0.85)]
    s4 = sc["s4"]
    ev += [(s4 + 0.25, A.sfx_whoosh(0.5, False), 0.4)]
    for k in range(0, 20):
        ev.append((s4 + 1.9 + 1.3 * (1 - (1 - k / 20) ** (1 / 3)), tick_sfx(), 0.6))
    ev += [(s4 + 3.3, stamp_sfx(), 0.85)]
    s5 = sc["s5"]
    ev += [(s5 + 0.3, A.sfx_pop(), 0.5), (s5 + 1.3, A.sfx_whoosh(0.5), 0.35)]
    s6 = sc["s6"]
    ev += [(s6 + 0.2, A.sfx_riser(0.8), 0.25), (s6 + 1.0, A.sfx_ding(), 0.6), (s6 + 1.2, A.sfx_pop(), 0.6)]
    s7 = sc["s7"]
    ev += [(s7 + 0.3, whir_sfx(1.3), 0.7), (s7 + 2.2, A.sfx_cash(), 0.6)]
    s8 = sc["s8"]
    ev += [(s8 + 0.73, stamp_sfx(), 1.0), (s8 + 0.75, A.sfx_impact(), 0.5)]
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
    music = retro_bgm(TOTAL + 2.0)[2 * sr: 2 * sr + n]       # 1편과 다른 마디부터 시작
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
