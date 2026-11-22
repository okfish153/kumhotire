"""EP01 각그랜저 1분 쇼츠 (사용자 녹음, 대본 docs/ep01_gak_grandeur_script.md 초안 2)

목소리: assets/voice/ep01/ep01_take1.aac → tools/clap_cut.py 로 13문장 정리 (손뼉 없음)
화면: 위 고정 2줄 제목 / 가운데 실사진 카드와 그래픽 / 아래 큰 자막 / 오른쪽 아래 차형 반응
- 시리즈 번호·다음 편 예고 없음. 끝 문장이 첫 문장으로 이어지도록 마지막 화면을 첫 화면과 맞춤.
사용법: python3 ep01_gak_grandeur.py [--preview 1 5 9]
"""
import argparse
import json
import math
import os
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

import audio as A
import ep_grandeur2 as G
from ep_grandeur2 import (CREAM, AMBER, RED, INK, CARD_W, CARD_H, CARD_Y, MAIN_BOX, photo, card, put_card,
                          shade_card, memo_card, option_chip, stamp, bowl, won_bill, rich_img, jolt,
                          retro_bgm, calc_sfx, stamp_sfx, tick_sfx, credit)
from video import (W, H, YEL, WHITE, prog, out_cubic, out_back, in_out, clamp, text_img, box, compose, paste)

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "assets", "voice", "ep01", "ep01_take1.aac")
SCRIPT = os.path.join(ROOT, "docs", "ep01_gak_grandeur_script.md")
VOICE_DIR = os.path.join(ROOT, "build", "ep01_take1")
BUILD = os.path.join(ROOT, "build", "ep01_video")
OUT = os.path.join(ROOT, "output", "ep01_gak_grandeur_1min.mp4")
CUT_ARGS = ["--no-clap", "--tempo", "1.15", "--gap", "0.3", "--inner-pause", "0.25"]
TITLE = ("짜장면 *28,000그릇* 값?", "지금 짜장면 값으론 *2억!*")
FPS = 30
TAIL = 0.35
CHAR_PATH = os.path.join(ROOT, "assets", "character", "chahyung_base.png")
OPERA = (1040, 205)          # 원본 사진에서 오페라 글라스(C필러 작은 창) 중심

# 문장별 아래 자막 조각 (*노란 강조*)
CAPS = [
    ["짜장면 *2만 8천 그릇*"],
    ["그게 이 차 *한 대 값*이었습니다"],
    ["지금 짜장면 값으로 치면,", "*2억 원*이 넘어요"],
    ["근데 이 차엔", "*숨은 창*이 하나 있어요"],
    ["자, 퀴즈!", "*1986년*, 이 차는 얼마였을까요?"],
    ["정답, *1,690만 원*", "짜장면이 *600원*이던 시절이죠"],
    ["그 시절엔 말이죠,", "대기업 신입 기본급이 *31만 원*"],
    ["한 푼도 안 쓰고 *4년 반*", "…짜장면도 못 먹고요"],
    ["네모 반듯한 차체에 반짝이는 크롬", "그래서 *각그랜저*"],
    ["다들 이 차를", "*회장님 차*로 기억하시죠"],
    ["아까 그 숨은 창,", "바로 이 *오페라 글라스*", "뒷자리 손님을 위한 창이었죠"],
    ["여러분 동네엔", "누구네 *각그랜저*가 있었나요?", "댓글로 알려 주세요"],
    ["구독해 두시면", "옛날 차 이야기, 계속 들려드릴게요", "그럼 이 차 값이 얼마였냐면요,"],
]
TL = {}


