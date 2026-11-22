"""차형 사용 가이드 한 장 (A4 가로, 300dpi) → assets/character/ip/chahyung_style_guide.png / .pdf"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(ROOT, "assets", "character")
OUT = os.path.join(CH, "ip")
F = lambda w, s: ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", f"Pretendard-{w}.ttf"), s)
INK, AMBER, PAPER, GREY, RED, GREEN = (30, 30, 30), (245, 166, 35), (250, 247, 240), (110, 110, 110), (200, 50, 50), (40, 140, 80)
SUIT, PANEL = (220, 43, 44), (44, 44, 44)          # 설정서 v3 차형 레드·패널 블랙
W, H = 3508, 2480
pg = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(pg)
base = Image.open(os.path.join(CH, "chahyung_v3_base.png")).convert("RGBA")
sil = Image.open(os.path.join(OUT, "chahyung_silhouette.png")).convert("RGB")
prof = Image.open(os.path.join(OUT, "chahyung_profile_round_800.png")).convert("RGBA")


def fit(im, h):
    return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)


def heading(x, y, t):
    d.text((x, y), t, font=F("ExtraBold", 64), fill=PANEL)
    d.rectangle((x, y + 86, x + 120, y + 94), fill=SUIT)


# 머리말
d.rectangle((0, 0, W, 240), fill=PANEL)
d.rectangle((0, 232, W, 240), fill=SUIT)
d.text((140, 62), "차형 캐릭터 사용 가이드", font=F("Black", 104), fill=(255, 255, 255))
d.text((1501, 152), "차를 읽는 시간 · v3 · 2026-11", font=F("Bold", 51), fill=AMBER, anchor="ls")

# 1. 기준 그림
heading(140, 320, "기준 그림")
im = fit(base, 1500)
pg.paste(im, (180, 470), im)
d.text((140, 2010), "확정본: chahyung_v3_base.png", font=F("SemiBold", 40), fill=GREY)
d.text((140, 2070), "얼굴·색·비율은 어떤 버전에서도 바꾸지 않습니다.", font=F("SemiBold", 40), fill=GREY)

# 2. 색상표
X2 = 1300
heading(X2, 320, "색상")
cols = [("차형 레드", "레이싱 슈트", "#DC2B2C"), ("패널 블랙", "옆구리 패널 · 깃 · 벨트 · 머리", "#2C2C2C"),
        ("차형 앰버", "지퍼 · 열쇠 · 신발", "#F5A623"), ("마시멜로 화이트", "얼굴 · 손 · 줄무늬 · 글자", "#FFFDF8"),
        ("볼 핑크", "볼", "#FAB4BC"), ("외곽선", "모든 선", "#1E1E1E")]
for i, (n, u, hx) in enumerate(cols):
    y = 470 + i * 170
    rgb = tuple(int(hx[k:k + 2], 16) for k in (1, 3, 5))
    d.rounded_rectangle((X2, y, X2 + 140, y + 140), 24, fill=rgb, outline=INK, width=4)
    d.text((X2 + 175, y + 8), n, font=F("Bold", 50), fill=INK)
    d.text((X2 + 175, y + 76), f"{hx}  ·  {u}", font=F("SemiBold", 38), fill=GREY)

# 3. 꼭 지킬 것
heading(X2, 1540, "꼭 지킬 것")
rules = ["웃는 실눈 + 발그레한 볼 + 마시멜로 얼굴", "2등신 (머리 : 몸 = 1 : 1)",
         "모자 없이 짧은 검은 머리, 옆머리만 희끗", "빨간 레이싱 슈트 + 검은 옆구리 패널·깃·벨트",
         "가슴에 CHAHYUNG 한 줄, 다른 글자·로고 없음", "앰버 자동차 열쇠고리 (정지: 늘어뜨림 · 동작: 검지)",
         "굵고 일정한 검은 외곽선, 단색 채색"]
for i, r in enumerate(rules):  # 설정서 v3 기준 7개
    cy = 1700 + i * 86
    d.ellipse((X2 + 1, cy - 20, X2 + 41, cy + 20), fill=GREEN)
    d.text((X2 + 68, cy), r, font=F("Bold", 44), fill=INK, anchor="lm")

# 4. 실루엣 + 최소 크기
X3 = 2420
heading(X3, 320, "실루엣 · 최소 크기")
s = fit(sil, 560)
pg.paste(s, (X3, 470))
p = prof.resize((300, 300), Image.LANCZOS); pg.paste(p, (X3 + 470, 480), p)
p = prof.resize((96, 96), Image.LANCZOS); pg.paste(p, (X3 + 820, 684), p)
d.text((X3 + 470, 810), "화면: 아이콘 32px 이상", font=F("Bold", 40), fill=INK)
d.text((X3 + 470, 870), "인쇄: 얼굴 지름 10mm 이상", font=F("Bold", 40), fill=INK)
d.text((X3 + 470, 930), "주변 여백: 얼굴 폭의 1/4", font=F("Bold", 40), fill=INK)


# 5. 하지 마세요
heading(X3, 1120, "하지 마세요")
small = fit(base, 380)
arr = np.array(small).astype(np.int16)
hue = arr.copy(); hue[..., [0, 1, 2]] = arr[..., [2, 0, 1]]            # 색 바꾸기
wrong = [("색 바꾸기", Image.fromarray(hue.clip(0, 255).astype(np.uint8), "RGBA")),
         ("늘이기", small.resize((small.width, int(small.height * 1.35))).crop((0, 0, small.width, 380)).resize((int(small.width * 0.7), 380))),
         ("로고 붙이기", small.copy())]
dd = ImageDraw.Draw(wrong[2][1])
dd.rectangle((52, 205, 132, 245), fill=(200, 200, 200), outline=INK, width=3)
dd.text((60, 208), "LOGO", font=F("Black", 26), fill=INK)
for i, (t, im) in enumerate(wrong):
    x = X3 + i * 340
    pg.paste(im, (x + (300 - im.width) // 2, 1270), im)
    d.line((x + 20, 1290, x + 280, 1630), fill=RED, width=14)
    d.line((x + 280, 1290, x + 20, 1630), fill=RED, width=14)
    d.text((x + 150, 1690), t, font=F("Bold", 44), fill=RED, anchor="ma")
d.text((X3, 1800), "· 다른 회사·레이싱팀 로고, 스폰서 패치를 붙이지 않기", font=F("SemiBold", 40), fill=INK)
d.text((X3, 1860), "· 술·담배, 위험 운전과 함께 쓰지 않기", font=F("SemiBold", 40), fill=INK)
d.text((X3, 1920), "· 대비가 약한 빨간 배경 위에 그대로 올리지 않기", font=F("SemiBold", 40), fill=INK)
d.text((X3, 1980), "  (흰 테두리나 앰버 원 배경을 깔기)", font=F("SemiBold", 40), fill=GREY)

# 꼬리말
d.line((140, 2300, W - 140, 2300), fill=(210, 205, 195), width=4)
d.text((140, 2340), "© 차를 읽는 시간. 캐릭터 '차형'의 이름과 모습은 허락 없이 상업적으로 쓸 수 없습니다.",
       font=F("SemiBold", 40), fill=GREY)
pg.save(os.path.join(OUT, "chahyung_style_guide.png"), dpi=(300, 300))
pg.save(os.path.join(OUT, "chahyung_style_guide.pdf"), resolution=300.0, title="chahyung_style_guide_v3")
print("ok")
