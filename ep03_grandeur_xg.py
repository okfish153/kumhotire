"""EP03 그랜저 XG 1분 쇼츠 (대본 docs/ep03_grandeur_xg_script.md)

목소리: 구글 클라우드 TTS(ko-KR-Chirp3-HD-Algenib)로 문장마다 만든 assets/voice/ep03/line_XX.wav를 이어 붙인다.
        파일이 없으면 tools/tts_lines.py로 먼저 만든다.
화면: 위 고정 2줄 제목 / 가운데 실사진 카드와 그래픽 / 아래 큰 자막 / 오른쪽 아래 차형(움직임)
- 시리즈 번호·다음 편 예고 없음. 끝 화면을 첫 화면과 맞춰 반복 재생이 이어지게.
사용법: python3 ep03_grandeur_xg.py [--preview 1 5 9]
"""
import argparse
import math
import os
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import audio as A
from tools.chahyung_motion import Chahyung
import ep_grandeur2 as G
from ep_grandeur2 import (CREAM, AMBER, RED, INK, CARD_W, CARD_H, put_card, shade_card, stamp, option_chip,
                          bowl, rich_img, jolt, retro_bgm, calc_sfx, stamp_sfx, tick_sfx)
from video import (W, H, YEL, WHITE, prog, out_cubic, out_back, in_out, clamp, text_img, box, compose, paste, cover)
import ep02_new_grandeur as E2
from ep02_new_grandeur import big, label, envelope, bubble, caption, write_srt

ROOT = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.path.join(ROOT, "assets", "voice", "ep03")
BUILD = os.path.join(ROOT, "build", "ep03_video")
OUT = os.path.join(ROOT, "output", "ep03_grandeur_xg_1min.mp4")
TITLE = ("회장님 *뒷자리* 차에서", "*내가 직접 모는 차*로?")
FPS = 30
TAIL = 0.2                                   # 끝과 처음 사이를 짧게 (반복 재생이 끊기지 않게)
COUNT_AFTER = 4                              # 이 문장(퀴즈) 뒤에 '하나, 둘, 셋' 카운트다운
COUNT_WORDS = ("하나", "둘", "셋!")
GAP = 0.42                                   # 문장 사이 쉼
IMG = os.path.join(ROOT, "assets", "images")
PHOTOS = {   # 파일, 쓸 영역, 번호판(흐림), 크레딧
    "white": ("grandeur_xg_white_osx.jpg", (0, 60, 1280, 856), (1046, 578, 1162, 652),
              "사진: OSX · 퍼블릭 도메인 · Wikimedia Commons (번호판 흐림)"),
    "rear": ("grandeur_xg_benespit.jpg", (0, 0, 1280, 960), (380, 630, 600, 780),
             "사진: Benespit · CC BY-SA 4.0 · Wikimedia Commons (크롭·번호판 흐림)"),
    "black": ("grandeur_xg_q30_black_damianboh.jpg", (0, 300, 1280, 960), (335, 638, 400, 680),
              "사진: Damian B Oh · CC BY-SA 4.0 · Wikimedia Commons (크롭·번호판 흐림)"),
}

CAPS = [
    ["*회장님 뒷자리* 차가,", "*내가 모는 차*가 됐습니다"],
    ["1998년, *그랜저 XG*"],
    ["근데 이 차,", "*문*을 열면 깜짝 놀라요"],
    ["자, 퀴즈!", "뉴 그랜저 최고급이 *3,490만 원*", "XG는요?", "*하나*", "하나, *둘*", "하나, 둘, *셋!*"],
    ["정답,", "*2,200만~2,700만 원대*", "*700만 원* 가까이 쌌죠"],
    ["그 시절엔 말이죠,", "*외환위기* 한가운데였어요"],
    ["신입 월급마저 *줄던* 해였죠", "…짜장면도 못 먹고요"],
    ["그렇게 *회장님 뒷자리* 차가,", "*내가 운전석*에 앉는 차가 됐죠"],
    ["아까 그 문,", "창틀이 없는 *프레임리스 도어*", "유리만 쏙!"],
    ["그리고 XG는,", "현대가 *직접 개발한 엔진*을 앞세운", "*첫 그랜저*였어요"],
    ["근데 그거 아세요?", "이 *그랜저 XG*부터,"],
]
MOTIONS = [["secret", "key_spin"], "nod", "secret", ["talk", "think", "think"], "jump", "talk", ["awkward", "awkward"],
           ["talk", "key_spin"], ["point_down", "point_down", "cheer"], ["talk", "key_spin", "jump"], ["think", "secret"]]
