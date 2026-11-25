"""롱폼 01 · 제네시스, 구르던 차에서 지붕 에어백까지 (가로 1920×1080, 약 4분)
대본: docs/long01_genesis_gv90_script.md
목소리: python3 tools/tts_lines.py docs/long01_genesis_gv90_script.md assets/voice/long01 --rate 1.0
사용법: python3 long01_genesis.py [--preview 3 40 120]
"""
import argparse
import json
import math
import os
import re
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import audio as A
from ep_grandeur2 import CREAM, AMBER, RED, INK, stamp, option_chip, retro_bgm, stamp_sfx, tick_sfx
from tools.chahyung_motion import Chahyung
from video import YEL, WHITE, prog, out_cubic, out_back, in_out, clamp, text_img, rich_img, box, compose, paste, cover

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1920, 1080, 30
VOICE = os.path.join(ROOT, "assets", "voice", "long01")
IMGD = os.path.join(ROOT, "assets", "images", "genesis")
BUILD = os.path.join(ROOT, "build", "long01")
OUT = os.path.join(ROOT, "output", "long01_genesis_gv90.mp4")
GAP, CH_GAP, HEAD, TAIL = 0.75, 1.8, 0.3, 2.5
QUIZ = 30                                    # 이 문장 뒤 하나, 둘, 셋
CHAPTERS = {1: ("", ""), 6: ("1장", "이름 하나로 시작하다"), 11: ("2장", "차 이름에서 브랜드로"),
            16: ("3장", "2021년 2월, 그 커브길"), 24: ("4장", "그리고 지금, GV90"), 32: ("마무리", "구르는 순간까지")}
CREDIT = {
    "bh_show": "사진: Bull-Doser · 퍼블릭 도메인 · Wikimedia Commons",
    "bh_front": "사진: Benespit · CC BY-SA 4.0 · Wikimedia Commons (크롭)",
    "gv80_front": "사진: Benespit · CC BY-SA 4.0 · Wikimedia Commons (크롭)",
    "gv80_white": "사진: MercurySable99 · CC BY-SA 4.0 · Wikimedia Commons (크롭·스티커 흐림)",
    "gv80_show": "사진: CChanSonichu · CC BY-SA 4.0 · Wikimedia Commons (크롭)",
    "gv90_gray_front": "사진: Damian B Oh · CC BY-SA 4.0 · Wikimedia Commons (크롭)",
    "gv90_green_door": "사진: Damian B Oh · CC BY-SA 4.0 · Wikimedia Commons (크롭)",
    "gv90_neolun_rear": "사진: Damian B Oh · CC BY-SA 4.0 · Wikimedia Commons (크롭)",
    "gv90_white_front": "사진: Damian B Oh · CC BY-SA 4.0 · Wikimedia Commons (크롭)",
}
FILES = {"bh_show": "bh_show_bulldoser.jpg", "bh_front": "bh_front_benespit.jpg", "gv80_front": "gv80_front_benespit.jpg",
         "gv80_white": "gv80_white_mercurysable99.jpg", "gv80_show": "gv80_show_cchansonichu.jpg",
         "gv90_gray_front": "gv90_gray_front_damianboh.jpg", "gv90_green_door": "gv90_green_door_damianboh.jpg",
         "gv90_neolun_rear": "gv90_neolun_rear_damianboh.jpg", "gv90_white_front": "gv90_white_front_damianboh.jpg"}
PLATES = {"gv80_white": [(900, 355, 1000, 400)]}      # 앞유리 스티커

