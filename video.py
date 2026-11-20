"""1080x1920 세로 숏폼 영상 프레임 렌더러 (PIL 모션그래픽).

장면 구성 (대본 6단락과 1:1 매칭)
 S1 후킹      : 실제 매장 거리 사진 + '가격만 보세요?' 키네틱 타이포 + 흔들리는 가격표
 S2 문제 제기 : '잠깐!' 스탬프 + 가격 vs 내 차에 맞는 선택 비교 카드
 S3 전문성    : 매장 사진 카드 + 스캔 레이저 HUD + 3단 체크리스트
 S4 해결책    : '금호타이어 전문점' 리본 + 매장 포스터 → 렌탈 포스터 스와이프
 S5 신뢰      : 포스터의 서비스 아이콘 4종 타일 + ONE STOP 배지
 S6 CTA       : 매장명/전화번호 버튼/주소/네이버 리뷰 QR
"""
import math
import os
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
ROOT = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(ROOT, "assets", "images")
FNT = os.path.join(ROOT, "assets", "fonts")

RED = (230, 0, 18)
DRED = (150, 0, 12)
YEL = (255, 212, 0)
WHITE = (255, 255, 255)
DARK = (16, 16, 20)
INK = (25, 25, 30)

TL = None  # timeline (render() 에서 주입)


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur) if dur > 0 else float(t >= start)


def out_cubic(p):
    return 1 - (1 - p) ** 3


def out_back(p, s=1.9):
    p -= 1
    return 1 + (s + 1) * p ** 3 + s * p ** 2


def in_out(p):
    return 3 * p * p - 2 * p ** 3


# ------------------------------------------------------------------ assets
@lru_cache(None)
def font(size, weight="Black"):
    return ImageFont.truetype(os.path.join(FNT, f"Pretendard-{weight}.ttf"), size)


@lru_cache(None)
def load(name):
    return Image.open(os.path.join(IMG, name)).convert("RGBA")


@lru_cache(None)
def blurred(name, r):
    return load(name).filter(ImageFilter.GaussianBlur(r))


@lru_cache(None)
def text_img(txt, size, fill=WHITE, weight="Black", stroke=0, sfill=(0, 0, 0), shadow=8):
    f = font(size, weight)
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), txt, font=f, stroke_width=stroke)
    pad = stroke + shadow * 3 + 6
    im = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + shadow // 2, pad - t + shadow), txt, font=f,
                                fill=(0, 0, 0, 170), stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(shadow)))
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, font=f, fill=fill,
                            stroke_width=stroke, stroke_fill=sfill)
    return im


def parse_markup(s):
    """'*강조*' 구간은 노란색"""
    segs, hi = [], False
    for i, part in enumerate(s.split("*")):
        if part:
            segs.append((part, YEL if hi else WHITE))
        hi = not hi
    return tuple(segs)


@lru_cache(None)
def rich_img(markup, size, stroke=9, weight="Black"):
    segs = parse_markup(markup)
    f = font(size, weight)
    total = sum(f.getlength(s) for s, _ in segs)
    asc, desc = f.getmetrics()
    pad = stroke + 24
    im = Image.new("RGBA", (int(total) + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    x = pad
    for s, c in segs:
        ImageDraw.Draw(sh).text((x + 3, pad + asc + 8), s, font=f, anchor="ls", fill=(0, 0, 0, 200),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 200))
        x += f.getlength(s)
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(7)))
    d = ImageDraw.Draw(im)
    x = pad
    for s, c in segs:
        d.text((x, pad + asc), s, font=f, anchor="ls", fill=c, stroke_width=stroke, stroke_fill=(0, 0, 0))
        x += f.getlength(s)
    return im


@lru_cache(None)
def round_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    return m


@lru_cache(None)
def shadow_for(w, h, r, blur=22, alpha=150):
    pad = blur * 3
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((pad, pad + 14, pad + w, pad + h + 14), r, fill=(0, 0, 0, alpha))
    return im.filter(ImageFilter.GaussianBlur(blur))