# ------------------------------------------------------------------ 목소리·타임라인
def load_timeline():
    rep = os.path.join(VOICE_DIR, "report.json")
    wav = os.path.join(VOICE_DIR, "voice_clean.wav")
    if not (os.path.exists(rep) and os.path.exists(wav)):
        subprocess.check_call(["python3", os.path.join(ROOT, "tools", "clap_cut.py"), SRC, "--script", SCRIPT,
                               "--out", VOICE_DIR] + CUT_ARGS)
    r = json.load(open(rep, encoding="utf-8"))
    lines = [(x["start"], x["end"]) for x in r["kept_timeline"]]
    assert len(lines) == len(CAPS), f"문장 {len(lines)}개 ≠ 자막 {len(CAPS)}개"
    chunks = []
    for (st, en), caps in zip(lines, CAPS):
        w = [max(4, len(c.replace("*", ""))) for c in caps]
        acc = st
        for c, k in zip(caps, w):
            d = (en - st) * k / sum(w)
            chunks.append((acc, acc + d, c))
            acc += d
    voice = A.read_wav(wav)
    total = round(len(voice) / A.SR + TAIL, 2)
    TL.update(lines=lines, chunks=chunks, total=total)
    return voice


def Ls(i):
    """i번 문장(1부터)의 시작"""
    return TL["lines"][i - 1][0]


def Le(i):
    return TL["lines"][i - 1][1]


def chunk_start(i, k):
    caps_before = sum(len(c) for c in CAPS[:i - 1])
    return TL["chunks"][caps_before + k][0]


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


def to_screen(px, py, zoom=1.0, fx=0.5, fy=0.5):
    """원본 사진 좌표 → 화면 좌표 (card()/cover()와 같은 계산)"""
    bl, bt, br, bb = MAIN_BOX
    bw, bh = br - bl, bb - bt
    s = max(CARD_W / bw, CARD_H / bh) * zoom
    cw, ch = CARD_W / s, CARD_H / s
    l = bl + clamp(fx * bw - cw / 2, 0, bw - cw)
    t = bt + clamp(fy * bh - ch / 2, 0, bh - ch)
    return W / 2 - CARD_W / 2 + (px - l) * s, CARD_Y - CARD_H / 2 + (py - t) * s


def big(c, txt, t0, t, y=700, size=110, color=YEL, rot=0, x=W / 2):
    p = out_back(prog(t, t0, 0.18), 2.2)
    if p > 0:
        paste(c, text_img(txt, size, color, "Black", stroke=8, sfill=(0, 0, 0), shadow=8), x, y, 1.6 - 0.6 * p, rot,
              clamp(p * 2))


def label(txt, w, fill=RED, fg=WHITE, size=72):
    return compose((box(w, int(size * 1.7), 30, fill, CREAM, 5, True), 0, 0),
                   (text_img(txt, size, fg, "Black", shadow=0), 0, -4))


@lru_cache(None)
def ring(d=300, color=YEL, width=12):
    im = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((width, width, d - width, d - width), outline=color, width=width)
    return im


@lru_cache(None)
def chahyung(h=300):
    im = Image.open(CHAR_PATH).convert("RGBA")
    bb = im.getbbox()
    im = im.crop(bb)
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)