# 화면 자막 (숫자는 숫자로)
CAPS = [
    "2021년 2월, 미국 *로스앤젤레스*의 내리막 커브길",
    "SUV 한 대가 중앙분리대를 넘어, *여러 번 굴렀습니다*",
    "운전석에는 *타이거 우즈*가 있었죠",
    "그리고 그 차는, *제네시스 GV80*이었습니다",
    "오늘은 이 차를 만든 이름, *제네시스*가 | 어디서 시작해서 어디까지 왔는지 따라가 볼게요",
    "시작은 *2008년*이었습니다 | 현대차가 처음으로 작정하고 만든 고급 세단, *제네시스*",
    "그때 제네시스는 브랜드가 아니라, *차 이름 하나*였어요",
    "그런데 이듬해 1월, 미국 *디트로이트*에서 | 깜짝 놀랄 소식이 들려옵니다",
    "이 차가 *북미 올해의 차*로 뽑힌 거예요 | *한국 차로는 처음*이었습니다",
    "그 시절엔 말이죠, | 한국 차가 미국에서 *고급차*로 상을 받는다는 건 | 쉽게 상상하기 어려운 일이었어요",
    "그리고 *2015년 11월*, | 제네시스는 차 이름에서 *브랜드*가 됩니다",
    "현대라는 이름을 떼고, *따로 간판*을 단 거죠 | 첫 차는 플래그십 세단 *EQ900*이었습니다",
    "그리고 *2020년 1월*, 브랜드의 *첫 SUV*가 나옵니다 | *GV80*",
    "큼직한 *크레스트 그릴*에, 위아래 *두 줄* 헤드램프 | 한눈에 제네시스라는 걸 알 수 있는 얼굴이었죠",
    "그런데 1년 뒤, 이 차는 | *전혀 다른 이유*로 전 세계 뉴스에 오르게 됩니다",
    "*2021년 2월 23일* | 제한속도 시속 *72km*의 내리막길",
    "경찰 발표로는, 차는 시속 *135~140km*로 달리고 있었습니다 | 제한속도의 *거의 두 배*였죠",
    "커브를 돌지 못한 차는 중앙분리대를 넘고, | 길가로 *굴러 내려갔습니다*",
    "경찰이 밝힌 원인은 | *과속*과 *커브 대처 실패*였어요",
    "우즈는 다리를 *크게 다쳤습니다* | 하지만 *목숨은 건졌죠*",
    "우즈는 *안전벨트*를 매고 있었고, *에어백*도 터졌습니다",
    "당시 보안관은 이렇게 말했습니다 | 차 *실내가 거의 온전*했고, | 그게 살아남을 *쿠션*이 됐다고요",
    "앞쪽은 *완전히 부서졌는데*, | 사람이 앉는 공간은 *버텨 준* 겁니다",
    "그리고 5년 뒤, *2026년 11월* | 제네시스에서 *가장 큰 차*가 나왔습니다 | *GV90*",
    "값은 *1억 3,950만 원*부터 | 제일 비싼 네오룬 4인승은 *2억 3,950만 원*입니다",
    "배터리는 *123.5kWh* | 현대차그룹 전기차 가운데 *가장 큽니다* | 한 번 충전으로 *500km*를 달리고요",
    "앞뒤 모터를 합친 최고 출력은 *490kW* | 그룹에서 *가장 힘센* 전기차예요",
    "네오룬은 앞문과 뒷문이 *서로 마주 보며* 열립니다 | 문 사이 기둥은 아예 *문 안에 숨겼죠*",
    "차를 세우면 앞좌석이 *뒤로 빙글* 돌아서, | 뒷좌석과 *마주 앉을* 수도 있어요",
    "자, 퀴즈! | 차 이름 하나였던 첫 제네시스에서 GV90까지, | *몇 년*이 걸렸을까요?",
    "정답, *18년*입니다",
    "그런데요, GV90에는 | *세계 최초*라는 에어백이 하나 있습니다",
    "바로 *지붕 에어백* | 차가 *구를 때*를 위해 만든 에어백이에요",
    "차가 구르는 걸 감지하면, | 순식간에 펼쳐져 *유리 지붕을 덮습니다*",
    "사람이 지붕 밖으로 *튕겨 나가지 않게* 막고, | 머리가 지붕에 *부딪히지 않게* 받쳐 주죠",
    "5년 전, 커브길에서 *구르던* 제네시스",
    "그 이름을 단 차가 이제는, | *구르는 순간까지* 계산하고 나옵니다",
    "18년 전 *차 이름 하나*로 시작한 제네시스 | 다음 이야기는, *어디까지* 갈까요",
    "*차를 읽는 시간*, 차형이었습니다",
]
MOTIONS = ["think", "shock", "secret", "point_down", "talk", "nod", "talk", "secret", "jump", "talk",
           "key_spin", "nod", "cheer", "point_down", "secret", "think", "shock", "shock", "awkward", "nod",
           "talk", "talk", "think", "cheer", "jump", "nod", "key_spin", "shock", "cheer", "think",
           "jump", "secret", "shock", "point_down", "nod", "think", "key_spin", "talk", "cheer"]
TL = {}


# ------------------------------------------------------------------ 타임라인
def runs(a, thr=0.02, join=0.12):
    hop = A.SR // 100
    on = [np.abs(a[i:i + hop]).max() > thr for i in range(0, len(a), hop)]
    out, s = [], None
    for i, v in enumerate(on + [False]):
        if v and s is None:
            s = i
        if not v and s is not None:
            if out and (s - out[-1][1]) / 100 < join:
                out[-1] = (out[-1][0], i)
            else:
                out.append((s, i))
            s = None
    return [(x / 100, y / 100) for x, y in out]


def trim(a):
    nz = np.nonzero(np.abs(a) > 0.01)[0]
    return a[max(0, nz[0] - 600): nz[-1] + 1800] if len(nz) else a


def load_timeline():
    assert len(CAPS) == len(MOTIONS) == 39
    parts, lines, t, count = [np.zeros(int(HEAD * A.SR))], [], HEAD, []
    for k in range(1, len(CAPS) + 1):
        if k in CHAPTERS and k > 1:
            parts.append(np.zeros(int(CH_GAP * A.SR)))
            t += CH_GAP
        a = trim(A.read_wav(os.path.join(VOICE, f"line_{k:02d}.wav")))
        st = t
        parts.append(a)
        t += len(a) / A.SR
        if k == QUIZ:
            parts.append(np.zeros(int(0.5 * A.SR)))
            t += 0.5
            cw = trim(A.read_wav(os.path.join(VOICE, "count.wav")))
            count = [(round(t + x, 3), round(t + y, 3)) for x, y in runs(cw)]
            assert len(count) == 3, count
            parts.append(cw)
            t += len(cw) / A.SR + 0.5
            parts.append(np.zeros(int(0.5 * A.SR)))
        lines.append((round(st, 3), round(t, 3)))
        parts.append(np.zeros(int(GAP * A.SR)))
        t += GAP
    voice = np.concatenate(parts)
    chunks = []
    for k, ((st, en), cap) in enumerate(zip(lines, CAPS), 1):
        segs = [x.strip() for x in cap.split("|")]
        if k == QUIZ:
            en = count[0][0] - 0.3
        w = [max(5, len(s.replace("*", ""))) for s in segs]
        acc = st
        for s, q in zip(segs, w):
            d = (en - st) * q / sum(w)
            chunks.append((acc, acc + d, s, k))
            acc += d
        if k == QUIZ:
            for j, s in enumerate(["*하나*", "하나, *둘*", "하나, 둘, *셋!*"]):
                chunks.append((count[j][0] - 0.1, count[j + 1][0] - 0.1 if j < 2 else lines[k - 1][1], s, k))
    total = round(len(voice) / A.SR + TAIL, 2)
    hop = A.SR // FPS
    n = int(total * FPS) + 1
    rms = np.array([np.sqrt(np.mean(voice[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(voice) else 0.0
                    for i in range(n)])
    rms = np.convolve(rms, np.ones(3) / 3, mode="same")
    energy = np.clip(rms / (np.percentile(rms[rms > 0], 95) + 1e-9), 0, 1).round(3).tolist()
    TL.update(lines=lines, chunks=chunks, total=total, energy=energy, count=count)
    return voice


def Ls(k):
    return TL["lines"][k - 1][0]


def Le(k):
    return TL["lines"][k - 1][1]


def cs(k, j):
    """k번 문장의 j번째 자막 조각 시작"""
    return [c[0] for c in TL["chunks"] if c[3] == k][j]


def line_at(t):
    k = 1
    for i, (st, _) in enumerate(TL["lines"], 1):
        if t >= st - 0.15:
            k = i
    return k


# ------------------------------------------------------------------ 부품
@lru_cache(None)
def photo(key):
    im = Image.open(os.path.join(IMGD, FILES[key])).convert("RGB")
    for b in PLATES.get(key, []):
        im.paste(im.crop(b).filter(ImageFilter.GaussianBlur(14)), b[:2])
    return im.convert("RGBA")


@lru_cache(None)
def vignette():
    v = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(v)
    for y in range(H):
        a = 0
        if y > H * 0.62:
            a = int(225 * ((y - H * 0.62) / (H * 0.38)) ** 1.2)
        elif y < 150:
            a = int(140 * (1 - y / 150))
        d.line((0, y, W, y), fill=(0, 0, 0, a))
    return v


def full_photo(c, key, t0, t, zoom=(1.0, 1.08), fx=(0.5, 0.5), fy=0.5, dark=0.0, gray=False):
    p = in_out(clamp((t - t0) / 9))
    im = cover(photo(key), W, H, zoom[0] + (zoom[1] - zoom[0]) * p, fx[0] + (fx[1] - fx[0]) * p, fy)
    if gray:
        g = im.convert("L").convert("RGBA")
        im = Image.blend(im, g, 0.85)
    c.alpha_composite(im)
    if dark > 0:
        c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * dark))))
    return CREDIT[key]


