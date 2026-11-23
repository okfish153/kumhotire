"""에피소드 2 – 귀여운 애니메이션 버전 (ep2c)

대본·나레이션 타이밍은 ep2와 동일. 비주얼만 귀엽게:
 - 파스텔 배경 + 흘러가는 구름 + 물방울 도트
 - 오리지널 마스코트 '타이어 친구' (표정 변화, 눈 깜빡임, 스쿼시&스트레치 바운스)
 - 둥근 Jua 폰트, 스티커 스타일 글씨(흰 테두리 + 남색 외곽선), 말풍선/생각풍선
 - 귀여운 BGM(마림바·우쿨렐레) + 만화 효과음(boing, squeak, sparkle)
"""
import math
import random
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import video as V
import ep2
from video import (W, H, prog, out_cubic, out_back, in_out, clamp, load, font, paste, cover,
                   service_tiles, round_mask)

OUT_NAME = "kumho_songwol_shorts_ep2_cute"
LINES = ep2.LINES
CHUNKS = [
    ["타이어 *4개* 바꾸려는데..", "왜 이렇게 *비싸?*"],
    ["싸게 하자니 *불안*하고,", "좋은 걸 하자니 *부담*되고!"],
    ["*잠깐!*", "무조건 *비싼 타이어*가", "*정답*은 아니죠!"],
    ["내 차에 맞는 *규격*부터", "*주행 습관*, *예산*까지", "*확인*하고!"],
    ["*금호타이어*를", "*합리적인 가격*으로!", "*교환*부터 *얼라인먼트*까지!"],
    ["타이어 가격 궁금하세요?", "나주 *금호타이어 송월점!*", "*견적*부터 물어보세요!"],
]
EXTRA = {"cta_top": "타이어 가격 궁금하세요?", "audio_style": "cute"}
VOICE = {"SUPERTONIC_SID": 1, "SUPERTONIC_SPEED": 1.05}   # 밝고 높은 톤의 여성 음성

NAVY = (44, 50, 92)
WHITE = (255, 255, 255)
PINK = (255, 128, 170)
CORAL = (255, 96, 110)
LEMON = (255, 224, 102)
MINT = (110, 214, 180)
SKY = (110, 190, 255)
CREAM = (255, 250, 240)
RED = (235, 30, 45)

THEMES = [((150, 214, 255), (225, 245, 255)),   # S1 하늘
          ((200, 182, 255), (240, 232, 255)),   # S2 라벤더
          ((255, 178, 190), (255, 232, 228)),   # S3 피치핑크
          ((140, 228, 200), (226, 250, 240)),   # S4 민트
          ((255, 222, 120), (255, 246, 214)),   # S5 레몬
          ((160, 205, 255), (255, 220, 235))]   # S6 하늘→핑크


def ck(i, j):
    return V.TL["chunks"][i][j][0]


def ss(i):
    return V.TL["scene_starts"][i]


def elastic(p):
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    return 1 + 2 ** (-10 * p) * math.sin((p * 10 - 0.75) * (2 * math.pi) / 3)


# ------------------------------------------------------------------ 배경
@lru_cache(None)
def pastel_bg(i):
    top, bot = THEMES[i]
    a = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top) * (1 - a) + np.array(bot) * a) * np.ones((1, W, 1))
    return Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")


