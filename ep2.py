"""에피소드 2: '타이어 4개 바꾸려는데… 왜 이렇게 비싸?'

장면 구성 (대본 6단락)
 S1 후킹      : 타이어 4개가 떨어지며 착지 + 견적 금액 숫자 롤링 → '왜 이렇게 비싸?!'
 S2 공감      : 저울(저렴 vs 좋은 타이어)이 좌우로 기우는 딜레마 + '불안' / '부담' 태그
 S3 해결책    : '잠깐!' 스탬프 + '무조건 비싼 타이어 = 정답?' 카드에 X 표시
 S4 전문성    : 매장 사진 스캔 + 규격 / 주행 습관 / 예산 체크리스트
 S5 구매 욕구 : 매장 포스터 + '합리적인 가격' 배지 → 교환·얼라인먼트 서비스 타일
 S6 CTA       : '타이어 가격 궁금하세요?' + 매장명 / 전화(견적 문의) / 주소 / QR
"""
import math
import random

from PIL import Image, ImageDraw

import video as V
from video import (W, H, RED, DRED, YEL, WHITE, INK, prog, out_cubic, out_back, in_out, clamp,
                   load, blurred, text_img, box, compose, paste, cover, photo_card, dark_grad,
                   draw_stripes, bottom_glow, overlay, burst, check_circle, service_tiles)

OUT_NAME = "kumho_songwol_shorts_ep2"

LINES = [
    "타이어 4개 바꾸려는데… 왜 이렇게 비싸?",
    "싸게 하자니 불안하고, 좋은 걸 하자니 부담되고!",
    "잠깐! 무조건 비싼 타이어가 정답은 아니죠.",
    "내 차에 맞는 규격부터 주행 습관, 예산까지 확인하고!",
    "금호타이어를 합리적인 가격으로! 교환부터 얼라인먼트까지!",
    "타이어 가격 궁금하세요? 나주 금호타이어 송월점! 견적부터 물어보세요!",
]

CHUNKS = [
    ["타이어 *4개* 바꾸려는데…", "왜 이렇게 *비싸?*"],
    ["싸게 하자니 *불안*하고,", "좋은 걸 하자니 *부담*되고!"],
    ["*잠깐!*", "무조건 *비싼 타이어*가", "*정답*은 아니죠."],
    ["내 차에 맞는 *규격*부터", "*주행 습관*, *예산*까지", "*확인*하고!"],
    ["*금호타이어*를", "*합리적인 가격*으로!", "*교환*부터 *얼라인먼트*까지!"],
    ["타이어 가격 궁금하세요?", "나주 *금호타이어 송월점!*", "*견적*부터 물어보세요!"],
]

EXTRA = {"cta_top": "타이어 가격 궁금하세요?", "cta_btn_tag": "견적 문의"}


def ck(i, j):
    return V.TL["chunks"][i][j][0]


def ss(i):
    return V.TL["scene_starts"][i]


# ------------------------------------------------------------------ 그래픽
_TIRE = {}


def tire_img(d=220):
    if d in _TIRE:
        return _TIRE[d]
    S = d * 2  # 2배로 그린 뒤 축소 (안티앨리어싱)
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    g = ImageDraw.Draw(im)
    c, r = S / 2, S / 2 - 2
    g.ellipse((c - r, c - r, c + r, c + r), fill=(22, 22, 26))
    for k in range(32):  # 트레드 블록
        a0, a1 = 2 * math.pi * k / 32, 2 * math.pi * (k + 0.55) / 32
        pts = [(c + rr * math.cos(a), c + rr * math.sin(a))
               for rr, a in [(r * .86, a0), (r * .99, a0), (r * .99, a1), (r * .86, a1)]]
        g.polygon(pts, fill=(52, 52, 58))
    g.ellipse((c - r * .66, c - r * .66, c + r * .66, c + r * .66), fill=(60, 60, 68))
    for k in range(5):  # 스포크
        a = 2 * math.pi * k / 5
        g.line([(c, c), (c + r * .6 * math.cos(a), c + r * .6 * math.sin(a))], fill=(200, 200, 208),
               width=int(r * .15))
    g.ellipse((c - r * .66, c - r * .66, c + r * .66, c + r * .66), outline=(215, 215, 222), width=int(r * .07))
    g.ellipse((c - r * .17, c - r * .17, c + r * .17, c + r * .17), fill=(215, 215, 222))
    g.ellipse((c - r * .07, c - r * .07, c + r * .07, c + r * .07), fill=RED)
    _TIRE[d] = im.resize((d, d), Image.LANCZOS)
    return _TIRE[d]


