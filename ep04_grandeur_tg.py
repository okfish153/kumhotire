"""EP04 그랜저 TG 1분 쇼츠 — 전성기의 문을 열다 (대본 docs/ep04_grandeur_tg_script.md)

목소리: 구글 클라우드 TTS(ko-KR-Chirp3-HD-Algenib), 문장마다 assets/voice/ep04/line_XX.wav
        (python3 tools/tts_lines.py docs/ep04_grandeur_tg_script.md assets/voice/ep04)
틀(타임라인·렌더·자막·차형)은 ep03_grandeur_xg.py를 그대로 쓰고, 이 파일은 장면과 효과음만 정한다.
사용법: python3 ep04_grandeur_tg.py [--preview 1 5 9]
"""
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

import audio as A
import ep_grandeur2 as G
from ep_grandeur2 import CREAM, AMBER, RED, INK, put_card, shade_card, stamp, option_chip, jolt, retro_bgm, stamp_sfx, tick_sfx
from video import W, YEL, WHITE, prog, out_cubic, out_back, in_out, clamp, text_img, box, compose, paste
import ep02_new_grandeur as E2
import ep03_grandeur_xg as E3
from ep02_new_grandeur import big, label, bubble, caption

ROOT = os.path.dirname(os.path.abspath(__file__))
TITLE = ("*전성기*의 문을 열다", "출시 첫날 *1만 1,362대* 계약")
CAPS = [
    ["출시 첫날,", "*1만 1,362대*가 계약됐습니다"],
    ["2005년, *그랜저 TG*"],
    ["근데 *진짜 기록*은,", "그해 *겨울*에 나와요"],
    ["하루 계약으로는", "*승용차 사상 최고* 기록이었죠"],
    ["자, 퀴즈!", "출시하고 *8영업일* 동안,", "몇 대나 계약됐을까요?", "*하나*", "하나, *둘*", "하나, 둘, *셋!*"],
    ["정답, *1만 5,287대*"],
    ["그 시절엔 말이죠,", "*청계천*이 다시 흐르기 시작한 해였어요"],
    ["그리고 그해 *12월*, 한 달에 *1만 236대*", "그랜저 처음으로 *한 달 1만 대*를 넘었습니다"],
    ["회장님 차에서, *누구나 타고 싶은 차*로", "그랜저 *전성기*의 문이 열린 거죠"],
    ["그리고 이 차, 단종을 앞둔 *2009년*에도", "*두 번이나* 한 달 1만 대를 넘겼어요"],
    ["근데 이 모든 기록의", "시작이 *바로*,"],
]
MOTIONS = ["shock", "nod", "secret", "jump", ["talk", "think", "think"], "cheer", "talk", ["shock", "key_spin"],
           ["cheer", "nod"], ["talk", "shock"], ["think", "secret"]]
PHOTOS = {
    "front": ("grandeur_tg_black_front_damianboh.jpg", (0, 0, 1280, 960), (330, 630, 600, 720),
              "사진: Damian B Oh · CC BY-SA 4.0 · Wikimedia Commons (크롭·번호판 흐림)"),
    "side": ("grandeur_tg_black_side_benespit.jpg", (0, 0, 1280, 908), (1140, 560, 1230, 650),
             "사진: Benespit · CC BY-SA 4.0 · Wikimedia Commons (크롭·번호판 흐림)"),
    "silver": ("grandeur_tg_silver_bus_damianboh.jpg", (0, 150, 1280, 960), (1010, 550, 1130, 620),
               "사진: Damian B Oh · CC BY-SA 4.0 · Wikimedia Commons (크롭·번호판 흐림)"),
}

# ep03 틀에 EP04 내용을 끼운다
E3.VOICE_DIR = os.path.join(ROOT, "assets", "voice", "ep04")
E3.BUILD = os.path.join(ROOT, "build", "ep04_video")
E3.OUT = os.path.join(ROOT, "output", "ep04_grandeur_tg_1min.mp4")
E3.CAPS = E2.CAPS = CAPS
E3.MOTIONS = E2.MOTIONS = MOTIONS
E2.TITLE = TITLE
E3.PHOTOS = PHOTOS
E3.COUNT_AFTER = 5                           # 5번 퀴즈 뒤 하나, 둘, 셋
TL = E2.TL
Ls, Le, chunk_start, xcard = E2.Ls, E2.Le, E2.chunk_start, E3.xcard