@lru_cache(None)
def box(w, h, r, fill, outline=None, ow=0, shadow=True):
    pad = 70 if shadow else 0
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = shadow_for(w, h, r)
        im.alpha_composite(sh, ((im.width - sh.width) // 2, (im.height - sh.height) // 2))
    ImageDraw.Draw(im).rounded_rectangle((pad, pad, pad + w - 1, pad + h - 1), r, fill=fill,
                                         outline=outline, width=ow)
    return im


def compose(*layers):
    """여러 RGBA 이미지를 중심 정렬로 합성. layers: (img, dx, dy)"""
    w = max(abs(dx) * 2 + im.width for im, dx, dy in layers)
    h = max(abs(dy) * 2 + im.height for im, dx, dy in layers)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for im, dx, dy in layers:
        out.alpha_composite(im, (w // 2 + dx - im.width // 2, h // 2 + dy - im.height // 2))
    return out


# ------------------------------------------------------------------ drawing
def paste(canvas, img, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    im = img
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if abs(rot) > 0.05:
        im = im.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = np.asarray(im.getchannel("A"), dtype=np.float32) * alpha
        im = im.copy()
        im.putalpha(Image.fromarray(a.astype(np.uint8)))
    x, y = int(round(cx - im.width / 2)), int(round(cy - im.height / 2))
    sx, sy = max(0, -x), max(0, -y)
    ex, ey = min(im.width, canvas.width - x), min(im.height, canvas.height - y)
    if ex <= sx or ey <= sy:
        return
    if (sx, sy, ex, ey) != (0, 0, im.width, im.height):
        im = im.crop((sx, sy, ex, ey))
    canvas.alpha_composite(im, (x + sx, y + sy))


def cover(src, w, h, zoom=1.0, fx=0.5, fy=0.5, box_=None):
    """Ken Burns용 cover-fit 크롭. box_ = 원본에서 사용할 영역"""
    if box_ is None:
        box_ = (0, 0, src.width, src.height)
    bl, bt, br, bb = box_
    bw, bh = br - bl, bb - bt
    s = max(w / bw, h / bh) * zoom
    cw, ch = w / s, h / s
    l = bl + clamp(fx * bw - cw / 2, 0, bw - cw)
    t = bt + clamp(fy * bh - ch / 2, 0, bh - ch)
    return src.resize((w, h), Image.BILINEAR, box=(l, t, l + cw, t + ch))


def photo_card(src, w, h, zoom, fx=0.5, fy=0.5, box_=None, r=34, border=8):
    inner = cover(src, w, h, zoom, fx, fy, box_)
    inner.putalpha(round_mask(w, h, r))
    base = box(w + border * 2, h + border * 2, r + border, WHITE)
    base = base.copy()
    base.alpha_composite(inner, ((base.width - w) // 2, (base.height - h) // 2))
    return base


@lru_cache(None)
def dark_grad(top=(28, 28, 34), bottom=(8, 8, 10)):
    a = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top) * (1 - a) + np.array(bottom) * a) * np.ones((1, W, 1))
    im = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
    return im


@lru_cache(None)
def stripes():
    per = 90
    im = Image.new("RGBA", (W + 2 * H, H + per * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for x in range(-H, W + 2 * H, per):
        d.polygon([(x, 0), (x + 30, 0), (x + 30 - H - per * 2, H + per * 2), (x - H - per * 2, H + per * 2)],
                  fill=(255, 255, 255, 9))
    return im


def draw_stripes(c, t):
    s = stripes()
    off = int((t * 60) % 90)
    paste(c, s.crop((off, 0, off + W, H)), W / 2, H / 2)


@lru_cache(None)
def vignette():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W * 0.75)) ** 2 + ((y - H / 2) / (H * 0.7)) ** 2)
    a = (np.clip(d - 0.45, 0, 1) ** 1.4 * 330).clip(0, 210).astype(np.uint8)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    im.putalpha(Image.fromarray(a))
    return im


@lru_cache(None)
def bottom_glow(color=RED, h=900, a=170):
    arr = np.zeros((h, W, 4), np.uint8)
    arr[..., :3] = color
    arr[..., 3] = (np.linspace(0, 1, h) ** 2 * a).astype(np.uint8)[:, None]
    return Image.fromarray(arr, "RGBA")


@lru_cache(None)
def overlay(alpha, color=(0, 0, 0)):
    return Image.new("RGBA", (W, H), color + (alpha,))


@lru_cache(None)
def burst(size=1500, n=18, color=RED, alpha=95):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = a0 + math.pi / n
        d.polygon([(c, c), (c + size * math.cos(a0), c + size * math.sin(a0)),
                   (c + size * math.cos(a1), c + size * math.sin(a1))], fill=color + (alpha,))
    m = Image.new("L", (size, size), 0)
    y, x = np.mgrid[0:size, 0:size]
    rr = np.sqrt((x - c) ** 2 + (y - c) ** 2) / c
    m = Image.fromarray((np.clip(1 - rr, 0, 1) ** 0.8 * 255).astype(np.uint8))
    a = np.asarray(im.getchannel("A"), np.float32) * np.asarray(m, np.float32) / 255
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im


@lru_cache(None)
def brand_pill():
    a = text_img("KUMHO TIRE", 40, WHITE, "Black", shadow=0)
    b = text_img("송월점", 36, WHITE, "ExtraBold", shadow=0)
    w = a.width + b.width + 70
    im = Image.new("RGBA", (w, 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, 79), 40, fill=(0, 0, 0, 150))
    d.rounded_rectangle((a.width + 18, 10, w - 10, 69), 30, fill=RED)
    im.alpha_composite(a, (18, (80 - a.height) // 2))
    im.alpha_composite(b, (a.width + 18 + (w - 10 - a.width - 18 - b.width) // 2, (80 - b.height) // 2))
    return im


@lru_cache(None)
def price_tag():
    w, h = 300, 190
    im = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = 40, 40
    pts = [(ox + 70, oy), (ox + w, oy), (ox + w, oy + h), (ox + 70, oy + h), (ox, oy + h / 2)]
    d.polygon(pts, fill=YEL, outline=INK, width=6)
    d.ellipse((ox + 38, oy + h / 2 - 16, ox + 70, oy + h / 2 + 16), fill=INK)
    t = text_img("₩ ?", 104, INK, "Black", shadow=0)
    im.alpha_composite(t, (ox + 70 + (w - 70 - t.width) // 2, oy + (h - t.height) // 2))
    return im


@lru_cache(None)
def check_circle(d=110, color=RED, mark=WHITE):
    im = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    g.ellipse((0, 0, d - 1, d - 1), fill=color)
    g.line([(d * .27, d * .52), (d * .44, d * .68), (d * .74, d * .33)], fill=mark, width=int(d * .11),
           joint="curve")
    return im


@lru_cache(None)
def pin_icon(s=64):
    im = Image.new("RGBA", (s, int(s * 1.35)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, s, s), fill=RED)
    d.polygon([(s * .12, s * .7), (s * .88, s * .7), (s / 2, s * 1.33)], fill=RED)
    d.ellipse((s * .32, s * .32, s * .68, s * .68), fill=WHITE)
    return im


@lru_cache(None)
def phone_icon(s=120):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, s - 1, s - 1), fill=RED)
    # 수화기 실루엣
    k = s / 120
    d.rounded_rectangle((30 * k, 26 * k, 52 * k, 54 * k), 8 * k, fill=WHITE)
    d.rounded_rectangle((66 * k, 68 * k, 94 * k, 90 * k), 8 * k, fill=WHITE)
    d.arc((24 * k, 22 * k, 104 * k, 102 * k), 90, 180, fill=WHITE, width=int(18 * k))
    return im


# ------------------------------------------------------------------ helpers
def shake(t, hits, amp=26):
    dx = dy = 0.0
    for h0, a in hits:
        if 0 <= t - h0 < 0.45:
            e = math.exp(-(t - h0) * 11) * amp * a
            dx += e * math.sin((t - h0) * 95)
            dy += e * math.cos((t - h0) * 73)
    return dx, dy


def chunk_t(i, j):
    return TL["chunks"][i][j][0]


def line_t(i):
    return TL["line_starts"][i]


# ------------------------------------------------------------------ scenes
def scene1(c, t):
    src = load("photo_street.jpg")
    z = 1.12 + 0.18 * prog(t, 0, 3.4)
    c.alpha_composite(cover(src, W, H, z, 0.32, 0.5))
    c.alpha_composite(overlay(120))
    c.alpha_composite(bottom_glow(RED, 1000, 150), (0, H - 1000))
    draw_stripes(c, t)
    # 배경 물음표
    q = text_img("?", 1100, RED, "Black", shadow=0)
    paste(c, q, 820, 1050, 1.0, 12 * math.sin(t * 1.6), 0.18 * prog(t, 0.1, 0.4))
    # 가격표
    p = out_back(prog(t, 0.25, 0.45))
    sw = 14 * math.sin(t * 5.5) * math.exp(-max(0, t - 0.25) * 0.6) + 10
    paste(c, price_tag(), 760, 400, p, sw, p)
    # 1줄
    l0 = line_t(0)
    p1 = out_cubic(prog(t, l0 - 0.05, 0.35))
    paste(c, text_img("타이어 바꾸실 때", 100, WHITE, "Black", stroke=4), -500 + 1040 * p1, 640, 1, 0, p1)
    # '가격만' 슬램
    k = chunk_t(0, 1)
    p2 = out_cubic(prog(t, k - 0.05, 0.22))
    if t > k - 0.05:
        paste(c, text_img("가격만", 245, YEL, "Black", stroke=12, sfill=INK), 540, 880, 2.6 - 1.6 * p2, -4, p2)
    p3 = out_back(prog(t, k + 0.35, 0.35))
    paste(c, text_img("보세요?", 210, WHITE, "Black", stroke=10, sfill=INK), 560, 1130, p3, 0, p3)


def scene2(c, t):
    s0 = TL["scene_starts"][1]
    lt = t - s0
    src = load("poster_square.png")
    c.alpha_composite(cover(blurred("poster_square.png", 14), W, H, 1.05 + 0.05 * prog(lt, 0, 6),
                            0.5, 0.5, (0, 330, 1254, 880)))
    c.alpha_composite(overlay(175))
    draw_stripes(c, t)
    paste(c, burst(), 540, 560, 1.0, t * 14, 0.9)
    # 잠깐! 스탬프
    p = out_cubic(prog(lt, 0.0, 0.2))
    stamp = compose((box(640, 270, 40, RED, WHITE, 10), 0, 0),
                    (text_img("잠깐!", 200, WHITE, "Black", shadow=6), 0, -6))
    paste(c, stamp, 540, 560, 3.0 - 2.0 * p, -6, p)
    # 비교 카드 A: 가격
    ka = chunk_t(1, 1)
    pa = out_cubic(prog(t, ka, 0.35))
    kb = chunk_t(1, 2)
    pb = out_back(prog(t, kb, 0.4))
    dim = prog(t, kb, 0.3)
    card_a = compose((box(860, 170, 34, (60, 60, 68)), 0, 0),
                     (text_img("가격", 86, (225, 225, 230), "Black", shadow=0), -210, -4),
                     (text_img("도 중요하지만…", 62, (200, 200, 205), "Bold", shadow=0), 70, 2))
    paste(c, card_a, 540 + (1 - pa) * 900, 920, 1 - 0.1 * dim, 0, pa * (1 - 0.45 * dim))
    # 비교 카드 B: 내 차에 맞는 선택
    pulse = 1 + 0.025 * math.sin(max(0, t - kb) * 7) * prog(t, kb + 0.4, 0.2)
    card_b = compose((box(960, 220, 40, RED, YEL, 8), 0, 0),
                     (check_circle(120, WHITE, RED), -365, 0),
                     (text_img("내 차에 맞는 선택", 88, WHITE, "Black", shadow=4), 60, -4))
    paste(c, card_b, 540, 1150, pb * pulse, 0, clamp(pb))
    # 더 중요! 배지
    kc = chunk_t(1, 3)
    pc = out_back(prog(t, kc, 0.35))
    badge = compose((box(330, 110, 55, YEL, INK, 6, False), 0, 0),
                    (text_img("더 중요!", 66, INK, "Black", shadow=0), 0, -2))
    paste(c, badge, 880, 1040, pc, 8, clamp(pc))


def scene3(c, t, line=2, title_txt="꼼꼼한 점검",
           labels=(("01", "타이어 상태"), ("02", "마모 점검"), ("03", "휠얼라인먼트")),
           times_fn=None, stamp_txt="꼼꼼하게!"):
    s0 = TL["scene_starts"][line]
    lt = t - s0
    c.alpha_composite(dark_grad())
    draw_stripes(c, t)
    c.alpha_composite(bottom_glow(DRED, 700, 120), (0, H - 700))
    # 타이틀
    pt = out_back(prog(lt, 0.0, 0.4))
    title = compose((box(560, 120, 60, RED, shadow=False), 0, 0),
                    (text_img(title_txt, 76, WHITE, "Black", shadow=0), 0, -3))
    paste(c, title, 540, 300, pt, 0, clamp(pt))
    # 매장 사진 카드 + Ken Burns
    pc = out_cubic(prog(lt, 0.05, 0.45))
    card = photo_card(load("poster_square.png"), 960, 430, 1.0 + 0.25 * prog(lt, 0, 6),
                      0.45, 0.75, (40, 330, 1214, 830))
    cy = 620 + (1 - pc) * 120
    paste(c, card, 540, cy, 0.9 + 0.1 * pc, 0, pc)
    # 스캔 레이저 + HUD 코너
    if pc > 0.9:
        top, bot = cy - 215, cy + 215
        ph = (math.sin(lt * 3.2) + 1) / 2
        ly = top + 10 + (bot - top - 20) * ph
        laser = Image.new("RGBA", (960, 60), (0, 0, 0, 0))
        g = ImageDraw.Draw(laser)
        for i in range(30):
            g.line([(0, 30 - i), (959, 30 - i)], fill=(255, 40, 40, int(70 * (1 - i / 30))))
            g.line([(0, 30 + i), (959, 30 + i)], fill=(255, 40, 40, int(70 * (1 - i / 30))))
        g.line([(0, 30), (959, 30)], fill=(255, 230, 230, 255), width=4)
        paste(c, laser, 540, ly)
        d = ImageDraw.Draw(c)
        L = 60
        for (x, y, sx, sy) in [(70, top - 10, 1, 1), (1010, top - 10, -1, 1), (70, bot + 10, 1, -1),
                               (1010, bot + 10, -1, -1)]:
            d.line([(x, y), (x + L * sx, y)], fill=YEL, width=8)
            d.line([(x, y), (x, y + L * sy)], fill=YEL, width=8)
        scan = text_img("SCANNING" + "." * (int(lt * 4) % 4), 34, YEL, "ExtraBold", shadow=4)
        paste(c, scan, 160 + scan.width / 2 - 60, bot - 30)
    # 체크리스트
    k0, k1, k2 = chunk_t(line, 0), chunk_t(line, 1), chunk_t(line, 2)
    times = times_fn(k0, k1, k2) if times_fn else [k0 + 0.1, k0 + 0.55 * (k1 - k0), k1]
    for i, (tt, (num, lab)) in enumerate(zip(times, labels)):
        p = out_cubic(prog(t, tt, 0.32))
        if p <= 0:
            continue
        pk = out_back(prog(t, tt + 0.3, 0.3))
        row = compose((box(900, 124, 30, WHITE), 0, 0),
                      (text_img(num, 54, RED, "Black", shadow=0), -370, 0),
                      (text_img(lab, 64, INK, "Black", shadow=0), -60, -2))
        y = 940 + i * 150
        paste(c, row, 540 + (1 - p) * 800, y, 1, 0, p)
        if pk > 0:
            flash = 1 + 0.15 * prog(t, k2, 0.15) * (1 - prog(t, k2 + 0.15, 0.25))
            paste(c, check_circle(96), 900, y, pk * flash, 0, clamp(pk))
    # 꼼꼼하게! 스탬프
    pk = out_back(prog(t, k2, 0.35))
    st_img = text_img(stamp_txt, 76, INK, "Black", shadow=0)
    stamp = compose((box(max(420, st_img.width + 40), 120, 24, YEL, INK, 6, False), 0, 0), (st_img, 0, -3))
    paste(c, stamp, 760, 800, pk, -7, clamp(pk))


def scene4(c, t):
    s0 = TL["scene_starts"][3]
    lt = t - s0
    c.alpha_composite(dark_grad((50, 6, 10), (10, 6, 8)))
    paste(c, burst(1700, 20, RED, 70), 540, 860, 1.0, -t * 10)
    draw_stripes(c, t)
    swap = chunk_t(3, 2) - 0.1
    ps = in_out(prog(t, swap, 0.4))
    # 포스터 카드 (매장 → 렌탈)
    pin = out_back(prog(lt, 0.15, 0.55), 1.4)
    for k, (name, x0) in enumerate([("poster_store.png", 540 - 1100 * ps), ("poster_rental.png", 540 + 1100 * (1 - ps))]):
        if (k == 0 and ps >= 1) or (k == 1 and ps <= 0):
            continue
        src = load(name)
        z = 1.0 + 0.08 * prog(lt if k == 0 else t - swap, 0, 5)
        card = photo_card(src, 700, 875, z, 0.5, 0.45, r=30, border=8)
        # 빛 반사 스윕
        sh_p = ((lt * 0.75) % 1.0)
        band = Image.new("RGBA", card.size, (0, 0, 0, 0))
        g = ImageDraw.Draw(band)
        bx = -400 + (card.width + 800) * sh_p
        g.polygon([(bx, 0), (bx + 120, 0), (bx - 280, card.height), (bx - 400, card.height)],
                  fill=(255, 255, 255, 70))
        band.putalpha(Image.fromarray(np.minimum(np.asarray(band.getchannel("A")),
                                                 np.asarray(card.getchannel("A"))).astype(np.uint8)))
        card = Image.alpha_composite(card, band)
        yy = 860 + (1 - pin) * 1300 if k == 0 else 860
        paste(c, card, x0, yy, 1.0, (1 - pin) * 6 if k == 0 else -3 * (1 - ps), 1.0)
    # 리본: 금호타이어 전문점
    pr = out_cubic(prog(lt, 0.0, 0.2))
    rib = Image.new("RGBA", (900, 150), (0, 0, 0, 0))
    ImageDraw.Draw(rib).polygon([(40, 0), (900, 0), (860, 150), (0, 150)], fill=RED)
    rib = compose((rib, 0, 0), (text_img("금호타이어 전문점", 92, WHITE, "Black", shadow=4), 0, -4))
    paste(c, rib, 540, 290, 1.9 - 0.9 * pr, -3, pr)
    # 합리적으로 배지
    pb = out_back(prog(t, swap + 0.3, 0.35))
    badge = compose((box(620, 96, 48, YEL, INK, 5, False), 0, 0),
                    (text_img("합리적인 가격 · 렌탈 상담", 50, INK, "Black", shadow=0), 0, -2))
    paste(c, badge, 540, 1340, pb, 0, clamp(pb))


@lru_cache(None)
def service_tiles():
    src = load("poster_store.png")
    boxes = [(28, 908, 282, 1122), (300, 908, 560, 1122), (578, 908, 822, 1122), (840, 908, 1100, 1122)]
    tiles = []
    for b in boxes:
        im = src.crop(b)
        tw, th = 420, 330
        s = min((tw - 30) / im.width, (th - 30) / im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        base = box(tw, th, 30, WHITE).copy()
        base.alpha_composite(im, ((base.width - im.width) // 2, (base.height - im.height) // 2))
        tiles.append(base)
    return tiles


def scene5(c, t):
    s0 = TL["scene_starts"][4]
    lt = t - s0
    c.alpha_composite(dark_grad())
    draw_stripes(c, t)
    c.alpha_composite(bottom_glow(RED, 900, 120), (0, H - 900))
    p1 = out_cubic(prog(lt, 0.0, 0.35))
    paste(c, text_img("교환부터 휠얼라인먼트까지", 70, WHITE, "Black", stroke=3), 540, 280 + (1 - p1) * 60, 1, 0, p1)
    k = chunk_t(4, 1)
    p2 = out_cubic(prog(t, k, 0.22))
    paste(c, text_img("한곳에서!", 170, YEL, "Black", stroke=10, sfill=INK), 540, 440, 2.2 - 1.2 * p2, -3, p2)
    pos = [(300, 760), (780, 760), (300, 1120), (780, 1120)]
    for i, (tile, (x, y)) in enumerate(zip(service_tiles(), pos)):
        p = out_back(prog(lt, 0.15 + 0.28 * i, 0.4))
        bob = 6 * math.sin(t * 3 + i)
        paste(c, tile, x, y + bob * prog(lt, 1.5, 0.3), p, 0, clamp(p))
    pb = out_back(prog(t, k, 0.45))
    if pb > 0:
        ring = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
        g = ImageDraw.Draw(ring)
        g.ellipse((0, 0, 259, 259), fill=RED, outline=WHITE, width=10)
        ring = compose((ring, 0, 0), (text_img("ONE", 62, WHITE, "Black", shadow=0), 0, -28),
                       (text_img("STOP", 62, YEL, "Black", shadow=0), 0, 36))
        pul = 1 + 0.05 * math.sin(max(0, t - k) * 8) * prog(t, k + 0.45, 0.2)
        paste(c, ring, 540, 940, pb * pul, -360 * (1 - clamp(pb)) - 8, clamp(pb))


def scene6(c, t):
    s0 = TL["scene_starts"][5]
    lt = t - s0
    c.alpha_composite(cover(blurred("photo_street.jpg", 5), W, H, 1.1 + 0.1 * prog(lt, 0, 8), 0.25, 0.45))
    c.alpha_composite(overlay(165))
    c.alpha_composite(bottom_glow(RED, 1100, 170), (0, H - 1100))
    draw_stripes(c, t)
    p0 = out_cubic(prog(lt, 0.0, 0.35))
    paste(c, text_img(TL.get("cta_top", "타이어 교환 고민 중이세요?"), 72, WHITE, "Black", stroke=3), 540, 300 + (1 - p0) * 50, 1, 0, p0)
    k1 = chunk_t(5, 1)
    p1 = out_cubic(prog(t, k1, 0.22))
    name = compose((box(980, 230, 36, RED, WHITE, 8), 0, 0),
                   (text_img("금호타이어 송월점", 112, WHITE, "Black", shadow=4), 0, -4))
    tag = compose((box(170, 76, 38, YEL, shadow=False), 0, 0), (text_img("나주", 50, INK, "Black", shadow=0), 0, -2))
    paste(c, name, 540, 500, 2.0 - 1.0 * p1, 0, p1)
    pt = out_back(prog(t, k1 + 0.15, 0.3))
    paste(c, tag, 170, 390, pt, -8, clamp(pt))
    # 전화 버튼
    pp = out_back(prog(t, k1 + 0.45, 0.4))
    if pp > 0:
        since = max(0, t - (k1 + 0.85))
        for j in range(2):
            ph = (since * 0.9 + j * 0.5) % 1.0
            if since > 0:
                ring = Image.new("RGBA", (1100, 300), (0, 0, 0, 0))
                ImageDraw.Draw(ring).rounded_rectangle((50, 50, 1049, 249), 100, outline=(255, 255, 255, int(200 * (1 - ph))), width=6)
                paste(c, ring, 540, 760, 0.86 + 0.12 * ph)
        btn = compose((box(940, 180, 90, WHITE), 0, 0), (phone_icon(126), -370, 0),
                      (text_img("061-335-6114", 96, RED, "Black", shadow=0), 70, -4))
        pul = 1 + 0.035 * math.sin(since * 7)
        paste(c, btn, 540, 760, pp * pul, 0, clamp(pp))
        if TL.get("cta_btn_tag"):
            pg = out_back(prog(t, k1 + 0.75, 0.35))
            bt = text_img(TL["cta_btn_tag"], 44, INK, "Black", shadow=0)
            paste(c, compose((box(bt.width + 50, 72, 36, YEL, INK, 4, False), 0, 0), (bt, 0, -2)),
                  850, 672, pg, 6, clamp(pg))
    # 주소
    pa = out_cubic(prog(t, k1 + 0.8, 0.35))
    addr = compose((pin_icon(56), -330, -4), (text_img("전남 나주시 예향로 4101", 58, WHITE, "Bold", stroke=2), 40, 0))
    paste(c, addr, 540, 930, 1, 0, pa)
    # QR + 네이버 리뷰
    k2 = chunk_t(5, 2)
    pq = out_back(prog(t, k2 - 0.3, 0.45))
    if pq > 0:
        qr = load("qr_review.png").resize((270, 270), Image.NEAREST)
        qcard = box(310, 310, 26, WHITE).copy()
        qcard.alpha_composite(qr, ((qcard.width - 270) // 2, (qcard.height - 270) // 2))
        paste(c, qcard, 300, 1170, pq, 0, clamp(pq))
        pl = out_cubic(prog(t, k2 - 0.1, 0.35))
        paste(c, text_img("네이버 리뷰", 70, YEL, "Black", stroke=3), 680 + (1 - pl) * 80, 1105, 1, 0, pl)
        paste(c, text_img("QR 스캔 후 리뷰 작성", 46, WHITE, "Bold", stroke=2), 680 + (1 - pl) * 80, 1190, 1, 0, pl)
        paste(c, text_img("고객님의 리뷰가 큰 힘이 됩니다", 34, (230, 230, 230), "SemiBold", stroke=2),
              680 + (1 - pl) * 80, 1250, 1, 0, pl)


SCENES = [scene1, scene2, scene3, scene4, scene5, scene6]
EPISODES = {"ep1": SCENES}  # 다른 에피소드는 epN.py 에서 등록


# ------------------------------------------------------------------ frame
def subtitle(c, t):
    for i, ch in enumerate(TL["chunks"]):
        for (st, en, txt) in ch:
            if st <= t < en:
                p = out_back(prog(t, st, 0.16), 2.4)
                im = rich_img(txt, 76)
                if im.width > 1020:
                    im = im.resize((1020, int(im.height * 1020 / im.width)), Image.BICUBIC)
                paste(c, im, 540, 1470, 0.8 + 0.2 * p, 0, clamp(p * 1.5))
                return


def frame(idx):
    t = idx / FPS
    ss = TL["scene_starts"]
    si = max(i for i in range(len(ss)) if ss[i] <= t)
    c = Image.new("RGBA", (W, H), DARK + (255,))
    EPISODES.get(TL.get("ep", "ep1"), SCENES)[si](c, t)
    c.alpha_composite(vignette())
    # 카메라 쉐이크
    dx, dy = shake(t, TL["shakes"])
    if abs(dx) + abs(dy) > 0.5:
        c = c.transform((W, H), Image.AFFINE, (1, 0, -dx, 0, 1, -dy), Image.BILINEAR, fillcolor=DARK + (255,))
    # 상단 브랜드/진행바, 자막
    paste(c, brand_pill(), 60 + brand_pill().width / 2, 150)
    subtitle(c, t)
    d = ImageDraw.Draw(c)
    d.rectangle((0, 0, int(W * t / TL["total"]), 9), fill=RED)
    # 장면 전환 플래시
    for s in ss[1:]:
        if 0 <= t - s < 0.18:
            c.alpha_composite(overlay(int(200 * (1 - (t - s) / 0.18)), (255, 255, 255)))
    return c.convert("RGB")


def _render_part(args):
    k, i0, i1, path, tl = args
    global TL
    TL = tl
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                          "-crf", "17", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(frame(i).tobytes())
    p.stdin.close()
    p.wait()
    return path


def render(tl, build_dir, workers=4):
    from multiprocessing import Pool
    global TL
    TL = tl
    n = int(round(tl["total"] * FPS))
    step = math.ceil(n / workers)
    jobs = [(k, k * step, min(n, (k + 1) * step), os.path.join(build_dir, f"part_{k}.mp4"), tl)
            for k in range(workers) if k * step < n]
    with Pool(workers) as pool:
        parts = pool.map(_render_part, jobs)
    lst = os.path.join(build_dir, "parts.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    out = os.path.join(build_dir, "video_noaudio.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                           "-c", "copy", out])
    return out
