"""차형 IP 기본 이미지: 프로필(채널 아이콘), 실루엣, 작은 크기 확인 시트.
실행: python3 tools/make_ip_assets.py  → assets/character/ip/
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "character", "chahyung_v3_base.png")
OUT = os.path.join(ROOT, "assets", "character", "ip")
FONT = os.path.join(ROOT, "assets", "fonts", "Pretendard-Bold.ttf")
AMBER, RED, BLACK, CREAM, INK = (245, 166, 35), (220, 43, 44), (44, 44, 44), (255, 253, 248), (30, 30, 30)
os.makedirs(OUT, exist_ok=True)
base = Image.open(SRC).convert("RGBA")
W, H = base.size

# 머리 영역 (v3 기준 그림 1301x2019 기준). 정사각형으로 자른다.
FACE_BOX = (190, 0, 1280, 1090)


# 아이콘은 머리와 깃만: 머리(타원) + 목·깃 영역만 남기고 나머지는 투명
head_src = base.copy()
_m = Image.new("L", (W, H), 0)
_d = ImageDraw.Draw(_m)
_d.ellipse((130, -60, 1340, 960), fill=255)
_d.polygon([(560, 900), (930, 900), (1000, 1040), (480, 1040)], fill=255)
head_src.putalpha(Image.composite(head_src.getchannel("A"), Image.new("L", (W, H), 0), _m.filter(ImageFilter.GaussianBlur(2))))


def profile(size, bg, circle):
    head = head_src.crop(FACE_BOX).resize((int(size * 0.86), int(size * 0.86)), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    disk = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(disk).ellipse((0, 0, size - 1, size - 1), fill=bg + (255,))
    canvas.alpha_composite(disk if circle else Image.new("RGBA", (size, size), bg + (255,)))
    canvas.alpha_composite(head, ((size - head.width) // 2, size - head.height))
    if circle:
        mask = Image.new("L", (size * 4, size * 4), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
        mask = mask.resize((size, size), Image.LANCZOS)
        a = canvas.split()[3]
        canvas.putalpha(Image.composite(a, Image.new("L", a.size, 0), mask))
    return canvas


# 1) 채널 아이콘: 유튜브 권장 800x800 (유튜브가 원으로 잘라 보여줌)
profile(800, AMBER, circle=False).convert("RGB").save(os.path.join(OUT, "chahyung_profile_800.png"))
# 2) 원형 투명 버전 (SNS·스티커 시안용)
profile(800, AMBER, circle=True).save(os.path.join(OUT, "chahyung_profile_round_800.png"))
profile(800, BLACK, circle=True).save(os.path.join(OUT, "chahyung_profile_round_black_800.png"))

# 3) 실루엣 (검은 단색) — 그림자만으로 차형인지 확인
alpha = base.split()[3].point(lambda v: 255 if v > 128 else 0)
sil = Image.new("RGBA", base.size, (255, 255, 255, 255))
sil.paste(Image.new("RGBA", base.size, (0, 0, 0, 255)), (0, 0), alpha)
sil.convert("RGB").save(os.path.join(OUT, "chahyung_silhouette.png"))

# 4) 작은 크기 확인 시트: 밝은 배경 / 어두운 배경, 16~256px
sizes = [256, 128, 64, 48, 32, 16]
font = ImageFont.truetype(FONT, 22)
sheet = Image.new("RGB", (1400, 760), (244, 244, 244))
d = ImageDraw.Draw(sheet)
d.rectangle((0, 380, 1400, 760), fill=(24, 28, 36))
icon = profile(512, AMBER, circle=True)
for row, (y0, col) in enumerate([(40, INK), (420, (230, 230, 230))]):
    x = 40
    for s in sizes:
        im = icon.resize((s, s), Image.LANCZOS)
        sheet.paste(im, (x, y0 + (256 - s) // 2), im)
        d.text((x, y0 + 270), f"{s}px", font=font, fill=col)
        x += s + 60
    full = base.resize((int(W * 300 / H), 300), Image.LANCZOS)
    sheet.paste(full, (1400 - full.width - 60, y0 + 10), full)
sheet.save(os.path.join(OUT, "chahyung_size_check.png"))
print("saved to", OUT)