def x_mark(c, cx, cy, size, p, width=26):
    """두 획이 차례로 그어지는 빨간 X"""
    d = ImageDraw.Draw(c)
    h = size / 2
    p1, p2 = clamp(p * 2), clamp(p * 2 - 1)
    if p1 > 0:
        d.line([(cx - h, cy - h), (cx - h + 2 * h * p1, cy - h + 2 * h * p1)], fill=RED, width=width)
    if p2 > 0:
        d.line([(cx + h, cy - h), (cx + h - 2 * h * p2, cy - h + 2 * h * p2)], fill=RED, width=width)


# ------------------------------------------------------------------ 장면
def scene1(c, t):
    c.alpha_composite(cover(load("photo_street.jpg"), W, H, 1.15 + 0.15 * prog(t, 0, 3), 0.3, 0.5))
    c.alpha_composite(overlay(150))
    c.alpha_composite(bottom_glow(RED, 900, 140), (0, H - 900))
    draw_stripes(c, t)
    paste(c, text_img("타이어 4개 교체", 92, WHITE, "Black", stroke=4), 540, 330, 1, 0,
          out_cubic(prog(t, 0.05, 0.3)))
    # 타이어 4개 낙하 + 바운스
    t0 = V.TL["line_starts"][0] + 0.15
    for i in range(4):
        st = t0 + 0.14 * i
        p = prog(t, st, 0.45)
        if p <= 0:
            continue
        y = -200 + (600 - -200) * out_back(p, 1.6)
        rot = -(1 - out_cubic(p)) * 300 - 6 * math.sin(t * 2 + i) * (p >= 1)
        paste(c, tire_img(220), 150 + 260 * i, y, 1, rot)
    # x4 배지
    pb = out_back(prog(t, t0 + 0.14 * 3 + 0.4, 0.3))
    badge = compose((box(150, 150, 75, YEL, INK, 6, False), 0, 0), (text_img("×4", 76, INK, "Black", shadow=0), 0, -4))
    paste(c, badge, 950, 470, pb, 10, clamp(pb))
    # 견적 금액 보드 (숫자 롤링 → ???)
    k1 = ck(0, 1)
    pbd = out_cubic(prog(t, t0 + 0.3, 0.35))
    if pbd > 0:
        if t < k1:
            rnd = random.Random(int(t * 30))
            num = f"₩ {rnd.randint(100, 999)},{rnd.randint(0, 999):03d}"
            col = WHITE
        else:
            num, col = "₩ ???,???", (255, 70, 70)
        board = compose((box(880, 230, 36, (20, 20, 24), RED, 6), 0, 0),
                        (text_img("견적 금액", 40, (200, 200, 200), "Bold", shadow=0), 0, -70),
                        (text_img(num, 118, col, "Black", shadow=0), 0, 25))
        paste(c, board, 540, 900 + (1 - pbd) * 80, 1, 0, pbd)
    # 왜 이렇게 비싸?!
    p2 = out_cubic(prog(t, k1, 0.22))
    if t >= k1:
        paste(c, text_img("왜 이렇게 비싸?!", 132, (255, 60, 60), "Black", stroke=10, sfill=WHITE),
              540, 1170, 2.2 - 1.2 * p2, -4 + 3 * math.sin(t * 30) * (1 - prog(t, k1, 0.5)), p2)