# ------------------------------------------------------------------ 화면 부품
@lru_cache(None)
def count_badge(n, w=820):
    return compose((box(w, 300, 40, (20, 20, 22, 225), YEL, 6, True), 0, 0),
                   (text_img("출시 첫날 계약 (사전 예약 포함)", 40, CREAM, "Bold", shadow=0), 0, -88),
                   (text_img(f"{n:,}대", 150, YEL, "Black", stroke=6, sfill=(0, 0, 0), shadow=0), 0, 32))


def hook(c, t, back=1.0):
    """1번(그리고 끝에서 돌아오는) 첫 화면: 검정 TG 정면 + 첫날 계약 대수"""
    put_card(c, xcard("front", 1.0 + 0.04 * in_out(prog(t, 0, 3)), 0.5, 0.45))
    shade_card(c, 0.3)
    a = clamp(back)
    if a > 0:
        pulse = 1 + 0.03 * math.sin(t * 7) * (t < 2.5)
        paste(c, count_badge(11362), W / 2, 1085, 0.92 * pulse, -2, a)


@lru_cache(None)
def snow(seed=3, n=46):
    rng = np.random.default_rng(seed)
    return [(rng.uniform(60, 1020), rng.uniform(0, 1), rng.uniform(5, 13), rng.uniform(40, 90)) for _ in range(n)]


def stream(c, t, y0=900, a=1.0):
    d = ImageDraw.Draw(c)
    for k in range(6):
        pts = [(x, y0 + k * 46 + 16 * math.sin(x / 70 + t * 3 + k)) for x in range(60, 1021, 20)]
        d.line(pts, fill=(80 + k * 15, 150 + k * 12, 220), width=10)