CHAR_H, CHAR_X, CHAR_FOOT = 300, 950, 1405
TL = E2.TL                                   # ep02 자막·차형 함수가 같은 타임라인을 보게 함
E2.TITLE = TITLE
E2.CAPS = CAPS
E2.MOTIONS = MOTIONS


# ------------------------------------------------------------------ 목소리·타임라인
def speech_runs(a, thr=0.02, join=0.12):
    """소리 나는 구간들 (초) — 카운트다운 박자 찾기"""
    hop = A.SR // 100
    on = [np.abs(a[i:i + hop]).max() > thr for i in range(0, len(a), hop)]
    runs, s = [], None
    for i, v in enumerate(on + [False]):
        if v and s is None:
            s = i
        if not v and s is not None:
            if runs and (s - runs[-1][1]) / 100 < join:
                runs[-1] = (runs[-1][0], i)
            else:
                runs.append((s, i))
            s = None
    return [(x / 100, y / 100) for x, y in runs]


def load_timeline():
    files = [os.path.join(VOICE_DIR, f"line_{k:02d}.wav") for k in range(1, len(CAPS) + 1)]
    missing = [f for f in files if not os.path.exists(f)]
    assert not missing, f"음성 파일 없음: {missing[:2]} … tools/tts_lines.py로 만든다"
    parts, lines, t = [], [], 0.12
    parts.append(np.zeros(int(t * A.SR)))
    def trim(a):
        nz = np.nonzero(np.abs(a) > 0.01)[0]                  # 앞뒤 무음 자르기
        return a[max(0, nz[0] - 600): nz[-1] + 1500] if len(nz) else a

    count, speech_end = [], {}
    for k, f in enumerate(files, 1):
        a = trim(A.read_wav(f))
        st = t
        parts.append(a)
        t += len(a) / A.SR
        if k == COUNT_AFTER:                                  # 퀴즈 뒤 하나, 둘, 셋 (한 박자씩)
            speech_end[k] = t
            cw = trim(A.read_wav(os.path.join(VOICE_DIR, "count.wav")))   # "하나... 둘... 셋!" 한 파일
            parts.append(np.zeros(int(0.45 * A.SR)))
            t += 0.45
            for s0, s1 in speech_runs(cw):
                count.append((round(t + s0, 3), round(t + s1, 3)))
            assert len(count) == len(COUNT_WORDS), f"카운트다운 박자 {len(count)}개"
            parts.append(cw)
            t += len(cw) / A.SR
        lines.append((round(st, 3), round(t, 3)))
        parts.append(np.zeros(int(GAP * A.SR)))
        t += GAP
    voice = np.concatenate(parts[:-1])
    chunks = []
    for k, ((st, en), caps) in enumerate(zip(lines, CAPS), 1):
        if k == COUNT_AFTER:
            n = len(COUNT_WORDS)
            caps, en = caps[:-n], speech_end[k]
        w = [max(4, len(c.replace("*", ""))) for c in caps]
        acc = st
        for c, q in zip(caps, w):
            d = (en - st) * q / sum(w)
            chunks.append((acc, acc + d, c))
            acc += d
        if k == COUNT_AFTER:
            for j, c in enumerate(CAPS[k - 1][-n:]):
                chunks.append((count[j][0] - 0.1, (count[j + 1][0] - 0.1) if j + 1 < n else lines[k - 1][1], c))
    total = round(len(voice) / A.SR + TAIL, 2)
    hop = A.SR // FPS
    n = int(total * FPS) + 1
    rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(voice) else 0.0
                    for i in range(n)])
    rms = np.convolve(rms, np.ones(3) / 3, mode="same")
    energy = np.clip(rms / (np.percentile(rms[rms > 0], 95) + 1e-9), 0, 1).round(3).tolist()
    TL.update(lines=lines, chunks=chunks, total=total, energy=energy, preview=False, count=count)
    return voice


Ls, Le, chunk_start = E2.Ls, E2.Le, E2.chunk_start