def scene2(c, t):
    lt = t - ss(1)
    c.alpha_composite(dark_grad())
    draw_stripes(c, t)
    c.alpha_composite(bottom_glow(DRED, 800, 120), (0, H - 800))
    pt = out_back(prog(lt, 0.0, 0.4))
    title = compose((box(520, 120, 60, RED, shadow=False), 0, 0),
                    (text_img("고민되시죠?", 76, WHITE, "Black", shadow=0), 0, -3))
    paste(c, title, 540, 300, pt, 0, clamp(pt))
    k0, k1 = ck(1, 0), ck(1, 1)
    # 저울: 1구간엔 '저렴' 쪽(왼쪽)이 위로 들려 불안, 2구간엔 '좋은' 쪽(오른쪽)이 무겁게 내려가 부담
    ang = -11 * in_out(prog(t, k0 + 0.2, 0.5)) + 22 * in_out(prog(t, k1 + 0.1, 0.5))
    ang += 2.0 * math.sin(lt * 4) * clamp(lt)
    pa = out_cubic(prog(lt, 0.05, 0.4))
    a = math.radians(ang)
    px, py = 540, 600
    L = 360
    lx, ly = px - L * math.cos(a), py - L * math.sin(a)
    rx, ry = px + L * math.cos(a), py + L * math.sin(a)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(layer)
    g.polygon([(px - 120, 1080), (px + 120, 1080), (px + 40, 1020), (px - 40, 1020)], fill=(210, 210, 218))
    g.line([(px, py), (px, 1030)], fill=(210, 210, 218), width=22)
    g.line([(lx, ly), (rx, ry)], fill=WHITE, width=20)
    g.ellipse((px - 30, py - 30, px + 30, py + 30), fill=YEL, outline=INK, width=5)
    for ex, ey in [(lx, ly), (rx, ry)]:
        g.line([(ex, ey), (ex - 110, ey + 150)], fill=(200, 200, 200), width=5)
        g.line([(ex, ey), (ex + 110, ey + 150)], fill=(200, 200, 200), width=5)
        g.chord((ex - 160, ey + 100, ex + 160, ey + 210), 0, 180, fill=(170, 170, 180))
    if pa < 1:
        a_ = (layer.getchannel("A").point(lambda v: int(v * pa)))
        layer.putalpha(a_)
    c.alpha_composite(layer)
    # 접시 위 카드
    cheap = compose((box(290, 120, 26, (70, 70, 78), shadow=False), 0, 0),
                    (text_img("저렴한 타이어", 44, WHITE, "Black", shadow=0), 0, -2))
    good = compose((box(290, 120, 26, RED, YEL, 5, False), 0, 0),
                   (text_img("좋은 타이어", 48, WHITE, "Black", shadow=0), 0, -2))
    paste(c, cheap, lx, ly + 95, 1, 0, pa)
    paste(c, good, rx, ry + 95, 1, 0, pa)
    # 불안 / 부담 태그
    for (txt, x, y, st) in [("불안…", lx, ly + 290, k0 + 0.45), ("부담…", rx, ry + 290, k1 + 0.45)]:
        p = out_back(prog(t, st, 0.35))
        tag = compose((box(220, 100, 50, YEL, INK, 5, False), 0, 0), (text_img(txt, 58, INK, "Black", shadow=0), 0, -3))
        paste(c, tag, x, y, p, -6 if x < 540 else 6, clamp(p))