def panel(c, color=(24, 24, 28)):
    c.alpha_composite(Image.new("RGBA", (W, H), color + (255,)))
    d = ImageDraw.Draw(c)
    for x in range(-H, W, 60):
        d.line((x, 0, x + H, H), fill=(color[0] + 6, color[1] + 6, color[2] + 6), width=2)


def big(c, txt, t0, t, x=W / 2, y=H / 2, size=120, color=YEL, rot=0):
    p = out_back(prog(t, t0, 0.22), 2.0)
    if p > 0:
        paste(c, text_img(txt, size, color, "Black", stroke=8, sfill=(0, 0, 0), shadow=10), x, y, 1.5 - 0.5 * p, rot,
              clamp(p * 2))


def tag(txt, fill=(250, 246, 236), fg=INK, size=48, w=None):
    t = text_img(txt, size, fg, "Black", shadow=0)
    w = w or t.width + 80
    return compose((box(w, int(size * 1.75), int(size * 0.85), fill, None, 0, True), 0, 0), (t, 0, -3))


def pop(c, im, x, y, t0, t, rot=0, sc=1.0):
    p = out_back(prog(t, t0, 0.28), 2.0)
    if p > 0:
        paste(c, im, x, y, (0.3 + 0.7 * p) * sc, rot, clamp(p * 2))


def stamp_at(c, txt, x, y, t0, t, size=80, rot=-7, back=True):
    ps = prog(t, t0, 0.16)
    if ps > 0:
        sc = 2.2 - 1.2 * ps
        if back:
            st = stamp(txt, size)
            paste(c, box(st.width - 20, st.height - 30, 26, (250, 246, 236, 235), None, 0, True), x, y, sc, rot,
                  clamp(ps * 3))
        paste(c, stamp(txt, size), x, y, sc, rot, clamp(ps * 3))


@lru_cache(None)
def suv(w=620, color=(40, 40, 46), roofbag=0.0):
    """옆에서 본 SUV 실루엣 (오른쪽이 앞)"""
    h = int(w * 0.46)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = w / 620
    body = [(20, 200), (30, 130), (120, 120), (190, 50), (430, 48), (520, 120), (600, 135), (605, 205), (20, 210)]
    d.polygon([(x * s, y * s) for x, y in body], fill=color, outline=CREAM)
    d.polygon([(x * s, y * s) for x, y in [(205, 62), (300, 62), (300, 118), (150, 120)]], fill=(150, 190, 225))
    d.polygon([(x * s, y * s) for x, y in [(312, 62), (420, 62), (495, 118), (312, 118)]], fill=(150, 190, 225))
    for cx in (130, 480):
        d.ellipse(((cx - 52) * s, (205 - 52) * s, (cx + 52) * s, (205 + 52) * s), fill=(20, 20, 22), outline=CREAM,
                  width=max(2, int(4 * s)))
        d.ellipse(((cx - 22) * s, (205 - 22) * s, (cx + 22) * s, (205 + 22) * s), fill=(150, 150, 155))
    if roofbag > 0:                                   # 지붕 에어백: 유리 지붕을 덮으며 펼쳐짐
        x1 = 200 + (420 - 200) * roofbag
        d.rounded_rectangle((195 * s, 30 * s, x1 * s, 66 * s), int(16 * s), fill=YEL, outline=INK, width=max(2, int(3 * s)))
    return im


def car_roll(c, t, t0, x0, x1, y, dur=2.2, w=420, roofbag_at=None):
    p = clamp((t - t0) / dur)
    x = x0 + (x1 - x0) * out_cubic(p)
    rot = -360 * 1.5 * out_cubic(p)
    rb = 0.0 if roofbag_at is None else clamp((p - roofbag_at) / 0.12)
    paste(c, suv(w, roofbag=round(rb, 2)), x, y - 40 * abs(math.sin(math.radians(rot))), 1, rot)