@lru_cache(None)
def bubble(txt, w=760):
    b = box(w, 170, 60, (250, 246, 236), INK, 6, True)
    tail = Image.new("RGBA", (90, 70), (0, 0, 0, 0))
    ImageDraw.Draw(tail).polygon([(0, 0), (90, 0), (70, 70)], fill=(250, 246, 236), outline=INK)
    return compose((b, 0, 0), (tail, w // 2 - 150, 112), (text_img(txt, 62, INK, "Black", shadow=0), 0, -4))


def caption(c, t):
    for st, en, cap in TL["chunks"]:
        if st - 0.05 <= t < en + 0.12:
            p = out_back(prog(t, st - 0.05, 0.14), 2.2)
            im = rich_img(cap, 84, 10)
            if im.width > 1040:
                im = im.resize((1040, int(im.height * 1040 / im.width)), Image.BICUBIC)
            paste(c, im, W / 2, 1480, 0.9 + 0.1 * p, 0, clamp(p * 1.6))
            return


def char_react(c, t):
    """오른쪽 아래 구석의 차형. 반응 순간 통통 튐."""
    p = 1.0                                     # 처음부터 계속 (반복 재생 때 끊기지 않게)
    hop = 0.0
    for i in (2, 6, 8, 10, 12):
        q = prog(t, Ls(i) + 0.05, 0.35)
        if 0 < q < 1:
            hop = max(hop, math.sin(q * math.pi) * 38)
    bob = 4 * math.sin(t * 3.2)
    paste(c, chahyung(), 950, 1255 - hop + bob + 60 * (1 - p), 1.0, -4 * math.sin(t * 1.7), clamp(p * 2))


def photo_credit(c):
    im = credit()
    paste(c, im, 40 + im.width / 2 * 0.9, 1362, 0.9)


# ------------------------------------------------------------------ 장면
def frame(i):
    t = i / FPS
    c = title_band().copy()
    show_credit = True
    if t < Ls(2) - 0.05:                                         # 1 짜장면 2만 8천 그릇
        lt = t
        put_card(c, card(photo(), 1.0 + 0.06 * in_out(prog(t, 0, Ls(2))), 0.45, 0.55))
        shade_card(c, 0.35 * prog(lt, 0.1, 0.4))
        rng = np.random.default_rng(4)
        for k in range(50):
            x = 140 + rng.random() * 800
            y0 = 560 + rng.random() * 700
            p = out_cubic(prog(lt, 0.1 + rng.random() * 1.6, 0.35))
            if p > 0:
                paste(c, bowl(), x, 520 + (y0 - 520) * p, 1, (k * 37) % 30 - 15, clamp(p * 3))
        cnt = int(28_000 * out_cubic(prog(lt, 0.15, max(0.6, Le(1) - 0.3))))
        paste(c, label(f"짜장면 {cnt:,}그릇", 760, size=80), W / 2, 900, 1, -2, clamp((lt - 0.2) * 5))
    elif t < Ls(3) - 0.05:                                       # 2 = 이 차 한 대 값
        dx, dy = jolt(t, Ls(2), 22)
        put_card(c, card(photo(), 1.08, 0.45, 0.55), dx=dx, dy=dy)
        paste(c, label("짜장면 28,000그릇", 700, size=70), W / 2, 720, 0.9)
        big(c, "= 이 차 한 대 값", Ls(2) + 0.1, t, 1120, 96, YEL)
    elif t < Ls(4) - 0.05:                                       # 3 지금 값으로 2억
        lt = t - Ls(3)
        put_card(c, card(photo(), 1.1, 0.45, 0.55))
        shade_card(c, 0.62)
        paste(c, text_img("지금 짜장면 값으로", 64, CREAM, "Black", stroke=5, sfill=(0, 0, 0), shadow=4), W / 2, 690)
        val = 2.12 * out_cubic(prog(t, chunk_start(3, 1) - 0.3, 0.6))
        txt = "약 2억 1천만 원" if val >= 2.11 else f"약 {val:.1f}억 원"
        sc = 1.0 + 0.12 * (1 - out_cubic(prog(t, chunk_start(3, 1) + 0.3, 0.25)))
        paste(c, text_img(txt, 128, YEL, "Black", stroke=6, sfill=(0, 0, 0), shadow=10), W / 2, 880, sc)
        p2 = prog(lt, 0.4, 0.3)
        paste(c, text_img("2025년 서울 짜장면 평균 7,551원 × 28,167그릇", 38, CREAM, "Bold", stroke=4,
                          sfill=(0, 0, 0), shadow=3), W / 2, 1040, 1, 0, p2)
        paste(c, text_img("짜장면 값 환산 · 물가 환산 아님 · 한국소비자원 참가격", 32, (215, 205, 190), "SemiBold",
                          stroke=3, sfill=(0, 0, 0), shadow=3), W / 2, 1100, 1, 0, p2)
    elif t < Ls(5) - 0.05:                                       # 4 숨은 창?
        lt = t - Ls(4)
        put_card(c, card(photo(), 1.0, 0.45, 0.55))
        x, y = to_screen(*OPERA, 1.0, 0.45, 0.55)
        p = out_back(prog(t, chunk_start(4, 1), 0.3))
        pulse = 1 + 0.06 * math.sin(lt * 9)
        paste(c, ring(230), x, y, p * pulse, 0, clamp(p * 2))
        paste(c, text_img("?", 150, YEL, "Black", stroke=8, sfill=(0, 0, 0), shadow=8), x, y - 10,
              p * pulse, 8 * math.sin(lt * 4), clamp(p * 2))
        big(c, "숨은 창 하나!", chunk_start(4, 1) + 0.1, t, 1180, 88, YEL)
    elif t < Ls(6) - 0.05:                                       # 5 퀴즈
        lt = t - Ls(5)
        put_card(c, card(photo(), 1.04, 0.45, 0.55))
        shade_card(c, 0.5)
        big(c, "1986년, 이 차 값은?", Ls(5) + 0.05, t, 640, 84, YEL)
        for k, (no, txt) in enumerate([("1", "169만 원"), ("2", "1,690만 원"), ("3", "1억 원")]):
            pk = out_back(prog(t, chunk_start(5, 1) + 0.2 + 0.3 * k, 0.25))
            paste(c, option_chip(no, txt), W / 2, 850 + k * 150, pk, 0, clamp(pk * 1.4))
    elif t < Ls(7) - 0.05:                                       # 6 정답 1,690만 원
        hit = Ls(6) + 0.25
        dx, dy = jolt(t, hit, 24)
        put_card(c, card(photo(), 1.08, 0.45, 0.55), dx=dx, dy=dy)
        shade_card(c, 0.62)
        val = int(16_900_000 * out_cubic(clamp((t - Ls(6)) / 0.3)))
        txt = "1,690만 원" if t >= hit else f"{val // 10000:,}만 원"
        sc = 1.0 + 0.15 * (1 - out_cubic(prog(t, hit, 0.25)))
        paste(c, text_img(txt, 160, YEL, "Black", stroke=6, sfill=(0, 0, 0), shadow=10), W / 2 + dx, 760 + dy, sc)
        ps = prog(t, hit + 0.2, 0.16)
        if ps > 0:
            paste(c, stamp("정답", 84), W / 2 + 300, 900, 2.2 - 1.2 * ps, 0, clamp(ps * 3))
        paste(c, text_img("1986년 출시 초기 가격 · 오토뷰 보도", 38, CREAM, "Bold", stroke=4, sfill=(0, 0, 0),
                          shadow=3), W / 2, 960, 1, 0, prog(t, hit + 0.3, 0.25))
        pm = out_back(prog(t, chunk_start(6, 1), 0.3))
        paste(c, memo_card(), 330, 1140, 0.75 * pm, 0, clamp(pm * 1.5))
    elif t < Ls(9) - 0.05:                                       # 7·8 월급 31만 원 × 54칸
        show_credit = False
        lt = t - Ls(7)
        G.panel(c, (32, 38, 34))
        head = compose((box(800, 110, 26, (250, 246, 236), shadow=False), 0, 0),
                       (text_img("1986 대기업 신입 기본급 월 31만 원", 44, INK, "Black", shadow=0), 0, -3))
        paste(c, head, W / 2, 560, 1, 0, clamp(lt * 5))
        n = int(54 * out_cubic(prog(t, Ls(8) - 0.2, max(0.8, chunk_start(8, 1) - Ls(8)))))
        cols, dxs, dys = 9, 100, 66
        x0, y0 = W / 2 - (cols - 1) * dxs / 2, 680
        for k in range(54):
            r_, q = divmod(k, cols)
            x, y = x0 + q * dxs, y0 + r_ * dys
            ImageDraw.Draw(c).rounded_rectangle((x - 44, y - 26, x + 44, y + 26), 8, outline=(110, 130, 110), width=2)
            if k < n:
                paste(c, won_bill(), x, y, 0.58)
        if t >= Ls(8):
            if n >= 54:
                ps = out_back(prog(t, chunk_start(8, 1) - 0.25, 0.25))
                up = 330 * in_out(prog(t, chunk_start(8, 1) + 0.05, 0.3))
                paste(c, label("꼬박 4년 반!", 600, size=80), W / 2, 1140 - up, ps, -2, clamp(ps * 1.5))
            else:
                paste(c, text_img(f"{n}개월", 84, YEL, "Black", stroke=6, sfill=(0, 0, 0), shadow=4), W / 2, 1140)
        paste(c, text_img("1,690만 ÷ 31만 ≈ 54.5개월 · 기본급 기준", 28, (215, 205, 190), "SemiBold", shadow=2),
              W / 2, 1290)
        pj = prog(t, chunk_start(8, 1) + 0.1, 0.3)
        if pj > 0:                                               # …짜장면도 못 먹고요
            bx, by = W / 2, 1110
            paste(c, box(420, 300, 40, (32, 38, 34), shadow=True), bx, by, out_back(pj))
            paste(c, bowl(240), bx, by, out_back(pj))
            q = out_cubic(prog(t, chunk_start(8, 1) + 0.35, 0.2))
            if q > 0:
                d = ImageDraw.Draw(c)
                d.line((bx - 110, by - 110, bx - 110 + 220 * q, by - 110 + 220 * q), fill=RED, width=20)
                d.line((bx + 110, by - 110, bx + 110 - 220 * q, by - 110 + 220 * q), fill=RED, width=20)
    elif t < Ls(10) - 0.05:                                      # 9 크롬 → 각그랜저
        lt = t - Ls(9)
        dur = Le(9) - Ls(9)
        fx = 0.2 + 0.55 * in_out(prog(lt, 0, dur * 0.7))
        put_card(c, card(photo(), 1.9, fx, 0.66))
        sweep = prog(lt, 0.3, 0.9)
        if 0 < sweep < 1:
            lay = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
            xs = int(-200 + (CARD_W + 400) * sweep)
            ImageDraw.Draw(lay).polygon([(xs, 0), (xs + 70, 0), (xs - 130, CARD_H), (xs - 200, CARD_H)],
                                        fill=(255, 255, 255, 70))
            paste(c, lay, W / 2, CARD_Y)
        big(c, "각그랜저", chunk_start(9, 1) + 0.05, t, 1180, 140, YEL, -3)
    elif t < Ls(11) - 0.05:                                      # 10 회장님 차
        dx, dy = jolt(t, chunk_start(10, 1) + 0.1, 18)
        put_card(c, card(photo(0.35), 1.04 + 0.04 * prog(t, Ls(10), 3), 0.45, 0.55), dx=dx, dy=dy)
        ps = prog(t, chunk_start(10, 1) + 0.1, 0.16)
        if ps > 0:
            paste(c, stamp("회장님 차", 96), W / 2, 700, 2.2 - 1.2 * ps, 0, clamp(ps * 3))
    elif t < Ls(12) - 0.05:                                      # 11 오페라 글라스
        lt = t - Ls(11)
        bl, bt, br, bb = MAIN_BOX
        ofx, ofy = (OPERA[0] - bl) / (br - bl), (OPERA[1] - bt) / (bb - bt)
        z = 1.0 + 1.3 * in_out(prog(lt, 0, 0.9))
        fx = 0.45 + (ofx - 0.45) * in_out(prog(lt, 0, 0.9))
        fy = 0.55 + (ofy - 0.55) * in_out(prog(lt, 0, 0.9))
        put_card(c, card(photo(), z, fx, fy))
        x, y = to_screen(*OPERA, z, fx, fy)
        p = out_back(prog(t, chunk_start(11, 1), 0.3))
        paste(c, ring(int(150 * z)), x, y, p, 0, clamp(p * 2))
        pl = out_back(prog(t, chunk_start(11, 1) + 0.2, 0.25))
        paste(c, label("오페라 글라스", 560, YEL, INK, 70), W / 2 - 60, 1150, pl, -2, clamp(pl * 2))
        pd = prog(t, chunk_start(11, 2), 0.25)
        paste(c, text_img("뒷자리 손님을 위한 창 · 출처: 현대자동차그룹", 34, CREAM, "Bold", stroke=4,
                          sfill=(0, 0, 0), shadow=3), W / 2 - 60, 1262, 1, 0, pd)
    elif t < Ls(13) - 0.05:                                      # 12 댓글
        lt = t - Ls(12)
        put_card(c, card(photo(), 1.02, 0.45, 0.55))
        shade_card(c, 0.45)
        pb = out_back(prog(lt, 0.1, 0.3))
        paste(c, bubble("우리 동네 각그랜저는?"), W / 2, 760, pb, 0, clamp(pb * 2))
        pc = out_back(prog(t, chunk_start(12, 2), 0.3))
        paste(c, label("댓글로 알려 주세요", 640, size=60), W / 2, 1000, pc, 0, clamp(pc * 2))
    else:                                                        # 13 구독 → 첫 화면으로
        lt = t - Ls(13)
        back = in_out(prog(t, chunk_start(13, 2), 0.8))
        put_card(c, card(photo(), 1.02 - 0.02 * back, 0.45, 0.55))
        shade_card(c, 0.4 * (1 - back))
        p = out_back(prog(lt, 0.05, 0.3)) * (1 - prog(t, chunk_start(13, 2), 0.3))
        sub = compose((box(420, 130, 65, RED, shadow=True), 0, 0),
                      (text_img("구독", 76, WHITE, "Black", shadow=0), 0, -4))
        paste(c, sub, W / 2, 900, p, 0, clamp(p * 2))
    if show_credit:
        photo_credit(c)
    char_react(c, t)
    caption(c, t)
    ImageDraw.Draw(c).rectangle((0, 0, int(W * t / TL["total"]), 7), fill=AMBER)
    return c.convert("RGB")


# ------------------------------------------------------------------ 오디오
def build_audio(voice):
    sr = A.SR
    n = int(TL["total"] * sr)
    v = np.zeros(n)
    v[:len(voice)] = voice[:n]
    v = v / max(1e-6, np.abs(v).max()) * 0.92
    music = retro_bgm(TL["total"] + 1.0)[:n]
    act = np.convolve((np.abs(v) > 0.02).astype(float), np.ones(int(0.3 * sr)) / int(0.3 * sr), mode="same")
    duck = 1 - 0.55 * np.clip(act * 4, 0, 1)
    music = music * duck[:, None] * 0.7          # 끝은 페이드 없이: 반복 재생 때 끊김 없도록
    ev = []
    rng = np.random.default_rng(9)
    for k in range(10):
        ev.append((0.1 + rng.random() * 1.6, A.sfx_pop(), 0.3))
    ev += [(Ls(2) - 0.02, stamp_sfx(), 0.6), (chunk_start(3, 1) + 0.3, A.sfx_ding(), 0.5),
           (chunk_start(4, 1), A.sfx_pop(), 0.6), (Ls(5) - 0.1, A.sfx_whoosh(0.35), 0.4)]
    for k in range(3):
        ev.append((chunk_start(5, 1) + 0.2 + 0.3 * k, A.sfx_pop(), 0.6))
    hit = Ls(6) + 0.25
    ev += [(hit - 0.02, calc_sfx(), 1.0), (hit + 0.2, stamp_sfx(), 0.8), (Ls(7) - 0.12, A.sfx_whoosh(0.35), 0.4)]
    s8, e8 = Ls(8) - 0.2, chunk_start(8, 1)
    for k in range(0, 54, 3):
        ev.append((s8 + max(0.8, e8 - Ls(8)) * (1 - (1 - k / 54) ** (1 / 3)), tick_sfx(), 0.6))
    ev += [(chunk_start(8, 1) - 0.25, A.sfx_ding(), 0.5), (chunk_start(8, 1) + 0.35, stamp_sfx(), 0.6),
           (Ls(9) + 0.3, A.sfx_whoosh(0.5), 0.35), (chunk_start(10, 1) + 0.1, stamp_sfx(), 0.8),
           (chunk_start(11, 1), A.sfx_pop(), 0.6), (Ls(12) + 0.1, A.sfx_pop(), 0.5),
           (Ls(13) + 0.05, A.sfx_pop(), 0.5)]
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
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", mix,
                           "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                           "-ar", "48000", "-t", f"{TL['total']}", "-movflags", "+faststart", OUT])
    write_srt(OUT.replace(".mp4", ".srt"))
    print("[done]", OUT)


if __name__ == "__main__":
    main()