@lru_cache(None)
def dots():
    per = 120
    im = Image.new("RGBA", (W + per, H + per), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    for y in range(0, H + per, per):
        for x in range(0, W + per, per):
            ox = per / 2 if (y // per) % 2 else 0
            g.ellipse((x + ox - 9, y - 9, x + ox + 9, y + 9), fill=(255, 255, 255, 70))
    return im


@lru_cache(None)
def cloud(w=360):
    h = int(w * 0.5)
    S = 2
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    for (cx, cy, r) in [(.28, .62, .22), (.5, .45, .3), (.72, .6, .22), (.5, .72, .22)]:
        g.ellipse(((cx - r) * w * S, (cy - r * 1.6) * h * S + 0, (cx + r) * w * S, (cy + r * 1.6) * h * S),
                  fill=(255, 255, 255, 235))
    return im.resize((w, h), Image.LANCZOS)


def draw_bg(c, t, i):
    c.alpha_composite(pastel_bg(i))
    d = dots()
    off = int((t * 25) % 120)
    paste(c, d.crop((off, off, off + W, off + H)), W / 2, H / 2)
    for k, (y, sp, sz) in enumerate([(420, 22, 380), (980, 14, 300), (1700, 18, 420), (240, 10, 240)]):
        x = (k * 410 + t * sp) % (W + 500) - 250
        paste(c, cloud(sz), x, y + 10 * math.sin(t * 0.8 + k), 1, 0, 0.75)


# ------------------------------------------------------------------ 스티커 글씨/박스
@lru_cache(None)
def ctext(txt, size, fill=WHITE, s_in=7, s_out=15, shadow=9, outline=NAVY):
    f = font(size, "Jua")
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t_, r, b = d.textbbox((0, 0), txt, font=f, stroke_width=s_out)
    pad = s_out + shadow + 6
    im = Image.new("RGBA", (r - l + pad * 2, b - t_ + pad * 2 + shadow), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    x, y = pad - l, pad - t_
    if shadow:
        g.text((x, y + shadow), txt, font=f, fill=outline, stroke_width=s_out, stroke_fill=outline)
    if s_out:
        g.text((x, y), txt, font=f, fill=outline, stroke_width=s_out, stroke_fill=outline)
    g.text((x, y), txt, font=f, fill=fill, stroke_width=s_in, stroke_fill=WHITE if s_in else fill)
    return im


@lru_cache(None)
def plain(txt, size, fill=NAVY):
    f = font(size, "Jua")
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t_, r, b = d.textbbox((0, 0), txt, font=f)
    im = Image.new("RGBA", (r - l + 8, b - t_ + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - l, 4 - t_), txt, font=f, fill=fill)
    return im


@lru_cache(None)
def cbox(w, h, r, fill=WHITE, ol=NAVY, ow=6, drop=10):
    im = Image.new("RGBA", (w + 4, h + drop + 4), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    if drop:
        g.rounded_rectangle((2, 2 + drop, w + 1, h + 1 + drop), r, fill=ol)
    g.rounded_rectangle((2, 2, w + 1, h + 1), r, fill=fill, outline=ol, width=ow)
    return im


def stack(base, *items):
    """base 위에 (img, dx, dy) 를 중심 기준으로 올린다"""
    out = base.copy()
    for im, dx, dy in items:
        out.alpha_composite(im, (int(out.width / 2 + dx - im.width / 2), int(out.height / 2 + dy - im.height / 2)))
    return out


def sticker(txt, size, fill, txt_col=NAVY, padx=46, h=None):
    t = plain(txt, size, txt_col)
    hh = h or int(size * 1.55)
    return stack(cbox(t.width + padx * 2, hh, hh // 2, fill), (t, 0, -6))


@lru_cache(None)
def star(r=40, color=LEMON):
    S = 4
    im = Image.new("RGBA", (r * 2 * S, r * 2 * S), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    c = r * S
    pts = []
    for k in range(8):
        rr = r * S if k % 2 == 0 else r * S * 0.32
        a = math.pi / 4 * k - math.pi / 2
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    g.polygon(pts, fill=color)
    return im.resize((r * 2, r * 2), Image.LANCZOS)


@lru_cache(None)
def heart(s=60, color=CORAL):
    S = 4
    im = Image.new("RGBA", (s * S, s * S), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    k = s * S
    g.ellipse((0, 0, k * .55, k * .55), fill=color)
    g.ellipse((k * .45, 0, k, k * .55), fill=color)
    g.polygon([(k * .03, k * .38), (k * .97, k * .38), (k / 2, k * .95)], fill=color)
    return im.resize((s, s), Image.LANCZOS)


@lru_cache(None)
def burst_star(w=900, h=330, color=LEMON):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    pts = []
    n = 22
    for k in range(n * 2):
        a = math.pi * k / n
        rx, ry = (w / 2 - 8, h / 2 - 8) if k % 2 == 0 else (w / 2 * 0.8, h / 2 * 0.72)
        pts.append((w / 2 + rx * math.cos(a), h / 2 + ry * math.sin(a)))
    g.polygon(pts, fill=color, outline=NAVY, width=7)
    return im


@lru_cache(None)
def sweat(s=50):
    S = 4
    im = Image.new("RGBA", (s * S, int(s * 1.4) * S), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    k = s * S
    g.ellipse((k * .1, k * .5, k * .9, k * 1.3), fill=(140, 210, 255), outline=NAVY, width=int(k * .07))
    g.polygon([(k * .5, 0), (k * .16, k * .72), (k * .84, k * .72)], fill=(140, 210, 255))
    g.line([(k * .5, k * .02), (k * .14, k * .72)], fill=NAVY, width=int(k * .07))
    g.line([(k * .5, k * .02), (k * .86, k * .72)], fill=NAVY, width=int(k * .07))
    return im.resize((s, int(s * 1.4)), Image.LANCZOS)


# ------------------------------------------------------------------ 마스코트: 타이어 친구
@lru_cache(maxsize=512)
def mascot_img(d, expr="happy", blink=False, lx=0.0, ly=0.0):
    S = 3
    D = d * S
    im = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    c = D / 2
    r = D / 2 * 0.84
    ow = max(2, int(r * 0.055))
    # 몽글몽글한 트레드 돌기
    for k in range(18):
        a = 2 * math.pi * k / 18
        bx, by = c + r * .98 * math.cos(a), c + r * .98 * math.sin(a)
        br = r * .16
        g.ellipse((bx - br, by - br, bx + br, by + br), fill=(64, 64, 76), outline=NAVY, width=ow)
    g.ellipse((c - r, c - r, c + r, c + r), fill=(64, 64, 76), outline=NAVY, width=ow)
    # 휠(얼굴판)
    fr = r * .68
    g.ellipse((c - fr, c - fr, c + fr, c + fr), fill=(236, 240, 248), outline=NAVY, width=ow)
    g.arc((c - fr * .86, c - fr * .86, c + fr * .86, c + fr * .86), 200, 330, fill=WHITE, width=int(ow * 1.4))
    # 볼터치
    for sx in (-1, 1):
        cx, cy = c + sx * fr * .58, c + fr * .28
        g.ellipse((cx - fr * .17, cy - fr * .1, cx + fr * .17, cy + fr * .1), fill=(255, 160, 185))
    # 눈
    ey = c - fr * .12
    for sx in (-1, 1):
        ex = c + sx * fr * .36
        wink = expr == "wink" and sx == 1
        if expr == "happy_closed" or blink or wink:
            g.arc((ex - fr * .17, ey - fr * .12, ex + fr * .17, ey + fr * .16), 200, 340, fill=NAVY, width=int(ow * 1.3))
            continue
        er = fr * (.22 if expr == "shock" else .18)
        g.ellipse((ex - er, ey - er * 1.15, ex + er, ey + er * 1.15), fill=WHITE, outline=NAVY, width=ow)
        pr = er * (.45 if expr == "shock" else .62)
        px, py = ex + lx * er * .35, ey + ly * er * .35 + er * .1
        g.ellipse((px - pr, py - pr, px + pr, py + pr), fill=NAVY)
        hr = pr * .38
        g.ellipse((px - pr * .45 - hr, py - pr * .45 - hr, px - pr * .45 + hr, py - pr * .45 + hr), fill=WHITE)
        if expr == "worry":  # 八 모양 눈썹
            g.line([(ex - sx * er * .9, ey - er * 1.6), (ex + sx * er * .7, ey - er * 2.0)], fill=NAVY,
                   width=int(ow * 1.2))
    # 입
    my = c + fr * .38
    if expr in ("happy", "happy_closed", "wink"):
        g.chord((c - fr * .26, my - fr * .2, c + fr * .26, my + fr * .26), 0, 180, fill=CORAL, outline=NAVY, width=ow)
        g.ellipse((c - fr * .1, my + fr * .06, c + fr * .1, my + fr * .2), fill=(255, 170, 180))
    elif expr == "shock":
        g.ellipse((c - fr * .13, my - fr * .12, c + fr * .13, my + fr * .2), fill=NAVY)
        g.ellipse((c - fr * .07, my + fr * .04, c + fr * .07, my + fr * .17), fill=CORAL)
    elif expr == "worry":
        pts = [(c - fr * .2 + fr * .4 * i / 8, my + fr * .04 * math.sin(i * math.pi / 2)) for i in range(9)]
        g.line(pts, fill=NAVY, width=int(ow * 1.1), joint="curve")
    else:  # smile
        g.arc((c - fr * .18, my - fr * .18, c + fr * .18, my + fr * .1), 20, 160, fill=NAVY, width=int(ow * 1.2))
    return im.resize((d, d), Image.LANCZOS)


def mascot(c, x, y, d, t, expr="happy", look=(0, 0), squash=0.0, rot=0.0, seed=0, alpha=1.0):
    blink = ((t + seed * 0.37) % 3.1) < 0.12 and expr not in ("happy_closed",)
    lx, ly = round(look[0] * 4) / 4, round(look[1] * 4) / 4
    im = mascot_img(d, expr, blink, lx, ly)
    sx, sy = 1 + squash, 1 - squash
    if abs(squash) > 0.01:
        im = im.resize((max(1, int(d * sx)), max(1, int(d * sy))), Image.BICUBIC)
    paste(c, im, x, y + d * (1 - sy) / 2, 1, rot, alpha)


def land_squash(t, t_land, amp=0.28):
    if t < t_land:
        return -0.12  # 낙하 중엔 살짝 길쭉
    dt = t - t_land
    return amp * math.exp(-dt * 7) * math.cos(dt * 22)


# ------------------------------------------------------------------ 폴라로이드
def polaroid(src, w, h, zoom, fx=0.5, fy=0.5, box_=None, tape=True):
    inner = cover(src, w, h, zoom, fx, fy, box_)
    pad, bottom = 22, 70
    card = cbox(w + pad * 2, h + pad + bottom, 18, WHITE, NAVY, 6, 12).copy()
    card.alpha_composite(inner, (2 + pad, 2 + pad))
    if tape:
        for (tx, ang) in [(0.15, -24), (0.85, 22)]:
            tp = Image.new("RGBA", (170, 54), (255, 150, 190, 170))
            ImageDraw.Draw(tp).line([(0, 27), (170, 27)], fill=(255, 255, 255, 90), width=8)
            tp = tp.rotate(ang, Image.BICUBIC, expand=True)
            card.alpha_composite(tp, (int(card.width * tx - tp.width / 2), max(0, int(-tp.height / 2 + 14))))
    return card


# ------------------------------------------------------------------ 장면
def scene1(c, t):
    draw_bg(c, t, 0)
    pt = elastic(prog(t, 0.05, 0.7))
    paste(c, ctext("타이어 4개 교체!", 104, LEMON), 540, 330, pt, -3, clamp(pt * 3))
    t0 = V.TL["line_starts"][0] + 0.1
    k1 = ck(0, 1)
    shock = t >= k1
    for i in range(4):
        st = t0 + 0.16 * i
        p = prog(t, st, 0.4)
        if p <= 0:
            continue
        land = st + 0.4
        y = -150 + (640 + 150) * (p ** 2)
        hop = 0
        if shock:
            q = prog(t, k1 + 0.04 * i, 0.45)
            hop = -110 * math.sin(math.pi * q)
        elif t > land:
            hop = -12 * abs(math.sin((t - land) * 3.2 + i))
        x = 150 + 260 * i
        mascot(c, x, y + hop, 220, t, "shock" if shock else "happy",
               look=(0.6 * math.sin(t * 2 + i), -0.4 if shock else 0.2),
               squash=land_squash(t, land if not shock else k1 + 0.45 + 0.04 * i, 0.25),
               rot=6 * math.sin(t * 3 + i) * (not shock), seed=i)
        if shock:  # 땀방울 튀기
            q = prog(t, k1 + 0.1, 0.7)
            if 0 < q < 1:
                for s_ in (-1, 1):
                    paste(c, sweat(42), x + s_ * (90 + 50 * q), 560 + hop - 60 * math.sin(math.pi * q) + 30 * q,
                          1, -s_ * 25, 1 - q * 0.6)
    # 견적 말풍선
    pb = elastic(prog(t, t0 + 0.55, 0.6))
    if pb > 0:
        if not shock:
            rnd = random.Random(int(t * 15))
            num, col = f"{rnd.randint(100, 999)},{rnd.randint(0, 999):03d}원", NAVY
        else:
            num, col = "???,???원", CORAL
        bub = cbox(820, 230, 60, WHITE, NAVY, 7, 12).copy()
        bub = stack(bub, (plain("견적 금액", 44, PINK), 0, -62), (plain(num, 120, col), 0, 22))
        wob = 4 * math.sin(t * 40) * (1 - prog(t, k1, 0.4)) if shock else 0
        paste(c, bub, 540 + wob, 930, pb, 0, clamp(pb * 2))
    if shock:
        p2 = elastic(prog(t, k1, 0.7))
        paste(c, burst_star(), 540, 1215, p2, 3 * math.sin(t * 6), clamp(p2 * 2))
        paste(c, ctext("왜 이렇게 비싸?!", 112, CORAL), 540, 1205, p2, -3 + 2 * math.sin(t * 7), clamp(p2 * 2))


def scene2(c, t):
    draw_bg(c, t, 1)
    lt = t - ss(1)
    k0, k1 = ck(1, 0), ck(1, 1)
    pt = elastic(prog(lt, 0.0, 0.6))
    paste(c, sticker("고민 고민", 70, LEMON), 540, 300, pt, -2, clamp(pt * 2))
    side = -1 if t < k1 + 0.1 else 1
    tilt = -9 * in_out(prog(t, k0, 0.4)) + 18 * in_out(prog(t, k1, 0.4))
    pm = elastic(prog(lt, 0.05, 0.7))
    bob = 8 * math.sin(lt * 4)
    mascot(c, 540, 900 + bob, 320, t, "worry", look=(side * 0.9 * clamp((t - k0) * 3), -0.6),
           squash=0.03 * math.sin(lt * 8), rot=tilt, seed=3, alpha=clamp(pm * 2))
    # ? 마크
    for k, (dx, ph) in enumerate([(-120, 0), (130, 1.7)]):
        q = elastic(prog(lt, 0.4 + 0.2 * k, 0.6))
        paste(c, ctext("?", 90, SKY, s_in=5, s_out=11, shadow=6), 540 + dx, 690 + 12 * math.sin(lt * 3 + ph),
              q, 15 * math.sin(lt * 2 + ph), clamp(q * 2))
    # 생각 풍선 (왼쪽: 저렴 / 오른쪽: 좋은)
    for (x, st, title, tag, tagcol, exp_) in [(275, k0, "저렴한 타이어?", "불안해..", LEMON, "sweat"),
                                              (805, k1, "좋은 타이어?", "부담돼..", PINK, "heavy")]:
        q = elastic(prog(t, st, 0.7))
        if q <= 0:
            continue
        for j, (ox, oy, rr) in enumerate([(0.0, 0.0, 14), (0.0, 0.0, 22)]):
            fx = 540 + (x - 540) * (0.35 + 0.25 * j)
            fy = 760 - 80 * (j + 1)
            dot = cbox(rr * 2, rr * 2, rr, WHITE, NAVY, 5, 0)
            paste(c, dot, fx, fy, clamp(q), 0, clamp(q * 2))
        bub = stack(cbox(470, 200, 90, WHITE, NAVY, 7, 10), (plain(title, 58, NAVY), 0, -8))
        paste(c, bub, x, 480, q, 0, clamp(q * 2))
        qt = elastic(prog(t, st + 0.45, 0.6))
        paste(c, sticker(tag, 56, tagcol), x, 600, qt, -6 if x < 540 else 6, clamp(qt * 2))
        if exp_ == "sweat" and qt > 0:
            paste(c, sweat(46), x + 170, 560 + 8 * math.sin(t * 6), qt)
        if exp_ == "heavy" and qt > 0:
            paste(c, V.text_img("₩", 64, LEMON, "Black", stroke=7, sfill=NAVY, shadow=0), x + 175, 565 + 8 * math.sin(t * 6), qt)


@lru_cache(None)
def stop_sign(s=430):
    S = 2
    k = s * S
    im = Image.new("RGBA", (k, k + 16 * S), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    pts = [(k / 2 + k * .5 * math.cos(math.pi / 8 + math.pi / 4 * i), k / 2 + k * .5 * math.sin(math.pi / 8 + math.pi / 4 * i))
           for i in range(8)]
    g.polygon([(x, y + 16 * S) for x, y in pts], fill=NAVY)
    g.polygon(pts, fill=NAVY)
    inner = [(k / 2 + k * .46 * math.cos(math.pi / 8 + math.pi / 4 * i), k / 2 + k * .46 * math.sin(math.pi / 8 + math.pi / 4 * i))
             for i in range(8)]
    g.polygon(inner, fill=WHITE)
    inner2 = [(k / 2 + k * .41 * math.cos(math.pi / 8 + math.pi / 4 * i), k / 2 + k * .41 * math.sin(math.pi / 8 + math.pi / 4 * i))
              for i in range(8)]
    g.polygon(inner2, fill=CORAL)
    im = im.resize((s, s + 16), Image.LANCZOS)
    tx = plain("잠깐!", int(s * .3), WHITE)
    im.alpha_composite(tx, ((s - tx.width) // 2, (s - tx.height) // 2 - 6))
    return im


def scene3(c, t):
    draw_bg(c, t, 2)
    lt = t - ss(2)
    k1, k2 = ck(2, 1), ck(2, 2)
    p = elastic(prog(lt, 0.0, 0.7))
    paste(c, stop_sign(), 470, 560, p, -8 + 4 * math.sin(lt * 5) * clamp(lt), clamp(p * 2))
    for k in range(5):  # 반짝이
        a = k * 1.3 + lt * 0.8
        tw = 0.6 + 0.4 * math.sin(lt * 6 + k)
        paste(c, star(26 + 6 * (k % 2), WHITE), 470 + 300 * math.cos(a), 560 + 260 * math.sin(a), tw * clamp(p),
              0, clamp(p))
    no = t >= k2
    pm = elastic(prog(lt, 0.25, 0.7))
    shake_head = 14 * math.sin((t - k2) * 18) * math.exp(-(t - k2) * 2) if no else 0
    mascot(c, 850, 760, 230, t, "wink" if no else "shock", look=(-0.8, -0.3),
           squash=0.04 * math.sin(lt * 7), rot=shake_head, seed=5, alpha=clamp(pm * 2))
    pc = elastic(prog(t, k1 - 0.05, 0.7))
    card = stack(cbox(920, 280, 50, WHITE, NAVY, 7, 12),
                 (plain("무조건 비싼 타이어", 84, NAVY), 0, -52), (plain("= 정답?", 84, PINK), 0, 58))
    paste(c, card, 540, 1080, pc, 2, clamp(pc * 2))
    if no:
        q = out_cubic(prog(t, k2, 0.4))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        g = ImageDraw.Draw(layer)
        cx, cy, h = 540, 1080, 120
        p1, p2 = clamp(q * 2), clamp(q * 2 - 1)
        for (x0, y0, x1, y1, pp) in [(cx - h * 1.6, cy - h, cx + h * 1.6, cy + h, p1),
                                     (cx + h * 1.6, cy - h, cx - h * 1.6, cy + h, p2)]:
            if pp > 0:
                ex, ey = x0 + (x1 - x0) * pp, y0 + (y1 - y0) * pp
                g.line([(x0, y0), (ex, ey)], fill=CORAL, width=34)
                for (px, py) in [(x0, y0), (ex, ey)]:
                    g.ellipse((px - 17, py - 17, px + 17, py + 17), fill=CORAL)
        c.alpha_composite(layer)
        pn = elastic(prog(t, k2 + 0.3, 0.6))
        paste(c, sticker("NO!", 62, MINT), 860, 935, pn, 10, clamp(pn * 2))


def scene4(c, t):
    draw_bg(c, t, 3)
    lt = t - ss(3)
    k0, k1, k2 = ck(3, 0), ck(3, 1), ck(3, 2)
    pt = elastic(prog(lt, 0.0, 0.6))
    paste(c, sticker("맞춤 상담", 70, WHITE), 540, 300, pt, -2, clamp(pt * 2))
    pp = elastic(prog(lt, 0.1, 0.7))
    pol = polaroid(load("poster_square.png"), 820, 340, 1.0 + 0.2 * prog(lt, 0, 5), 0.45, 0.75, (40, 330, 1214, 830))
    paste(c, pol, 540, 620, pp, -2.5, clamp(pp * 2))
    # 돋보기 든 타이어 친구
    sx = 540 + 300 * math.sin(lt * 1.6)
    mascot(c, 905, 905, 170, t, "happy", look=(-0.7, -0.6), squash=0.04 * math.sin(lt * 9), seed=7,
           alpha=clamp(pp * 2))
    if pp > 0.5:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        g = ImageDraw.Draw(layer)
        mx, my = sx, 620 + 40 * math.sin(lt * 2.3)
        g.line([(mx + 55, my + 55), (mx + 120, my + 120)], fill=NAVY, width=22)
        g.ellipse((mx - 75, my - 75, mx + 75, my + 75), fill=(200, 235, 255, 90), outline=NAVY, width=12)
        g.arc((mx - 50, my - 50, mx + 50, my + 50), 200, 260, fill=WHITE, width=8)
        c.alpha_composite(layer)
    times = [k0 + 0.6 * (k1 - k0), k1 + 0.05, k1 + 0.55 * (k2 - k1)]
    rows = [("1", "타이어 규격", PINK), ("2", "주행 습관", LEMON), ("3", "예산 확인", SKY)]
    for i, (tt, (num, lab, col)) in enumerate(zip(times, rows)):
        q = elastic(prog(t, tt, 0.6))
        if q <= 0:
            continue
        y = 975 + i * 135
        nb = stack(cbox(84, 84, 42, col, NAVY, 5, 0), (plain(num, 52, NAVY), 0, -3))
        row = stack(cbox(820, 112, 56, WHITE, NAVY, 6, 9), (nb, -330, -4), (plain(lab, 62, NAVY), -40, -6))
        paste(c, row, 540, y, q, (-1) ** i * 1.5, clamp(q * 2))
        qc = elastic(prog(t, tt + 0.3, 0.5))
        if qc > 0:
            paste(c, heart(70, CORAL), 860, y - 6, qc, 0, clamp(qc * 2))
    pk = elastic(prog(t, k2, 0.6))
    paste(c, sticker("꼼꼼하게 확인!", 60, LEMON), 760, 790, pk, -8, clamp(pk * 2))


def scene5(c, t):
    draw_bg(c, t, 4)
    lt = t - ss(4)
    k1, k2 = ck(4, 1), ck(4, 2)
    pt = elastic(prog(lt, 0.0, 0.6))
    paste(c, ctext("금호타이어", 120, RED), 540, 310, pt, -3, clamp(pt * 2))
    shrink = in_out(prog(t, k2 - 0.1, 0.45))
    pp = elastic(prog(lt, 0.15, 0.8))
    pol = polaroid(load("poster_store.png"), 560, 700, 1.0 + 0.06 * prog(lt, 0, 5), 0.5, 0.45)
    paste(c, pol, 540, 820 - 190 * shrink, pp * (1 - 0.4 * shrink), 3, clamp(pp * 2))
    for k in range(6):  # 반짝이
        a = k * 1.05 + lt * 0.6
        tw = 0.5 + 0.5 * math.sin(lt * 5 + k * 1.7)
        paste(c, star(30, WHITE if k % 2 else LEMON), 540 + 380 * math.cos(a), 820 - 190 * shrink + 420 * math.sin(a) * (1 - 0.4 * shrink),
              tw * clamp(pp), 0, clamp(pp))
    pb = elastic(prog(t, k1, 0.6))
    if pb > 0:
        by = 1265 - 470 * shrink
        paste(c, sticker("합리적인 가격", 66, CORAL, WHITE), 540, by, pb, -3, clamp(pb * 2))
        paste(c, heart(64, PINK), 540 + 260, by - 40 + 6 * math.sin(t * 5), pb, 12, clamp(pb * 2))
        for k in range(6):  # 동전 퐁퐁
            q = prog(t, k1 + 0.05 * k, 0.9)
            if 0 < q < 1:
                ang = -math.pi / 2 + (k - 2.5) * 0.35
                cx = 540 + math.cos(ang) * 320 * q
                cy = by + math.sin(ang) * 300 * q + 380 * q * q
                coin = stack(cbox(70, 70, 35, LEMON, NAVY, 5, 0), (V.text_img("₩", 40, NAVY, "Black", shadow=0), 0, 0))
                paste(c, coin, cx, cy, 1, 200 * q, 1 - q ** 3)
    tiles = service_tiles()
    for i, (tile, x) in enumerate([(tiles[0], 290), (tiles[1], 790)]):
        q = elastic(prog(t, k2 + 0.15 + 0.3 * i, 0.6))
        paste(c, tile, x, 1160 + 6 * math.sin(t * 4 + i), 0.86 * q, (-4, 4)[i], clamp(q * 2))
    qa = elastic(prog(t, k2 + 0.4, 0.5))
    arrow = Image.new("RGBA", (110, 100), (0, 0, 0, 0))
    ImageDraw.Draw(arrow).polygon([(8, 32), (56, 32), (56, 8), (102, 50), (56, 92), (56, 68), (8, 68)],
                                  fill=PINK, outline=NAVY, width=6)
    paste(c, arrow, 540, 1150, qa, 0, clamp(qa * 2))


def scene6(c, t):
    draw_bg(c, t, 5)
    lt = t - ss(5)
    k1, k2 = ck(5, 1), ck(5, 2)
    p0 = elastic(prog(lt, 0.0, 0.6))
    paste(c, ctext("타이어 가격 궁금하세요?", 76, WHITE, s_in=0), 540, 300, p0, -2, clamp(p0 * 2))
    # 이름 나오기 전: 가운데 큰 타이어 친구가 '궁금' 표정
    pin_ = elastic(prog(lt, 0.1, 0.7))
    pout = in_out(prog(t, k1 - 0.15, 0.3))
    if pout < 1:
        mascot(c, 540, 880 + 10 * math.sin(lt * 4), 340, t, "smile", look=(0.3 * math.sin(lt * 2), -0.8),
               squash=0.04 * math.sin(lt * 8), rot=8 * math.sin(lt * 2.2), seed=11,
               alpha=clamp(pin_ * 2) * (1 - pout))
        for k, (dx, dy) in enumerate([(-190, -180), (200, -150)]):
            q = elastic(prog(lt, 0.4 + 0.25 * k, 0.6)) * (1 - pout)
            paste(c, ctext("?", 100, SKY, s_in=5, s_out=11, shadow=6), 540 + dx, 880 + dy + 12 * math.sin(lt * 3 + k),
                  q, 15 * math.sin(lt * 2 + k), clamp(q * 2))
    p1 = elastic(prog(t, k1, 0.7))
    name = stack(cbox(940, 210, 70, RED, NAVY, 7, 12), (plain("금호타이어 송월점", 104, WHITE), 0, -6))
    paste(c, name, 540, 500, p1, 0, clamp(p1 * 2))
    pt = elastic(prog(t, k1 + 0.15, 0.5))
    paste(c, sticker("나주", 48, LEMON), 165, 392, pt, -10, clamp(pt * 2))
    pm = elastic(prog(t, k1 + 0.3, 0.6))
    mascot(c, 940, 380, 150, t, "wink", look=(-0.6, 0.2), squash=0.06 * math.sin(lt * 9), rot=10 * math.sin(lt * 3),
           seed=9, alpha=clamp(pm * 2))
    pp = elastic(prog(t, k1 + 0.45, 0.6))
    if pp > 0:
        since = max(0, t - (k1 + 0.9))
        pul = 1 + 0.04 * math.sin(since * 7)
        ph = stack(cbox(110, 110, 55, PINK, NAVY, 6, 0), (V.phone_icon(80), 0, 0))
        btn = stack(cbox(900, 170, 85, WHITE, NAVY, 7, 12), (ph, -355, -5), (plain("061-335-6114", 96, NAVY), 60, -10))
        paste(c, btn, 540, 760, pp * pul, 0, clamp(pp * 2))
        pg = elastic(prog(t, k1 + 0.75, 0.5))
        paste(c, sticker("견적 문의", 44, LEMON), 850, 665, pg, 6, clamp(pg * 2))
    pa = out_cubic(prog(t, k1 + 0.8, 0.35))
    addr = stack(cbox(760, 86, 43, CREAM, NAVY, 5, 0), (V.pin_icon(44), -320, -2),
                 (plain("전남 나주시 예향로 4101", 50, NAVY), 30, -4))
    paste(c, addr, 540, 920, 1, 0, pa)
    pq = elastic(prog(t, k2 - 0.3, 0.7))
    if pq > 0:
        qr = load("qr_review.png").resize((250, 250), Image.NEAREST)
        pol = cbox(290, 330, 18, WHITE, NAVY, 6, 12).copy()
        pol.alpha_composite(qr, (22, 22))
        pol = stack(pol, (plain("네이버 리뷰", 34, PINK), 0, 140))
        paste(c, pol, 300, 1185, pq, -4, clamp(pq * 2))
        pl = elastic(prog(t, k2 - 0.1, 0.6))
        paste(c, ctext("리뷰도 부탁해요!", 60, PINK, s_in=4, s_out=11, shadow=6), 700, 1120, pl, 3, clamp(pl * 2))
        paste(c, plain("QR 스캔 후 리뷰 작성", 42, NAVY), 700, 1205, 1, 0, clamp(pl))
        paste(c, heart(56, CORAL), 860, 1270 + 6 * math.sin(t * 5), pl, -10, clamp(pl * 2))


# ------------------------------------------------------------------ 자막(귀여운 말풍선)
@lru_cache(None)
def cute_sub_img(markup):
    segs = V.parse_markup(markup)
    f = font(70, "Jua")
    total = sum(f.getlength(s) for s, _ in segs)
    asc, desc = f.getmetrics()
    w, h = int(total) + 90, asc + desc + 44
    base = cbox(w, h, h // 2, WHITE, NAVY, 6, 9).copy()
    g = ImageDraw.Draw(base)
    x = 45
    for s, col in segs:
        g.text((x, 22 + asc), s, font=f, anchor="ls", fill=CORAL if col != V.WHITE else NAVY)
        x += f.getlength(s)
    if base.width > 1020:
        base = base.resize((1020, int(base.height * 1020 / base.width)), Image.BICUBIC)
    return base


def cute_subtitle(c, t):
    for ch in V.TL["chunks"]:
        for (st, en, txt) in ch:
            if st <= t < en:
                p = elastic(prog(t, st, 0.45))
                paste(c, cute_sub_img(txt), 540, 1470, 0.75 + 0.25 * p, 0, clamp(p * 3))
                return


SCENES = [scene1, scene2, scene3, scene4, scene5, scene6]
V.EPISODES["ep2c"] = SCENES
V.EP_OPTS["ep2c"] = {"subtitle": cute_subtitle, "vignette": False}


def shakes(chunks, scene_starts):
    return [(chunks[0][1][0], 0.5), (scene_starts[2], 0.4)]


def sfx_events(tl):
    c, s = tl["chunks"], tl["scene_starts"]
    t0 = tl["line_starts"][0] + 0.1
    ev = [(0.05, "sparkle", 0.6, 0)]
    for i in range(4):
        ev.append((t0 + 0.16 * i + 0.4, "boing", 0.55, (-0.6, -0.2, 0.2, 0.6)[i]))
    tt = t0 + 0.6
    while tt < c[0][1][0] - 0.05:
        ev.append((tt, "click", 0.3, 0)); tt += 0.1
    ev += [(c[0][1][0] - 0.02, "shock", 0.8, 0), (c[0][1][0] + 0.15, "squeak", 0.5, 0.3),
           (s[1] - 0.2, "whoosh", 0.5, 0), (s[1] + 0.05, "boing", 0.5, 0),
           (c[1][0][0], "pop", 0.7, -0.5), (c[1][0][0] + 0.45, "squeak", 0.5, -0.5),
           (c[1][1][0], "pop", 0.7, 0.5), (c[1][1][0] + 0.45, "squeak", 0.5, 0.5),
           (s[2] - 0.2, "whoosh", 0.6, 0), (s[2], "boing", 0.8, 0), (s[2] + 0.1, "sparkle", 0.6, 0),
           (c[2][1][0] - 0.05, "pop", 0.8, 0),
           (c[2][2][0], "whoosh_down", 0.5, 0), (c[2][2][0] + 0.2, "whoosh_down", 0.5, 0),
           (c[2][2][0] + 0.3, "boing", 0.6, 0.4),
           (s[3] - 0.2, "whoosh", 0.6, 0), (s[3] + 0.1, "pop", 0.7, 0)]
    k0, k1, k2 = c[3][0][0], c[3][1][0], c[3][2][0]
    for tt in (k0 + 0.6 * (k1 - k0), k1 + 0.05, k1 + 0.55 * (k2 - k1)):
        ev += [(tt, "pop", 0.7, 0), (tt + 0.3, "squeak", 0.45, 0.4)]
    ev += [(k2, "sparkle", 0.7, 0),
           (s[4] - 0.2, "whoosh", 0.6, 0), (s[4] + 0.05, "boing", 0.7, 0), (s[4] + 0.2, "sparkle", 0.5, 0),
           (c[4][1][0], "cash", 0.7, 0), (c[4][1][0] + 0.1, "sparkle", 0.6, 0),
           (c[4][2][0] + 0.15, "pop", 0.7, -0.4), (c[4][2][0] + 0.45, "pop", 0.7, 0.4),
           (s[5] - 0.2, "whoosh", 0.6, 0), (c[5][1][0], "boing", 0.8, 0), (c[5][1][0] + 0.3, "squeak", 0.5, 0.5),
           (c[5][1][0] + 0.45, "pop", 0.7, 0), (c[5][2][0] - 0.3, "pop", 0.7, -0.3),
           (c[5][2][0] - 0.1, "sparkle", 0.6, 0.3), (tl["total"] - 1.6, "ding", 0.5, 0)]
    return ev