def gauge(c, cx, cy, r, val, vmax, mark=None, unit="km/h"):
    d = ImageDraw.Draw(c)
    d.arc((cx - r, cy - r, cx + r, cy + r), 150, 390, fill=(80, 80, 88), width=30)
    a1 = 150 + 240 * min(1, val / vmax)
    d.arc((cx - r, cy - r, cx + r, cy + r), 150, a1, fill=RED if mark and val > mark else AMBER, width=30)
    if mark:
        am = math.radians(150 + 240 * mark / vmax)
        d.line((cx + math.cos(am) * (r - 50), cy + math.sin(am) * (r - 50), cx + math.cos(am) * (r + 24),
                cy + math.sin(am) * (r + 24)), fill=WHITE, width=8)
    a = math.radians(a1)
    d.line((cx, cy, cx + math.cos(a) * (r - 40), cy + math.sin(a) * (r - 40)), fill=WHITE, width=12)
    d.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), fill=INK, outline=WHITE, width=4)
    paste(c, text_img(f"{int(val)}", 110, WHITE, "Black", stroke=6, sfill=(0, 0, 0)), cx, cy + r * 0.55)
    paste(c, text_img(unit, 36, CREAM, "Bold", shadow=0), cx, cy + r * 0.55 + 80)


def countdown(c, t, x, y):
    cnt = TL["count"]
    j = max([q for q, (st, _) in enumerate(cnt) if t >= st - 0.08] or [-1])
    if j < 0:
        return 1
    p = out_back(prog(t, cnt[j][0] - 0.08, 0.22))
    fill = YEL if j == 2 else (250, 246, 236)
    disk = compose((box(250, 250, 125, fill, INK, 8, True), 0, 0),
                   (text_img(["하나", "둘", "셋!"][j], 100, INK, "Black", shadow=0), 0, -4))
    paste(c, disk, x, y, 0.6 + 0.4 * p, (j - 1) * 6)
    for q in range(3):
        ImageDraw.Draw(c).ellipse((x - 70 + q * 70 - 14, y + 160 - 14, x - 70 + q * 70 + 14, y + 160 + 14),
                                  fill=YEL if q <= j else (90, 90, 96))
    return 1 + 0.05 * (1 - p)


def timeline_bar(c, t, t0, y=560, hl=None):
    pts = [(2008, "첫 제네시스"), (2015, "브랜드 독립"), (2020, "GV80"), (2021, "우즈 사고"), (2026, "GV90")]
    x0, x1 = 260, 1660
    d = ImageDraw.Draw(c)
    p = out_cubic(prog(t, t0, 1.2))
    d.line((x0, y, x0 + (x1 - x0) * p, y), fill=CREAM, width=8)
    for k, (yr, name) in enumerate(pts):
        x = x0 + (x1 - x0) * (yr - 2008) / 18
        q = out_back(prog(t, t0 + 0.2 * k, 0.3))
        if q <= 0:
            continue
        on = hl is None or yr in hl
        d.ellipse((x - 22, y - 22, x + 22, y + 22), fill=YEL if on else (110, 110, 116), outline=INK, width=4)
        dy = 60 if yr == 2021 else 0                  # 2020·2021이 붙어 있어 2021은 아래로 비켜 씀
        paste(c, text_img(str(yr), 52, YEL if on else CREAM, "Black", stroke=5, sfill=(0, 0, 0)), x + (30 if yr == 2021 else -30 if yr == 2020 else 0),
              y - 75 if yr != 2021 else y + 70, q)
        paste(c, text_img(name, 36, WHITE if on else (170, 170, 176), "Bold", stroke=4, sfill=(0, 0, 0)),
              x + (40 if yr == 2021 else -30 if yr == 2020 else 0), y + 70 + dy if yr != 2020 else y - 140, q)


def chapter_title(c, t):
    for k, (no, title) in CHAPTERS.items():
        if k == 1 or not title:
            continue
        t0 = Ls(k) - CH_GAP
        if t0 - 0.05 <= t < Ls(k) + 1.6:
            p = out_back(prog(t, t0, 0.35))
            q = 1 - prog(t, Ls(k) + 1.1, 0.5)
            a = clamp(p * 2) * q
            paste(c, Image.new("RGBA", (W, H), (0, 0, 0, int(150 * a))), W / 2, H / 2)
            paste(c, tag(no, RED, WHITE, 52), W / 2, H / 2 - 90, p, 0, a)
            paste(c, text_img(title, 110, WHITE, "Black", stroke=8, sfill=(0, 0, 0)), W / 2, H / 2 + 40, p, 0, a)


def chapter_pill(c, t):
    k = line_at(t)
    cur = max([q for q in CHAPTERS if q <= k])
    no, title = CHAPTERS[cur]
    if title:
        paste(c, tag(f"{no} · {title}", (20, 20, 22, 210), CREAM, 30), 70 + tag(f"{no} · {title}", size=30).width / 2,
              60)


def caption(c, t):
    for st, en, cap, k in TL["chunks"]:
        if st - 0.05 <= t < en + 0.12:
            p = out_back(prog(t, st - 0.05, 0.14), 2.0)
            im = rich_img(cap, 60, 9)
            if im.width > 1380:
                im = im.resize((1380, int(im.height * 1380 / im.width)), Image.BICUBIC)
            paste(c, im, 880, 975, 0.92 + 0.08 * p, 0, clamp(p * 1.6))
            return


@lru_cache(None)
def rig():
    return Chahyung(height=330)


def char(c, t):
    k = line_at(t)
    e = TL["energy"][min(len(TL["energy"]) - 1, int(t * FPS))]
    im = rig().frame(MOTIONS[k - 1], max(0.0, t - Ls(k)), e)
    c.alpha_composite(im, (int(1770 - im.width / 2), int(1068 - (im.height - rig().pad))))


def credit(c, txt):
    im = text_img(txt, 22, (225, 225, 225), "SemiBold", shadow=3)
    paste(c, im, 40 + im.width / 2, 1058)