def scene3(c, t):
    lt = t - ss(2)
    c.alpha_composite(cover(blurred("poster_square.png", 14), W, H, 1.05 + 0.05 * prog(lt, 0, 6),
                            0.5, 0.5, (0, 330, 1254, 880)))
    c.alpha_composite(overlay(180))
    draw_stripes(c, t)
    paste(c, burst(), 540, 520, 1.0, t * 14, 0.9)
    p = out_cubic(prog(lt, 0.0, 0.2))
    stamp = compose((box(640, 270, 40, RED, WHITE, 10), 0, 0),
                    (text_img("잠깐!", 200, WHITE, "Black", shadow=6), 0, -6))
    paste(c, stamp, 540, 520, 3.0 - 2.0 * p, -6, p)
    k1, k2 = ck(2, 1), ck(2, 2)
    pc = out_cubic(prog(t, k1 - 0.05, 0.35))
    card = compose((box(960, 300, 40, (24, 24, 28), WHITE, 6), 0, 0),
                   (text_img("무조건 비싼 타이어", 84, WHITE, "Black", shadow=0), 0, -55),
                   (text_img("= 정답?", 84, YEL, "Black", shadow=0), 0, 60))
    paste(c, card, 540 + (1 - pc) * 900, 1000, 1, 0, pc)
    if t >= k2:
        x_mark(c, 540, 1000, 300, out_cubic(prog(t, k2, 0.35)), 30)
        pn = out_back(prog(t, k2 + 0.3, 0.35))
        no = compose((box(260, 120, 60, RED, WHITE, 6, False), 0, 0), (text_img("NO!", 80, WHITE, "Black", shadow=0), 0, -3))
        paste(c, no, 860, 840, pn, 10, clamp(pn))


def scene4(c, t):
    V.scene3(c, t, line=3, title_txt="맞춤 상담",
             labels=(("01", "타이어 규격"), ("02", "주행 습관"), ("03", "예산 확인")),
             times_fn=lambda k0, k1, k2: [k0 + 0.6 * (k1 - k0), k1 + 0.05, k1 + 0.55 * (k2 - k1)],
             stamp_txt="꼼꼼하게 확인!")


def scene5(c, t):
    lt = t - ss(4)
    c.alpha_composite(dark_grad((50, 6, 10), (10, 6, 8)))
    paste(c, burst(1700, 20, RED, 70), 540, 760, 1.0, -t * 10)
    draw_stripes(c, t)
    k1, k2 = ck(4, 1), ck(4, 2)
    # 리본
    pr = out_cubic(prog(lt, 0.0, 0.2))
    rib = Image.new("RGBA", (760, 150), (0, 0, 0, 0))
    ImageDraw.Draw(rib).polygon([(40, 0), (760, 0), (720, 150), (0, 150)], fill=RED)
    rib = compose((rib, 0, 0), (text_img("금호타이어", 100, WHITE, "Black", shadow=4), 0, -4))
    paste(c, rib, 540, 290, 1.9 - 0.9 * pr, -3, pr)
    # 포스터 카드: 등장 → 교환/얼라인먼트 구간에 위로 작아짐
    pin = out_back(prog(lt, 0.15, 0.55), 1.4)
    shrink = in_out(prog(t, k2 - 0.1, 0.4))
    card = photo_card(load("poster_store.png"), 640, 800, 1.0 + 0.08 * prog(lt, 0, 5), 0.5, 0.45, r=30)
    sh = (lt * 0.75) % 1.0
    band = Image.new("RGBA", card.size, (0, 0, 0, 0))
    bx = -400 + (card.width + 800) * sh
    ImageDraw.Draw(band).polygon([(bx, 0), (bx + 120, 0), (bx - 280, card.height), (bx - 400, card.height)],
                                 fill=(255, 255, 255, 70))
    import numpy as np
    band.putalpha(Image.fromarray(np.minimum(np.asarray(band.getchannel("A")),
                                             np.asarray(card.getchannel("A"))).astype(np.uint8)))
    card = Image.alpha_composite(card, band)
    cy = 820 + (1 - pin) * 1300 - 180 * shrink
    paste(c, card, 540, cy, 1 - 0.38 * shrink, (1 - pin) * 6, 1)
    # 합리적인 가격 배지 (+ 동전 반짝)
    pb = out_back(prog(t, k1, 0.35))
    badge = compose((box(560, 110, 55, YEL, INK, 6, False), 0, 0),
                    (text_img("합리적인 가격", 66, INK, "Black", shadow=0), 0, -3))
    by = 1250 - 470 * shrink
    paste(c, badge, 540, by, pb, -4, clamp(pb) * (1 - 0.0 * shrink))
    # 교환 → 얼라인먼트 타일
    tiles = service_tiles()
    for i, (tile, x) in enumerate([(tiles[0], 300), (tiles[1], 780)]):
        p = out_back(prog(t, k2 + 0.15 + 0.3 * i, 0.4))
        paste(c, tile, x, 1150, 0.92 * p, 0, clamp(p))
    pa = out_cubic(prog(t, k2 + 0.4, 0.3))
    arrow = Image.new("RGBA", (90, 90), (0, 0, 0, 0))
    ImageDraw.Draw(arrow).polygon([(10, 25), (50, 25), (50, 5), (85, 45), (50, 85), (50, 65), (10, 65)], fill=RED)
    paste(c, arrow, 540, 1150, pa, 0, pa)