@lru_cache(None)
def calendar(w=360):
    h = int(w * 1.05)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 26, fill=(250, 246, 236), outline=INK, width=5)
    d.rounded_rectangle((0, 0, w - 1, 110), 26, fill=RED)
    d.rectangle((0, 70, w - 1, 110), fill=RED)
    t = text_img("2005", 48, WHITE, "Black", shadow=0)
    im.alpha_composite(t, ((w - t.width) // 2, 55 - t.height // 2))
    t = text_img("12월", 120, INK, "Black", shadow=0)
    im.alpha_composite(t, ((w - t.width) // 2, 110 + (h - 110 - t.height) // 2))
    return im


def doors(c, p, y=850, w=820, h=620):
    """가운데가 갈라지며 열리는 문, 뒤에서 빛"""
    x0, y0 = W / 2 - w / 2, y - h / 2
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for k in range(12):
        r = 1 - k / 12
        gd.rectangle((w / 2 - w / 2 * p * r - 10, 0, w / 2 + w / 2 * p * r + 10, h), fill=(255, 214, 0, int(40 + 16 * k)))
    c.alpha_composite(glow, (int(x0), int(y0)))
    d = ImageDraw.Draw(c)
    half = w / 2 * (1 - p)
    for side in (-1, 1):
        xa = W / 2 - half if side < 0 else W / 2
        d.rectangle((xa if side > 0 else x0 + (w / 2 - half) * 0, y0, (W / 2) if side < 0 else W / 2 + half, y0 + h),
                    fill=None)
    # 왼쪽 문
    d.rectangle((x0, y0, x0 + half, y0 + h), fill=(70, 46, 30), outline=INK, width=6)
    d.rectangle((x0 + w - half, y0, x0 + w, y0 + h), fill=(70, 46, 30), outline=INK, width=6)
    if half > 30:
        d.ellipse((x0 + half - 40, y - 14, x0 + half - 12, y + 14), fill=AMBER)
        d.ellipse((x0 + w - half + 12, y - 14, x0 + w - half + 40, y + 14), fill=AMBER)
    d.rectangle((x0 - 20, y0 - 20, x0 + w + 20, y0 + h + 20), outline=CREAM, width=10)


# ------------------------------------------------------------------ 장면
def frame(i):
    t = i / E3.FPS
    c = E2.title_band().copy()
    cred = PHOTOS["front"][3]
    if t < Ls(2) - 0.05:                                        # 1 출시 첫날 11,362대
        hook(c, t)
    elif t < Ls(3) - 0.05:                                      # 2 2005 그랜저 TG
        lt = t - Ls(2)
        cred = PHOTOS["side"][3]
        put_card(c, xcard("side", 1.15 - 0.12 * out_cubic(prog(lt, 0, 1.2)), 0.5, 0.5))
        big(c, "2005 그랜저 TG", Ls(2) + 0.15, t, 1130, 100, YEL, x=W / 2 - 60)
    elif t < Ls(4) - 0.05:                                      # 3 진짜 기록은 그해 겨울
        lt = t - Ls(3)
        cred = PHOTOS["silver"][3]
        put_card(c, xcard("silver", 1.05, 0.6, 0.5))
        shade_card(c, 0.62)
        for (x, ph, r, sp) in snow():
            y = 480 + ((ph * 860 + lt * sp * 3) % 860)
            ImageDraw.Draw(c).ellipse((x - r, y - r, x + r, y + r), fill=(245, 248, 255))
        big(c, "그해 겨울…?", chunk_start(3, 1), t, 860, 140, YEL, -3, x=W / 2 - 40)
    elif t < Ls(5) - 0.05:                                      # 4 승용차 사상 최고
        lt = t - Ls(4)
        dx, dy = jolt(t, chunk_start(4, 1), 20)
        put_card(c, xcard("front", 1.12, 0.5, 0.4), dx=dx, dy=dy)
        shade_card(c, 0.68)
        paste(c, count_badge(11362), W / 2, 760, 0.7, -2)
        ps = prog(t, chunk_start(4, 1) + 0.05, 0.16)
        if ps > 0:
            sc = 2.2 - 1.2 * ps
            paste(c, box(620, 150, 24, (250, 246, 236, 235), shadow=True), W / 2 - 40, 1030, sc, -6, clamp(ps * 3))
            paste(c, stamp("승용차 사상 최고", 64), W / 2 - 40, 1030, sc, -6, clamp(ps * 3))
        paste(c, text_img("하루 계약 기준 · 한국일보 2005-05-29 보도", 32, CREAM, "Bold", stroke=4, sfill=(0, 0, 0)),
              W / 2 - 40, 1180, 1, 0, prog(t, chunk_start(4, 1) + 0.4, 0.3))
    elif t < Ls(6) - 0.05:                                      # 5 퀴즈
        lt = t - Ls(5)
        cred = None
        G.panel(c, (30, 30, 34))
        paste(c, label("자, 퀴즈!", 420, RED, WHITE, 70), W / 2, 560, out_back(prog(lt, 0, 0.25)) + 0.001)
        paste(c, text_img("출시하고 8영업일 동안 계약은?", 50, CREAM, "Black", stroke=5, sfill=(0, 0, 0)),
              W / 2, 680, 1, 0, clamp((t - chunk_start(5, 1)) * 4))
        beat = E3.countdown(c, t) or 1
        for k, txt in enumerate(["5천 대", "1만 대", "1만 5천 대"]):
            pk = out_back(prog(t, chunk_start(5, 2) + 0.12 * k, 0.25))
            paste(c, option_chip(str(k + 1), txt), W / 2 - 80, 800 + k * 135, (pk + 0.001) * beat * 0.95, 0,
                  clamp(pk * 2))
    elif t < Ls(7) - 0.05:                                      # 6 정답 15,287대
        lt = t - Ls(6)
        cred = None
        G.panel(c, (30, 30, 34))
        hit = Ls(6) + 0.35
        for k, txt in enumerate(["5천 대", "1만 대", "1만 5천 대"]):
            st = 0 if t < hit else (1 if k == 2 else 2)
            paste(c, option_chip(str(k + 1), txt, st), W / 2 - 80, 600 + k * 130, 0.85)
        dx, dy = jolt(t, hit, 18)
        v = int(15287 * out_cubic(prog(t, hit - 0.2, 0.8)))
        paste(c, text_img(f"{v:,}대", 130, YEL, "Black", stroke=6, sfill=(0, 0, 0), shadow=8), W / 2 - 60 + dx,
              1030 + dy, 1, 0, clamp((t - hit + 0.2) * 4))
        paste(c, text_img("5월 18일 출시 → 27일까지 · 한국일보 2005-05-29", 32, CREAM, "Bold", stroke=4,
                          sfill=(0, 0, 0)), W / 2 - 60, 1150, 1, 0, prog(t, hit + 0.6, 0.3))
    elif t < Ls(8) - 0.05:                                      # 7 청계천
        lt = t - Ls(7)
        cred = None
        G.panel(c, (26, 34, 40))
        paste(c, label("2005", 300, AMBER, INK, 72), W / 2, 580, out_back(prog(lt, 0, 0.25)) + 0.001)
        stream(c, t, 860)
        pc = out_back(prog(t, chunk_start(7, 1) + 0.1, 0.3))
        paste(c, label("청계천 복원 개통 · 10월", 640, (250, 246, 236), INK, 54), W / 2 - 40, 1200, pc + 0.001, -2,
              clamp(pc * 2))
    elif t < Ls(9) - 0.05:                                      # 8 12월 10,236대
        lt = t - Ls(8)
        cred = None
        G.panel(c, (30, 30, 34))
        paste(c, calendar(), 300, 760, out_back(prog(lt, 0, 0.3)) + 0.001, -4)
        base_y, x = 1180, 760
        hgt = int(560 * out_cubic(prog(t, Ls(8) + 0.3, 1.4)))
        ImageDraw.Draw(c).rectangle((x - 110, base_y - hgt, x + 110, base_y), fill=AMBER)
        ImageDraw.Draw(c).line((x - 190, base_y - 560 * 0.977, x + 190, base_y - 560 * 0.977), fill=RED, width=6)
        paste(c, text_img("1만 대 선", 36, RED, "Black", stroke=4, sfill=(255, 255, 255)), x - 210, base_y - 560 * 0.977 + 34)
        n = int(10236 * hgt / 560)
        paste(c, text_img(f"{n:,}대", 70, WHITE, "Black", stroke=6, sfill=(0, 0, 0)), x, base_y - hgt - 50)
        ps = prog(t, chunk_start(8, 1) + 0.05, 0.16)
        if ps > 0:
            paste(c, stamp("그랜저 첫 월 1만 대", 50), 330, 1090, 2.2 - 1.2 * ps, -6, clamp(ps * 3))
        paste(c, text_img("판매 기준 · 아시아경제·뉴시스 보도", 30, (215, 215, 220), "SemiBold", shadow=2), W / 2,
              1290)
    elif t < Ls(10) - 0.05:                                     # 9 전성기의 문
        lt = t - Ls(9)
        cred = None
        G.panel(c, (22, 20, 18))
        p = in_out(prog(t, chunk_start(9, 1) - 0.2, 0.9))
        doors(c, p)
        if p > 0.3:
            paste(c, text_img("그랜저 전성기", 110, INK, "Black", stroke=6, sfill=(255, 240, 180)), W / 2, 850, 1, 0,
                  clamp((p - 0.3) * 2))
        paste(c, label("회장님 차 → 누구나 타고 싶은 차", 820, (250, 246, 236), INK, 48), W / 2, 1250, 1, 0,
              clamp(lt * 4))
    elif t < Ls(11) - 0.05:                                     # 10 2009년에도 두 번 월 1만 대
        lt = t - Ls(10)
        cred = None
        G.panel(c, (30, 30, 34))
        paste(c, label("단종 앞둔 2009년", 560, (250, 246, 236), INK, 56), W / 2, 560, out_back(prog(lt, 0, 0.25)) + 0.001)
        base_y, top = 1180, 470
        line_y = base_y - top * 10000 / 11156
        d = ImageDraw.Draw(c)
        d.line((170, line_y, 910, line_y), fill=RED, width=6)
        paste(c, text_img("1만 대 선", 34, RED, "Black", stroke=4, sfill=(255, 255, 255)), 230, line_y - 28)
        for k, (mon, v, x) in enumerate([("5월", 10642, 420), ("6월", 11156, 680)]):
            pk = out_cubic(prog(t, Ls(10) + 0.4 + 0.4 * k, 0.9))
            hgt = int(top * v / 11156 * pk)
            d.rectangle((x - 90, base_y - hgt, x + 90, base_y), fill=AMBER)
            paste(c, text_img(f"{int(round(v * pk)):,}대", 52, WHITE, "Black", stroke=5, sfill=(0, 0, 0)),
                  x, base_y - hgt - 40)
            paste(c, text_img(mon, 44, CREAM, "Black", shadow=0), x, base_y + 40)
        ps = prog(t, chunk_start(10, 1) + 0.5, 0.16)
        if ps > 0:
            sc = 2.2 - 1.2 * ps
            paste(c, box(440, 150, 24, (250, 246, 236, 235), shadow=True), W / 2 - 10, 1000, sc, -8, clamp(ps * 3))
            paste(c, stamp("또 1만 대!", 64), W / 2 - 10, 1000, sc, -8, clamp(ps * 3))
        paste(c, text_img("판매 기준 · 뉴시스 보도", 30, (215, 215, 220), "SemiBold", shadow=2), W / 2, 1290)
    else:                                                       # 11 첫 화면으로 돌아감 ("딱 하루")
        back = in_out(prog(t, Ls(11) + 0.1, 0.9))
        hook(c, 0.0, back)
        shade_card(c, 0.3 * (1 - back))
    if cred:
        E2.credit_line(c, cred)
    E3.char_react(c, t)
    caption(c, t)
    ImageDraw.Draw(c).rectangle((0, 0, int(W * t / TL["total"]), 7), fill=AMBER)
    return c.convert("RGB")


# ------------------------------------------------------------------ 오디오
def build_audio(voice):
    sr = A.SR
    n = int(TL["total"] * sr)
    v = np.zeros(n)
    v[:len(voice)] = voice[:n]
    v = v / max(1e-9, np.abs(v).max()) * 0.92
    music = retro_bgm(TL["total"] + 1.0)[:n]
    act = np.convolve((np.abs(v) > 0.02).astype(float), np.ones(int(0.3 * sr)) / int(0.3 * sr), mode="same")
    music = music * (1 - 0.55 * np.clip(act * 4, 0, 1))[:, None] * 0.7
    ev = [(0.05, A.sfx_impact(), 0.5), (Ls(2), A.sfx_whoosh(0.35), 0.4), (chunk_start(3, 1), A.sfx_riser(0.8), 0.35),
          (chunk_start(4, 1) + 0.05, stamp_sfx(), 0.8), (Ls(5), A.sfx_ding(), 0.5)]
    ev += [(chunk_start(5, 2) + 0.12 * k, A.sfx_pop(), 0.5) for k in range(3)]
    ev += [(st - 0.05, tick_sfx(), 0.9) for st, _ in TL["count"]]
    hit = Ls(6) + 0.35
    ev += [(hit - 0.2 + 0.8 * k / 12, tick_sfx(), 0.5) for k in range(12)]
    ev += [(hit, A.sfx_ding(), 0.7), (Ls(7), A.sfx_whoosh(0.35), 0.4), (Ls(8), A.sfx_whoosh(0.35), 0.4)]
    ev += [(Ls(8) + 0.3 + 1.4 * k / 14, tick_sfx(), 0.5) for k in range(14)]
    ev += [(chunk_start(8, 1) + 0.05, stamp_sfx(), 0.8), (chunk_start(9, 1) - 0.2, A.sfx_riser(0.9), 0.4),
           (chunk_start(9, 1) + 0.6, A.sfx_impact(), 0.5), (Ls(10), A.sfx_whoosh(0.35), 0.4),
           (chunk_start(10, 1) + 0.5, stamp_sfx(), 0.8), (Ls(11) + 0.1, A.sfx_riser(0.8), 0.3),
           (chunk_start(11, 1), A.sfx_impact(), 0.4)]
    fx = np.zeros(n)
    for t0, snd, g in ev:
        i = int(max(0, t0) * sr)
        if i < n:
            snd = snd[: n - i]
            fx[i:i + len(snd)] += snd * g
    mix = music + (v + fx * 0.5)[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    os.makedirs(E3.BUILD, exist_ok=True)
    p = os.path.join(E3.BUILD, "mix.wav")
    A.write_wav(p, mix)
    return p


E3.frame = frame
E3.build_audio = build_audio

if __name__ == "__main__":
    E3.main()