# ------------------------------------------------------------------ 장면 (문장 번호별)
def scene(c, k, t):
    lt = t - Ls(k)
    cr = None
    if k == 1:
        cr = full_photo(c, "gv80_white", 0, t, (1.15, 1.05), (0.5, 0.5), dark=0.35)
        pop(c, tag("2021.2 · 미국 로스앤젤레스", (250, 246, 236), INK, 52), W / 2, 420, Ls(1) + 0.2, t)
    elif k == 2:
        panel(c, (30, 26, 24))
        d = ImageDraw.Draw(c)
        pts = [(x, 760 + 140 * math.sin(x / 520)) for x in range(0, W + 1, 20)]
        d.line(pts, fill=(90, 90, 96), width=90)
        d.line(pts, fill=CREAM, width=6)
        car_roll(c, t, Ls(2) + 0.2, 300, 1450, 600, dur=2.6, w=560)
    elif k == 3:
        cr = full_photo(c, "gv80_front", Ls(3), t, (1.0, 1.1), (0.45, 0.5), dark=0.45)
        pop(c, tag("운전석: 타이거 우즈", AMBER, INK, 64), W / 2, 450, Ls(3) + 0.3, t)
    elif k == 4:
        cr = full_photo(c, "gv80_front", Ls(3), t, (1.1, 1.18), (0.5, 0.5))
        big(c, "제네시스 GV80", cs(4, 0) + 0.6, t, W / 2, 420, 140)
    elif k == 5:
        panel(c)
        paste(c, text_img("제네시스", 150, YEL, "Black", stroke=8, sfill=(0, 0, 0)), W / 2, 260, 1, 0, clamp(lt * 3))
        timeline_bar(c, t, Ls(5) + 0.3)
    elif k == 6:
        cr = full_photo(c, "bh_show", Ls(6), t, (1.0, 1.1))
        big(c, "2008 · 제네시스", cs(6, 0) + 0.2, t, W / 2, 380, 120)
    elif k == 7:
        cr = full_photo(c, "bh_front", Ls(7), t, (1.0, 1.08), (0.5, 0.5), dark=0.35)
        pop(c, tag("브랜드 (아님)", (120, 116, 110), WHITE, 64), W / 2 - 260, 430, Ls(7) + 0.3, t, -3)
        pop(c, tag("차 이름 (맞음)", AMBER, INK, 64), W / 2 + 260, 430, cs(7, 0) + 1.2, t, 3)
    elif k == 8:
        cr = full_photo(c, "bh_front", Ls(7), t, (1.08, 1.15), (0.5, 0.5), dark=0.6)
        pop(c, tag("2009.1 · 미국 디트로이트", (250, 246, 236), INK, 56), W / 2, 420, Ls(8) + 0.3, t)
    elif k == 9:
        cr = full_photo(c, "bh_show", Ls(9), t, (1.1, 1.18), dark=0.55)
        stamp_at(c, "북미 올해의 차", W / 2 - 60, 380, Ls(9) + 0.5, t, 96)
        pop(c, tag("한국 차 최초", RED, WHITE, 64), W / 2 + 280, 560, cs(9, 1), t, 4)
        pop(c, text_img("2009 북미 올해의 차 · CNN Money 2009-01-08 보도", 30, CREAM, "Bold", stroke=4, sfill=(0, 0, 0)),
            W / 2, 680, cs(9, 1) + 0.4, t)
    elif k == 10:
        cr = full_photo(c, "bh_show", Ls(9), t, (1.18, 1.25), dark=0.65, gray=True)
        pop(c, tag("그 시절엔 말이죠", AMBER, INK, 60), W / 2, 420, Ls(10) + 0.2, t)
    elif k == 11:
        panel(c, (26, 24, 30))
        pop(c, tag("2015.11", (250, 246, 236), INK, 64), W / 2, 300, Ls(11) + 0.1, t)
        p = in_out(prog(t, cs(11, 1), 0.8))
        paste(c, text_img("차 이름", 110, (170, 170, 176), "Black", stroke=6, sfill=(0, 0, 0)), W / 2 - 320, 520, 1, 0,
              clamp(lt * 3))
        paste(c, text_img("→", 110, YEL, "Black", stroke=6, sfill=(0, 0, 0)), W / 2, 520, 1, 0, p)
        paste(c, text_img("브랜드", 130, YEL, "Black", stroke=8, sfill=(0, 0, 0)), W / 2 + 320, 520, 0.6 + 0.4 * p, 0, p)
    elif k == 12:
        panel(c, (26, 24, 30))
        paste(c, text_img("현대", 120, (150, 150, 156), "Black", stroke=6, sfill=(0, 0, 0)), W / 2 - 330, 400)
        q = out_cubic(prog(t, Ls(12) + 0.5, 0.4))
        if q > 0:
            ImageDraw.Draw(c).line((W / 2 - 460, 400, W / 2 - 460 + 260 * q, 400), fill=RED, width=16)
        paste(c, text_img("→", 110, YEL, "Black", stroke=6, sfill=(0, 0, 0)), W / 2 - 60, 400, 1, 0, q)
        paste(c, text_img("제네시스", 130, YEL, "Black", stroke=8, sfill=(0, 0, 0)), W / 2 + 280, 400, 1, 0, q)
        pop(c, tag("따로 간판", RED, WHITE, 48), W / 2 + 280, 270, Ls(12) + 1.0, t, 4)
        pop(c, tag("첫 차: 플래그십 세단 EQ900", (250, 246, 236), INK, 56), W / 2, 620, cs(12, 1), t)
    elif k == 13:
        cr = full_photo(c, "gv80_show", Ls(13), t, (1.0, 1.08), (0.5, 0.5), 0.55)
        big(c, "2020.1 · GV80", Ls(13) + 0.3, t, W / 2, 330, 120)
        pop(c, tag("브랜드 첫 SUV", RED, WHITE, 60), W / 2, 480, cs(13, 0) + 1.0, t, -3)
    elif k == 14:
        cr = full_photo(c, "gv80_front", Ls(14), t, (1.2, 1.5), (0.3, 0.32), 0.4)
        pop(c, tag("크레스트 그릴", AMBER, INK, 56), 620, 300, Ls(14) + 0.4, t, -3)
        pop(c, tag("두 줄 헤드램프", AMBER, INK, 56), 1260, 300, Ls(14) + 1.3, t, 3)
    elif k == 15:
        cr = full_photo(c, "gv80_white", Ls(15), t, (1.0, 1.1), (0.5, 0.5), dark=0.55, gray=True)
        big(c, "1년 뒤…", cs(15, 1), t, W / 2, 400, 150, YEL, -3)
    elif k == 16:
        panel(c, (22, 26, 30))
        sign = compose((box(320, 320, 160, WHITE, RED, 30, True), 0, 0),
                       (text_img("72", 150, INK, "Black", shadow=0), 0, -6))
        pop(c, sign, W / 2 - 280, 440, Ls(16) + 0.2, t)
        pop(c, tag("제한속도 시속 72km (45마일)", (250, 246, 236), INK, 48), W / 2 - 280, 690, cs(16, 1), t)
        pop(c, tag("2021.2.23", RED, WHITE, 64), W / 2 + 330, 440, Ls(16) + 0.4, t, 3)
    elif k == 17:
        panel(c, (22, 26, 30))
        v = 72 + (140 - 72) * out_cubic(prog(t, Ls(17) + 0.4, 2.0))
        gauge(c, W / 2 - 200, 520, 300, v, 200, mark=72)
        stamp_at(c, "거의 2배", W / 2 + 420, 420, cs(17, 1), t, 96)
        pop(c, text_img("시속 84~87마일(약 135~140km) · 보안관 발표(2021-04-07)", 30, CREAM, "Bold", stroke=4, sfill=(0, 0, 0)),
            W / 2 + 420, 600, cs(17, 1) + 0.4, t)
    elif k == 18:
        panel(c, (30, 26, 24))
        d = ImageDraw.Draw(c)
        pts = [(x, 640 + 200 * math.sin(x / 400 + 1)) for x in range(0, W + 1, 20)]
        d.line(pts, fill=(90, 90, 96), width=90)
        d.line(pts, fill=CREAM, width=6)
        car_roll(c, t, Ls(18) + 0.3, 250, 1500, 500, dur=3.0, w=560)
    elif k == 19:
        panel(c, (30, 22, 22))
        stamp_at(c, "원인: 과속", W / 2 - 220, 380, Ls(19) + 0.6, t, 100)
        stamp_at(c, "커브 대처 실패", W / 2 + 230, 560, cs(19, 1) + 0.2, t, 84, 5)
        pop(c, text_img("LA 카운티 보안관 발표 · 2021-04-07", 32, CREAM, "Bold", stroke=4, sfill=(0, 0, 0)), W / 2, 720,
            cs(19, 1) + 0.5, t)
    elif k == 20:
        panel(c, (24, 24, 28))
        pop(c, tag("다리 중상", (120, 116, 110), WHITE, 80), W / 2 - 250, 460, Ls(20) + 0.3, t, -3)
        pop(c, tag("생존", AMBER, INK, 96), W / 2 + 250, 460, cs(20, 1), t, 3)
    elif k == 21:
        panel(c, (24, 24, 28))
        pop(c, tag("안전벨트 착용", (250, 246, 236), INK, 80), W / 2 - 280, 460, Ls(21) + 0.3, t, -2)
        pop(c, tag("에어백 작동", (250, 246, 236), INK, 80), W / 2 + 280, 460, Ls(21) + 1.6, t, 2)
    elif k == 22:
        panel(c, (30, 28, 24))
        pop(c, text_img("“", 260, YEL, "Black", shadow=0), 330, 300, Ls(22) + 0.1, t)
        q1 = "차 실내가 거의 온전했고,"
        q2 = "그게 살아남을 쿠션이 됐다"
        pop(c, text_img(q1, 80, WHITE, "Black", stroke=6, sfill=(0, 0, 0)), W / 2, 400, cs(22, 1), t)
        pop(c, text_img(q2, 80, YEL, "Black", stroke=6, sfill=(0, 0, 0)), W / 2, 530, cs(22, 2), t)
        pop(c, text_img("— 알렉스 비야누에바 LA 카운티 보안관, 2021년 2월 회견 (요약 번역)", 32, CREAM, "Bold", stroke=4,
                        sfill=(0, 0, 0)), W / 2, 660, cs(22, 2) + 0.4, t)
    elif k == 23:
        panel(c, (24, 24, 28))
        car = suv(900)
        paste(c, car, W / 2, 480)
        d = ImageDraw.Draw(c)
        x0, y0 = W / 2 - 450, 480 - car.height / 2
        p = prog(t, Ls(23) + 0.3, 0.4)
        if p > 0:
            d.rectangle((x0 + 760 * 900 / 620 * 0 + 900 * 0.80, y0 + 30, x0 + 900, y0 + car.height - 40), outline=RED, width=10)
            paste(c, tag("완전히 부서짐", RED, WHITE, 44), x0 + 900 * 0.9, y0 - 40)
        q = prog(t, cs(23, 1), 0.4)
        if q > 0:
            d.rectangle((x0 + 900 * 0.3, y0 + 40, x0 + 900 * 0.75, y0 + car.height * 0.62), outline=(80, 220, 120), width=10)
            paste(c, tag("버틴 공간", (80, 220, 120), INK, 44), x0 + 900 * 0.52, y0 + car.height + 50)
    elif k == 24:
        cr = full_photo(c, "gv90_gray_front", Ls(24), t, (1.0, 1.1), (0.5, 0.5), dark=0.25)
        pop(c, tag("2026.11", (250, 246, 236), INK, 60), W / 2, 260, Ls(24) + 0.5, t)
        big(c, "GV90", cs(24, 2), t, W / 2, 420, 200)
    elif k == 25:
        cr = full_photo(c, "gv90_white_front", Ls(25), t, (1.0, 1.08), (0.5, 0.5), dark=0.45)
        pop(c, tag("GV90  1억 3,950만 원부터", (250, 246, 236), INK, 64), W / 2, 330, Ls(25) + 0.5, t, -2)
        pop(c, tag("네오룬 4인승  2억 3,950만 원", AMBER, INK, 64), W / 2, 480, cs(25, 1) + 0.3, t, 2)
        pop(c, text_img("개별소비세 5% 기준 · 제네시스 발표(2026-11-10)", 30, CREAM, "Bold", stroke=4, sfill=(0, 0, 0)), W / 2,
            590, cs(25, 1) + 0.6, t)
    elif k == 26:
        panel(c, (20, 28, 26))
        d = ImageDraw.Draw(c)
        p = out_cubic(prog(t, Ls(26) + 0.2, 1.6))
        d.rounded_rectangle((W / 2 - 520, 300, W / 2 + 480, 520), 30, outline=CREAM, width=10)
        d.rectangle((W / 2 + 480, 370, W / 2 + 520, 450), fill=CREAM)
        d.rounded_rectangle((W / 2 - 500, 320, W / 2 - 500 + 960 * p, 500), 20, fill=(80, 220, 120))
        paste(c, text_img(f"{123.5 * p:.1f} kWh", 100, WHITE, "Black", stroke=6, sfill=(0, 0, 0)), W / 2, 410)
        pop(c, tag("그룹 전기차 중 최대", AMBER, INK, 52), W / 2 - 250, 620, cs(26, 1), t, -2)
        pop(c, tag("1회 충전 500km", (250, 246, 236), INK, 52), W / 2 + 300, 620, cs(26, 2), t, 2)
    elif k == 27:
        panel(c, (22, 26, 30))
        v = 490 * out_cubic(prog(t, Ls(27) + 0.4, 1.6))
        gauge(c, W / 2 - 200, 520, 300, v, 600, unit="kW")
        stamp_at(c, "그룹 최고 출력", W / 2 + 430, 440, cs(27, 1), t, 76)
    elif k == 28:
        cr = full_photo(c, "gv90_green_door", Ls(28), t, (1.0, 1.35), (0.5, 0.18), 0.5, dark=0.2)
        pop(c, tag("마주 보며 열리는 문", AMBER, INK, 56), W / 2, 300, Ls(28) + 0.5, t, -2)
        pop(c, tag("기둥은 문 안에", (250, 246, 236), INK, 56), W / 2, 440, cs(28, 1), t, 2)
    elif k == 29:
        panel(c, (26, 24, 30))
        p = in_out(prog(t, Ls(29) + 0.5, 1.4))
        d = ImageDraw.Draw(c)
        for (x, rot) in [(W / 2 - 230, 180 * p), (W / 2 + 230, 0)]:
            seat = Image.new("RGBA", (260, 300), (0, 0, 0, 0))
            sd = ImageDraw.Draw(seat)
            sd.rounded_rectangle((20, 0, 240, 90), 30, fill=(176, 168, 156), outline=INK, width=5)
            sd.rounded_rectangle((20, 100, 240, 290), 30, fill=(200, 192, 180), outline=INK, width=5)
            paste(c, seat, x, 470, 1, rot - 90 if x < W / 2 else 90)
        paste(c, text_img("앞좌석", 44, CREAM, "Black", stroke=4, sfill=(0, 0, 0)), W / 2 - 230, 690)
        paste(c, text_img("뒷좌석", 44, CREAM, "Black", stroke=4, sfill=(0, 0, 0)), W / 2 + 230, 690)
        pop(c, tag("180도 회전", AMBER, INK, 56), W / 2, 260, Ls(29) + 1.2, t)
    elif k == 30:
        panel(c, (30, 30, 34))
        pop(c, tag("자, 퀴즈!", RED, WHITE, 70), W / 2 - 60, 170, Ls(30), t)
        beat = countdown(c, t, W / 2 + 420, 520)
        for q, txt in enumerate(["10년", "14년", "18년"]):
            pk = out_back(prog(t, cs(30, 2) + 0.12 * q, 0.25))
            paste(c, option_chip(str(q + 1), txt), W / 2 - 250, 380 + q * 150, (pk + 0.001) * beat, 0, clamp(pk * 2))
    elif k == 31:
        panel(c, (30, 30, 34))
        for q, txt in enumerate(["10년", "14년", "18년"]):
            paste(c, option_chip(str(q + 1), txt, 1 if q == 2 else 2), W / 2 - 520, 190 + q * 105, 0.68)
        timeline_bar(c, t, Ls(31) + 0.1, 660, hl=(2008, 2026))
        big(c, "18년", Ls(31) + 0.3, t, W / 2 + 330, 340, 170)
    elif k == 32:
        cr = full_photo(c, "gv90_neolun_rear", Ls(32), t, (1.0, 1.08), dark=0.55)
        big(c, "세계 최초?", cs(32, 1), t, W / 2, 400, 150, YEL, -3)
    elif k == 33:
        panel(c, (22, 26, 30))
        rb = out_cubic(prog(t, Ls(33) + 0.6, 0.5))
        paste(c, suv(900, roofbag=round(rb, 2)), W / 2, 470)
        pop(c, tag("지붕 에어백", AMBER, INK, 70), W / 2, 190, Ls(33) + 0.6, t)
        pop(c, tag("전복(구를 때) 대비", (250, 246, 236), INK, 52), W / 2, 740, cs(33, 1), t)
    elif k == 34:
        panel(c, (30, 26, 24))
        d = ImageDraw.Draw(c)
        d.line([(x, 720) for x in range(0, W + 1, 40)], fill=(90, 90, 96), width=70)
        car_roll(c, t, Ls(34) + 0.2, 300, 1450, 560, dur=2.8, roofbag_at=0.18)
        pop(c, tag("구름 감지 → 순식간에 펼침", (250, 246, 236), INK, 52), W / 2, 220, Ls(34) + 0.8, t)
    elif k == 35:
        panel(c, (22, 26, 30))
        paste(c, suv(820, roofbag=1.0), W / 2, 500)
        pop(c, tag("튕겨 나감 막기", RED, WHITE, 56), W / 2 - 330, 220, Ls(35) + 0.4, t, -3)
        pop(c, tag("머리 부상 줄이기", RED, WHITE, 56), W / 2 + 330, 220, cs(35, 1), t, 3)
        pop(c, text_img("제네시스 GV90 발표 자료(2026-11-10) 설명", 30, CREAM, "Bold", stroke=4, sfill=(0, 0, 0)), W / 2, 790,
            cs(35, 1) + 0.6, t)
    elif k == 36:
        cr = full_photo(c, "gv80_white", Ls(36), t, (1.05, 1.12), dark=0.45, gray=True)
        big(c, "2021", Ls(36) + 0.2, t, W / 2, 400, 200, CREAM)
    elif k == 37:                                     # 왼쪽 2021 GV80(흑백) | 오른쪽 2026 GV90
        left = cover(photo("gv80_white"), W // 2, H, 1.1, 0.5, 0.5)
        left = Image.blend(left, left.convert("L").convert("RGBA"), 0.85)
        right = cover(photo("gv90_gray_front"), W // 2, H, 1.15, 0.5, 0.5)
        s = in_out(prog(t, Ls(37), 0.8))
        c.alpha_composite(left, (0, 0))
        c.alpha_composite(right, (int(W // 2 + (1 - s) * W // 2), 0))
        ImageDraw.Draw(c).rectangle((W // 2 - 4, 0, W // 2 + 4, H), fill=YEL)
        paste(c, tag("2021 · 구르던 차", (120, 116, 110), WHITE, 52), W / 4, 220)
        pop(c, tag("2026 · 구를 때까지 계산", AMBER, INK, 52), W * 3 / 4, 220, Ls(37) + 0.6, t)
        cr = "사진: MercurySable99 · Damian B Oh · CC BY-SA 4.0 · Wikimedia Commons (크롭)"
    elif k == 38:
        panel(c)
        timeline_bar(c, t, Ls(38), 520)
        pop(c, text_img("다음 이야기는, 어디까지?", 90, YEL, "Black", stroke=7, sfill=(0, 0, 0)), W / 2, 260, cs(38, 1), t)
    else:                                             # 39 끝 화면
        cr = full_photo(c, "gv90_gray_front", Ls(39) - 3, t, (1.1, 1.15), dark=0.6)
        p = out_back(prog(t, Ls(39) + 0.1, 0.4))
        paste(c, text_img("차를 읽는 시간", 150, WHITE, "Black", stroke=8, sfill=(0, 0, 0)), W / 2 - 80, 420, p + 0.001, 0,
              clamp(p * 2))
        paste(c, tag("옛날 차 이야기 · 숫자는 정확하게", AMBER, INK, 48), W / 2 - 80, 580, p + 0.001, 0, clamp(p * 2))
    return cr


def frame(i):
    t = i / FPS
    c = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    k = line_at(t)
    cr = scene(c, k, t)
    c.alpha_composite(vignette())
    if cr:
        credit(c, cr)
    chapter_pill(c, t)
    chapter_title(c, t)
    char(c, t)
    caption(c, t)
    ImageDraw.Draw(c).rectangle((0, 0, int(W * t / TL["total"]), 6), fill=AMBER)
    return c.convert("RGB")


# ------------------------------------------------------------------ 오디오·렌더
def build_audio(voice):
    sr = A.SR
    n = int(TL["total"] * sr)
    v = np.zeros(n)
    v[:len(voice)] = voice[:n]
    v = v / max(1e-9, np.abs(v).max()) * 0.92
    music = retro_bgm(TL["total"] + 1.0)[:n]
    act = np.convolve((np.abs(v) > 0.02).astype(float), np.ones(int(0.3 * sr)) / int(0.3 * sr), mode="same")
    music = music * (1 - 0.6 * np.clip(act * 4, 0, 1))[:, None] * 0.55
    ev = [(Ls(k) - CH_GAP, A.sfx_whoosh(0.5), 0.45) for k in CHAPTERS if k > 1]
    ev += [(Ls(2) + 0.2 + 0.7 * j, A.sfx_impact(), 0.35) for j in range(3)]
    ev += [(Ls(18) + 0.3 + 0.8 * j, A.sfx_impact(), 0.35) for j in range(3)]
    ev += [(Ls(9) + 0.5, stamp_sfx(), 0.8), (Ls(19) + 0.6, stamp_sfx(), 0.8), (cs(19, 1) + 0.2, stamp_sfx(), 0.7),
           (cs(17, 1), stamp_sfx(), 0.8), (Ls(17) + 0.4, A.sfx_riser(2.0), 0.3), (cs(27, 1), stamp_sfx(), 0.7),
           (Ls(30), A.sfx_ding(), 0.5), (Ls(31) + 0.3, A.sfx_ding(), 0.7), (Ls(33) + 0.6, A.sfx_whoosh(0.4), 0.5),
           (Ls(34) + 0.7, A.sfx_pop(), 0.6), (Ls(37), A.sfx_whoosh(0.6), 0.4), (Ls(39), A.sfx_riser(1.2), 0.3)]
    ev += [(st - 0.05, tick_sfx(), 0.9) for st, _ in TL["count"]]
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
        for k, (st, en, cap, _) in enumerate(TL["chunks"], 1):
            f.write(f"{k}\n{ts(st)} --> {ts(en)}\n{cap.replace('*', '')}\n\n")


def _render_part(args):
    i0, i1, path, tl = args
    TL.update(tl)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
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
    print("[total]", TL["total"])
    if a.preview is not None:
        for s in a.preview:
            p = os.path.join(BUILD, f"preview_{s:06.2f}.png")
            frame(int(s * FPS)).save(p)
            print(p)
        return
    for k, (st, en) in enumerate(TL["lines"], 1):
        print(f"{k:2d} {st:7.2f}-{en:7.2f}")
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