SCENES = [scene1, scene2, scene3, scene4, scene5, V.scene6]
V.EPISODES["ep2"] = SCENES


def shakes(chunks, scene_starts):
    return [(chunks[0][1][0], 1.0), (scene_starts[2], 1.0), (chunks[2][2][0], 0.7),
            (scene_starts[4], 0.7), (chunks[5][1][0], 0.9)]


def sfx_events(tl):
    c, s = tl["chunks"], tl["scene_starts"]
    t0 = tl["line_starts"][0] + 0.15
    ev = [(0.02, "whoosh", 0.7, 0)]
    for i in range(4):  # 타이어 착지
        ev += [(t0 + 0.14 * i + 0.3, "impact", 0.35, (-0.6, -0.2, 0.2, 0.6)[i])]
    ev += [(t0 + 0.14 * 3 + 0.4, "pop", 0.8, 0.4)]
    # 숫자 롤링 클릭
    tt = t0 + 0.35
    while tt < c[0][1][0] - 0.05:
        ev.append((tt, "click", 0.35, 0))
        tt += 0.09
    ev += [(c[0][1][0] - 0.03, "impact", 0.9, 0), (c[0][1][0], "stop", 0.6, 0),
           (s[1] - 0.2, "whoosh", 0.8, 0), (s[1] + 0.05, "click", 0.6, 0),
           (c[1][0][0] + 0.2, "whoosh_down", 0.5, -0.5), (c[1][0][0] + 0.45, "pop", 0.7, -0.4),
           (c[1][1][0] + 0.1, "whoosh_down", 0.5, 0.5), (c[1][1][0] + 0.45, "pop", 0.7, 0.4),
           (s[2] - 0.35, "riser", 0.5, 0), (s[2], "stop", 1.0, 0), (s[2], "impact", 0.7, 0),
           (c[2][1][0] - 0.05, "whoosh", 0.6, 0.4),
           (c[2][2][0], "impact", 0.6, 0), (c[2][2][0] + 0.3, "pop", 0.8, 0.3),
           (s[3] - 0.2, "whoosh", 0.8, 0), (s[3] + 0.05, "click", 0.7, 0)]
    k0, k1, k2 = c[3][0][0], c[3][1][0], c[3][2][0]
    for tt in (k0 + 0.6 * (k1 - k0), k1 + 0.05, k1 + 0.55 * (k2 - k1)):
        ev += [(tt, "whoosh_down", 0.45, 0.5), (tt + 0.3, "pop", 0.8, 0)]
    ev += [(k2, "ding", 0.6, 0),
           (s[4] - 0.2, "whoosh", 0.8, 0), (s[4], "impact", 0.8, 0),
           (c[4][1][0], "cash", 0.8, 0),
           (c[4][2][0] - 0.1, "whoosh", 0.5, 0), (c[4][2][0] + 0.15, "pop", 0.7, -0.4),
           (c[4][2][0] + 0.45, "pop", 0.7, 0.4),
           (s[5] - 0.6, "riser", 0.6, 0), (s[5] - 0.15, "whoosh", 0.8, 0),
           (c[5][1][0], "impact", 0.9, 0), (c[5][1][0] + 0.45, "pop", 0.8, 0),
           (c[5][1][0] + 0.8, "click", 0.6, 0),
           (c[5][2][0] - 0.3, "pop", 0.8, 0.3), (tl["total"] - 1.6, "ding", 0.55, 0)]
    return ev