# ------------------------------------------------------------------ 화면 부품
@lru_cache(None)
def pic(key):
    f, _, plate, _ = PHOTOS[key]
    im = Image.open(os.path.join(IMG, f)).convert("RGB")
    im.paste(im.crop(plate).filter(ImageFilter.GaussianBlur(12)), plate[:2])
    return im.convert("RGBA")


def xcard(key, zoom=1.0, fx=0.5, fy=0.5):
    inner = cover(pic(key), CARD_W, CARD_H, zoom, fx, fy, PHOTOS[key][1])
    inner.putalpha(G.card_mask())
    return inner


@lru_cache(None)
def price_tag(txt, sub, fill, fg=INK, w=560):
    return compose((box(w, 190, 34, fill, CREAM, 5, True), 0, 0),
                   (text_img(sub, 36, fg, "Bold", shadow=0), 0, -48),
                   (text_img(txt, 78, fg, "Black", shadow=0), 0, 22))


def strike(c, cx, cy, w, p, color=RED):
    if p > 0:
        ImageDraw.Draw(c).line((cx - w / 2, cy + 20, cx - w / 2 + w * p, cy + 20 - 40 * p), fill=color, width=14)


@lru_cache(None)
def seat_diagram(w=760, h=520):
    """위에서 본 차 실내: 앞 운전석·조수석, 뒷좌석"""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, w - 20, h - 20), 120, fill=(58, 58, 64), outline=CREAM, width=6)
    d.rounded_rectangle((60, 70, 140, h - 70), 30, fill=(90, 110, 140))          # 앞유리(왼쪽이 앞)
    for (x, y) in [(200, 110), (200, h - 230), (460, 110), (460, h - 230)]:       # 좌석 4개
        d.rounded_rectangle((x, y, x + 150, y + 120), 26, fill=(176, 168, 156), outline=INK, width=4)
    d.ellipse((150, h - 225, 200, h - 175), outline=CREAM, width=8)               # 운전대(왼쪽 앞, 한국 차)
    return im


@lru_cache(None)
def door_icon(frameless, w=360, h=300):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(20, 140), (w - 20, 140), (w - 20, h - 20), (20, h - 20)], fill=(70, 70, 78), outline=CREAM)
    glass = [(50, 134), (w - 40, 134), (w - 70, 30), (110, 30)]
    d.polygon(glass, fill=(150, 190, 225))
    if not frameless:                                    # 창틀
        d.line(glass + [glass[0]], fill=(20, 20, 24), width=24)
    else:
        d.line(glass[:2], fill=(30, 30, 34), width=10)
    d.rounded_rectangle((w - 110, 170, w - 50, 186), 6, fill=CREAM)              # 손잡이
    return im


@lru_cache(None)
def paper(w=900, h=420):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w - 1, h - 1), fill=(236, 228, 208), outline=INK, width=4)
    d.rectangle((24, 24, w - 24, 120), fill=INK)
    t = text_img("1998 경제", 64, (236, 228, 208), "Black", shadow=0)
    im.alpha_composite(t, ((w - t.width) // 2, 72 - t.height // 2))
    for k in range(5):
        y = 250 + k * 30
        d.line((40, y, w - 40 - (k % 2) * 160, y), fill=(150, 140, 120), width=8)
    return im


def countdown(c, t, x=W / 2 - 60, y=1185):
    """퀴즈 뒤 '하나, 둘, 셋!' — 박자마다 큰 원이 튀어나옴"""
    cnt = TL.get("count") or []
    j = max([q for q, (st, _) in enumerate(cnt) if t >= st - 0.08] or [-1])
    if j < 0:
        return 0
    p = out_back(prog(t, cnt[j][0] - 0.08, 0.22))
    fill = YEL if j == len(cnt) - 1 else (250, 246, 236)
    disk = compose((box(230, 230, 115, fill, INK, 8, True), 0, 0),
                   (text_img(COUNT_WORDS[j], 92, INK, "Black", shadow=0), 0, -4))
    paste(c, disk, x, y, 0.6 + 0.4 * p, (j - 1) * 6)
    for q in range(len(cnt)):                                 # 작은 점 3개
        on = q <= j
        ImageDraw.Draw(c).ellipse((x - 60 + q * 60 - 12, y + 128 - 12, x - 60 + q * 60 + 12, y + 128 + 12),
                                  fill=YEL if on else (90, 90, 96))
    return 1 + 0.04 * (1 - p)                                 # 보기 칩이 박자에 맞춰 살짝 들썩


def char_react(c, t):
    E2.CHAR_H, E2.CHAR_X, E2.CHAR_FOOT = CHAR_H, CHAR_X, CHAR_FOOT
    E2.char_react(c, t)


# ------------------------------------------------------------------ 장면
HOOK_BOX = (200, 230, 1100, 960)


def to_card(sx, sy, zoom=1.0, fx=0.5, fy=0.5, box_=HOOK_BOX):
    """원본 사진 좌표 → 화면 좌표 (put_card 기준)"""
    bl, bt, br, bb = box_
    bw, bh = br - bl, bb - bt
    sc = max(CARD_W / bw, CARD_H / bh) * zoom
    cw, ch = CARD_W / sc, CARD_H / sc
    l = bl + clamp(fx * bw - cw / 2, 0, bw - cw)
    t = bt + clamp(fy * bh - ch / 2, 0, bh - ch)
    return (W - CARD_W) / 2 + (sx - l) * sc, G.CARD_Y - CARD_H / 2 + (sy - t) * sc


def hook(c, t, back=1.0):
    """1번(그리고 끝에서 돌아오는) 첫 화면: 검정 Q30 + 뒷자리(회장님) → 운전대(나)"""
    z = 1.0 + 0.04 * in_out(prog(t, 0, 3))
    inner = cover(pic("black"), CARD_W, CARD_H, z, 0.5, 0.45, HOOK_BOX)
    inner.putalpha(G.card_mask())
    put_card(c, inner)
    shade_card(c, 0.28)
    a = clamp(back)
    if a <= 0:
        return
    rx, ry = to_card(865, 505, z, 0.5, 0.45)          # 뒷좌석 창
    wx, wy = to_card(590, 500, z, 0.5, 0.45)          # 앞유리(운전대 쪽)
    ring = Image.new("RGBA", (260, 170), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((8, 8, 252, 162), outline=YEL, width=12)
    paste(c, ring, rx, ry, 1, 0, a)
    paste(c, label("회장님 자리", 360, (60, 60, 66), WHITE, 50), rx + 10, ry + 105, 0.9, 3, a)
    # 뒷자리 → 운전대 쪽 굽은 화살표
    pts = [(rx - 90 + (wx + 70 - rx + 90) * k / 20, ry - 110 - 120 * math.sin(math.pi * k / 20)) for k in range(21)]
    pts = [(x, y) for x, y in pts]
    ov = Image.new("RGBA", c.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.line(pts, fill=(0, 0, 0, 200), width=26, joint="curve")
    d.line(pts, fill=YEL + (255,), width=16, joint="curve")
    ex, ey = pts[-1]
    d.polygon([(ex - 32, ey - 36), (ex + 32, ey - 36), (ex, ey + 20)], fill=YEL + (255,), outline=(0, 0, 0))
    if a < 1:
        ov.putalpha(ov.getchannel("A").point(lambda v: int(v * a)))
    c.alpha_composite(ov)
    paste(c, label("내가 운전대를?", 470, AMBER, INK, 58), wx - 60, wy + 240, 1, -3, a)


def frame(i):
    t = i / FPS
    c = E2.title_band().copy()
    cred = PHOTOS["black"][3]
    if t < Ls(2) - 0.05:                                        # 1 훅
        hook(c, t)
    elif t < Ls(3) - 0.05:                                      # 2 1998 그랜저 XG (뒷모습 XG 배지)
        lt = t - Ls(2)
        cred = PHOTOS["rear"][3]
        put_card(c, xcard("rear", 1.25 - 0.18 * out_cubic(prog(lt, 0, 1.2)), 0.3, 0.45))
        big(c, "1998 그랜저 XG", Ls(2) + 0.15, t, 1130, 96, YEL, x=W / 2 - 70)
    elif t < Ls(4) - 0.05:                                      # 3 문을 열면 깜짝
        lt = t - Ls(3)
        cred = PHOTOS["black"][3]
        z = 1.0 + 0.9 * in_out(prog(lt, 0.1, max(0.8, Le(3) - Ls(3) - 0.2)))
        put_card(c, xcard("black", z, 0.63, 0.35))
        shade_card(c, 0.3)
        for k, (x, y) in enumerate([(W / 2 - 120, 760), (W / 2 + 150, 700), (W / 2 + 20, 880)]):
            pq = out_back(prog(t, chunk_start(3, 1) + 0.15 * k, 0.25))
            paste(c, text_img("?", 150, YEL, "Black", stroke=8, sfill=(0, 0, 0)), x, y, pq + 0.001, (k - 1) * 10,
                  clamp(pq * 2))
    elif t < Ls(5) - 0.05:                                      # 4 퀴즈
        lt = t - Ls(4)
        cred = None
        G.panel(c, (30, 30, 34))
        paste(c, label("자, 퀴즈!", 420, RED, WHITE, 70), W / 2, 560, out_back(prog(lt, 0, 0.25)))
        pb = clamp((t - chunk_start(4, 1)) * 4)
        paste(c, text_img("뉴 그랜저 최고급 = 3,490만 원", 50, CREAM, "Black", stroke=5, sfill=(0, 0, 0)),
              W / 2, 680, 1, 0, pb)
        beat = countdown(c, t) or 1
        for k, txt in enumerate(["2천만 원대", "3천만 원대", "4천만 원대"]):
            pk = out_back(prog(t, chunk_start(4, 2) + 0.12 * k, 0.25))
            paste(c, option_chip(str(k + 1), txt), W / 2 - 80, 800 + k * 135, (pk + 0.001) * beat * 0.95, 0,
                  clamp(pk * 2))
    elif t < Ls(6) - 0.05:                                      # 5 정답
        lt = t - Ls(5)
        cred = None
        G.panel(c, (30, 30, 34))
        hit = chunk_start(5, 1)
        for k, txt in enumerate(["2천만 원대", "3천만 원대", "4천만 원대"]):
            st = 0 if t < hit else (1 if k == 0 else 2)
            sc = 1.0 + (0.08 * (1 - out_cubic(prog(t, hit, 0.3))) if st == 1 else 0)
            paste(c, option_chip(str(k + 1), txt, st), W / 2 - 80, 600 + k * 130, 0.85 * sc)
        dx, dy = jolt(t, hit, 18)
        v = int(2200 + 500 * out_cubic(prog(t, hit, 0.7)))
        txt = "2,200만~2,700만 원대" if t >= hit + 0.7 else f"2,200만~{v:,}만"
        paste(c, text_img(txt, 78, YEL, "Black", stroke=6, sfill=(0, 0, 0), shadow=8), W / 2 - 60 + dx, 1000 + dy, 1, 0,
              clamp((t - hit) * 4))
        ps = prog(t, chunk_start(5, 2) + 0.05, 0.16)
        if ps > 0:
            paste(c, stamp("700만 원 가까이 ↓", 52), W / 2 - 60, 1200, 2.0 - 1.0 * ps, -6, clamp(ps * 3))
        paste(c, text_img("Q25 · Q25 SE · Q30 · 출시 발표 때 · 한국일보 1998-09-24", 30, CREAM, "Bold", stroke=4,
                          sfill=(0, 0, 0)), W / 2 - 60, 1100, 1, 0, prog(t, hit + 0.5, 0.3))
    elif t < Ls(7) - 0.05:                                      # 6 외환위기
        lt = t - Ls(6)
        cred = None
        G.panel(c, (40, 34, 30))
        pp = out_back(prog(lt, 0.05, 0.3))
        paste(c, paper(), W / 2, 780, pp + 0.001, -3, clamp(pp * 2))
        ps = prog(t, chunk_start(6, 1) + 0.1, 0.16)
        if ps > 0:
            paste(c, stamp("외환위기", 92), W / 2 + 60, 830, 2.2 - 1.2 * ps, -8, clamp(ps * 3))
        paste(c, text_img("1997년 말 IMF 구제금융 → 1998년", 40, CREAM, "Bold", stroke=4, sfill=(0, 0, 0)),
              W / 2, 1080, 1, 0, prog(t, chunk_start(6, 1) + 0.4, 0.3))
    elif t < Ls(8) - 0.05:                                      # 7 신입 월급 감소 → 짜장면 X
        lt = t - Ls(7)
        cred = None
        G.panel(c, (32, 38, 34))
        p = in_out(prog(lt, 0.2, 0.9))
        paste(c, envelope(300, "129.2만"), W / 2 - 220, 760, 1.0, -4, clamp(lt * 4))
        paste(c, text_img("→", 110, CREAM, "Black", stroke=6, sfill=(0, 0, 0)), W / 2, 760, 1, 0, clamp(p * 3))
        paste(c, envelope(300, "125만"), W / 2 + 220, 760, 1.0 - 0.12 * p, 4, clamp(p * 3))
        pl = out_back(prog(lt, 0.9, 0.25))
        paste(c, label("-3.2%", 300, RED, WHITE, 72), W / 2 + 220, 590, pl + 0.001, 6, clamp(pl * 2))
        paste(c, text_img("대졸 사무직 초임 1997 → 1998 · 경총 조사(파이낸셜뉴스 보도)", 28, (215, 205, 190),
                          "SemiBold", shadow=2), W / 2, 920)
        pj = prog(t, chunk_start(7, 1) + 0.05, 0.3)
        if pj > 0:
            bx, by = W / 2, 1110
            paste(c, box(380, 260, 40, (32, 38, 34), shadow=True), bx, by, out_back(pj))
            paste(c, bowl(210), bx, by, out_back(pj))
            q = out_cubic(prog(t, chunk_start(7, 1) + 0.3, 0.2))
            if q > 0:
                d = ImageDraw.Draw(c)
                d.line((bx - 100, by - 100, bx - 100 + 200 * q, by - 100 + 200 * q), fill=RED, width=20)
                d.line((bx + 100, by - 100, bx + 100 - 200 * q, by - 100 + 200 * q), fill=RED, width=20)
    elif t < Ls(9) - 0.05:                                      # 8 회장님 뒷자리 → 내가 모는 차
        lt = t - Ls(8)
        cred = None
        G.panel(c, (26, 28, 34))
        paste(c, seat_diagram(), W / 2, 830, 1, 0, clamp(lt * 4))
        # 뒷좌석(오른쪽 아래) → 운전석(왼쪽 아래)
        rx, ry = W / 2 - 380 + 535, 830 - 260 + 350
        fx_, fy_ = W / 2 - 380 + 275, 830 - 260 + 350
        paste(c, label("회장님 자리", 330, (120, 116, 110), WHITE, 44), rx, ry - 230, 1, 0, clamp(lt * 4))
        p = in_out(prog(t, chunk_start(8, 1) - 0.1, 0.6))
        if p > 0:
            d = ImageDraw.Draw(c)
            x = rx + (fx_ - rx) * p
            d.line((rx, ry, x, ry), fill=YEL, width=16)
            d.polygon([(x - 6, ry - 30), (x - 6, ry + 30), (x - 50, ry)], fill=YEL)
        pk = out_back(prog(t, chunk_start(8, 1) + 0.5, 0.25))
        paste(c, label("내가 운전석!", 400, AMBER, INK, 56), fx_, ry + 190, pk + 0.001, -3, clamp(pk * 2))
        paste(c, text_img("※ 뒷자리 손님용 고급차에서 차주가 직접 모는 고급차 쪽으로", 28, (210, 210, 215), "SemiBold",
                          shadow=2), W / 2, 1300, 1, 0, prog(t, chunk_start(8, 1) + 0.6, 0.3))
    elif t < Ls(10) - 0.05:                                     # 9 프레임리스 도어
        lt = t - Ls(9)
        cred = PHOTOS["black"][3]
        if t < chunk_start(9, 1):
            put_card(c, xcard("black", 1.9, 0.63, 0.35))
            shade_card(c, 0.2)
        else:
            G.panel(c, (26, 28, 34))
            cred = None
            for k, (fl, x, name) in enumerate([(False, W / 2 - 230, "보통 문"), (True, W / 2 + 230, "프레임리스")]):
                pk = out_back(prog(t, chunk_start(9, 1) + 0.15 * k, 0.25))
                paste(c, door_icon(fl), x, 800, pk + 0.001, 0, clamp(pk * 2))
                paste(c, label(name, 330, AMBER if fl else (120, 116, 110), INK if fl else WHITE, 48), x, 1010, pk + 0.001)
            paste(c, text_img("창틀 있음", 40, CREAM, "Bold", stroke=4, sfill=(0, 0, 0)), W / 2 - 230, 610)
            paste(c, text_img("창틀 없음, 유리만!", 40, YEL, "Black", stroke=4, sfill=(0, 0, 0)), W / 2 + 230, 610)
            ps = prog(t, chunk_start(9, 2), 0.16)
            if ps > 0:
                paste(c, stamp("유리만 쏙", 60), W / 2 + 230, 1150, 2.2 - 1.2 * ps, -6, clamp(ps * 3))
    elif t < Ls(11) - 0.05:                                     # 10 현대 독자 개발 엔진, 첫 그랜저
        lt = t - Ls(10)
        cred = PHOTOS["rear"][3]
        put_card(c, xcard("rear", 1.1, 0.35, 0.45))
        shade_card(c, 0.6)
        pl = out_back(prog(t, chunk_start(10, 1), 0.3))
        paste(c, label("현대 독자 개발 엔진", 620, AMBER, INK, 60), W / 2 - 40, 800, pl + 0.001, -2, clamp(pl * 2))
        ps = prog(t, chunk_start(10, 2) + 0.05, 0.16)
        if ps > 0:
            sc = 2.2 - 1.2 * ps
            paste(c, box(520, 150, 24, (250, 246, 236, 235), shadow=True), W / 2 - 40, 1000, sc, -6, clamp(ps * 3))
            paste(c, stamp("첫 그랜저", 72), W / 2 - 40, 1000, sc, -6, clamp(ps * 3))
        paste(c, text_img("현대자동차그룹 그랜저 역사 스토리", 30, CREAM, "Bold", stroke=4, sfill=(0, 0, 0)),
              W / 2 - 40, 1140, 1, 0, prog(t, chunk_start(10, 2) + 0.4, 0.3))
    else:                                                       # 11 첫 화면으로 돌아감
        back = in_out(prog(t, Ls(11) + 0.1, 0.9))
        hook(c, 0.0, back)                                      # 첫 화면 사진 위에서 표시가 서서히 돌아옴
        shade_card(c, 0.3 * (1 - back))
    if cred:
        E2.credit_line(c, cred)
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
    v = v / max(1e-9, np.abs(v).max()) * 0.92
    music = retro_bgm(TL["total"] + 1.0)[:n]
    act = np.convolve((np.abs(v) > 0.02).astype(float), np.ones(int(0.3 * sr)) / int(0.3 * sr), mode="same")
    music = music * (1 - 0.55 * np.clip(act * 4, 0, 1))[:, None] * 0.7
    ev = [(0.35, A.sfx_whoosh(0.3), 0.4), (0.55, A.sfx_pop(), 0.5), (chunk_start(1, 1) + 0.1, A.sfx_pop(), 0.6),
          (Ls(2), A.sfx_whoosh(0.35), 0.4), (chunk_start(3, 1), A.sfx_riser(0.8), 0.35),
          (Ls(4), A.sfx_ding(), 0.5)]
    ev += [(chunk_start(4, 2) + 0.12 * k, A.sfx_pop(), 0.5) for k in range(3)]
    ev += [(st - 0.05, tick_sfx(), 0.9) for st, _ in TL["count"]]
    hit = chunk_start(5, 1)
    ev += [(chunk_start(5, 2) + 0.05, stamp_sfx(), 0.7), (hit - 0.02, A.sfx_ding(), 0.7), (hit + 0.05, calc_sfx(), 0.8), (Ls(6), A.sfx_whoosh(0.35), 0.4),
           (chunk_start(6, 1) + 0.1, stamp_sfx(), 0.8), (Ls(7) + 0.9, A.sfx_pop(), 0.5),
           (chunk_start(7, 1) + 0.3, stamp_sfx(), 0.6), (Ls(8), A.sfx_whoosh(0.35), 0.4),
           (chunk_start(8, 1) - 0.1, A.sfx_riser(0.6), 0.35), (chunk_start(8, 1) + 0.5, A.sfx_pop(), 0.6),
           (chunk_start(9, 1), A.sfx_whoosh(0.35), 0.4), (chunk_start(9, 2), stamp_sfx(), 0.8),
           (Ls(10) + 0.1, A.sfx_whoosh(0.35), 0.4), (chunk_start(10, 1), A.sfx_pop(), 0.5),
           (chunk_start(10, 2) + 0.05, stamp_sfx(), 0.8), (Ls(11) + 0.1, A.sfx_riser(0.8), 0.3)]
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
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", mix, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9",
                           "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{TL['total']}",
                           "-movflags", "+faststart", OUT])
    write_srt(OUT.replace(".mp4", ".srt"))
    print("[done]", OUT)


if __name__ == "__main__":
    main()
