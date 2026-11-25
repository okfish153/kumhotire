"""차형 SNS 이미지 세트 (설정서 v3 색, 기준 그림 그대로)
실행: python3 tools/make_sns_assets.py → assets/character/sns/

- youtube_profile_800.png        유튜브 채널 프로필 (800×800, 원형으로 잘려 보임)
- youtube_banner_2560x1440.png   유튜브 채널 배너 (모든 기기 공통 안전 영역 1546×423 안에 핵심)
- youtube_watermark_150.png      유튜브 브랜딩 워터마크 (150×150, 투명)
- profile_1080.png               인스타그램·틱톡·네이버 프로필 (1080×1080, 원형으로 잘려 보임)
- ig_highlight_*.png             인스타그램 하이라이트 커버 (1080×1920, 가운데 원만 보임)
- _check_*.png                   확인용(안전 영역·원형 미리보기), 올리지 않음
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(ROOT, "assets", "character")
OUT = os.path.join(CH, "sns")
F = lambda w, s: ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", f"Pretendard-{w}.ttf"), s)
RED, PANEL, AMBER, WHITE, INK, CREAM = (220, 43, 44), (44, 44, 44), (245, 166, 35), (255, 253, 248), (30, 30, 30), (246, 236, 214)
CHANNEL = "차를 읽는 시간"
TAGLINE = "옛날 차 이야기 · 숫자는 정확하게, 이야기는 재미있게"
os.makedirs(OUT, exist_ok=True)

base = Image.open(os.path.join(CH, "chahyung_v3_base.png")).convert("RGBA")
BW, BH = base.size


def head_only():
    """머리+깃만 남긴 그림 (make_ip_assets.py와 같은 방식)"""
    m = Image.new("L", (BW, BH), 0)
    d = ImageDraw.Draw(m)
    d.ellipse((130, -60, 1340, 960), fill=255)
    d.polygon([(560, 900), (930, 900), (1000, 1040), (480, 1040)], fill=255)
    im = base.copy()
    im.putalpha(Image.composite(im.getchannel("A"), Image.new("L", (BW, BH), 0), m.filter(ImageFilter.GaussianBlur(2))))
    return im.crop((190, 0, 1280, 1090))


HEAD = head_only()


def circle_mask(size, ss=4):
    m = Image.new("L", (size * ss, size * ss), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size * ss - 1, size * ss - 1), fill=255)
    return m.resize((size, size), Image.LANCZOS)


def profile(size, bg=AMBER, ring=True, transparent_out=False):
    """원형으로 잘려 보이는 프로필: 앰버 원 + 머리, 바깥은 레드 줄 테두리"""
    c = Image.new("RGBA", (size, size), (0, 0, 0, 0) if transparent_out else bg + (255,))
    disk = Image.new("RGBA", (size, size), bg + (255,))
    c.alpha_composite(disk) if not transparent_out else None
    if ring:                                            # 레이싱 슈트처럼 레드·화이트 테두리
        d = ImageDraw.Draw(c)
        w = int(size * 0.045)
        d.ellipse((w / 2, w / 2, size - w / 2, size - w / 2), outline=RED, width=w)
        d.ellipse((w * 1.3, w * 1.3, size - w * 1.3, size - w * 1.3), outline=WHITE, width=max(2, w // 4))
    h = HEAD.resize((int(size * 0.82), int(size * 0.82)), Image.LANCZOS)
    c.alpha_composite(h, ((size - h.width) // 2, int(size * 0.13)))
    if transparent_out:
        return c
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(c, (0, 0), circle_mask(size))
    sq = Image.new("RGBA", (size, size), bg + (255,))      # 업로드용은 정사각(바깥도 앰버)
    sq.alpha_composite(out)
    return sq


def stripes(d, x0, y0, x1, y1, n=3, gap=26, w=14, color=RED):
    for k in range(n):
        o = k * gap
        d.polygon([(x0 + o, y1), (x0 + o + w, y1), (x1 + o + w, y0), (x1 + o, y0)], fill=color)


def banner():
    W, H = 2560, 1440
    c = Image.new("RGBA", (W, H), PANEL + (255,))
    d = ImageDraw.Draw(c)
    # 아스팔트 느낌의 아주 옅은 줄과 레이싱 줄무늬
    for y in range(0, H, 6):
        d.line((0, y, W, y), fill=(48, 48, 48))
    sx0, sy0 = (W - 1546) // 2, (H - 423) // 2          # 안전 영역 (507, 508) ~ (2053, 931)
    d.rectangle((0, sy0 + 423 - 18, W, sy0 + 423), fill=RED)  # 아래 레드 띠
    d.rectangle((0, sy0 + 423 + 8, W, sy0 + 423 + 14), fill=WHITE)
    stripes(d, sx0 - 330, sy0 + 40, sx0 - 230, sy0 + 380, n=4, gap=34, w=18, color=RED)
    stripes(d, sx0 + 1546 + 90, sy0 + 40, sx0 + 1546 + 190, sy0 + 380, n=4, gap=34, w=18, color=AMBER)
    # 차형: 안전 영역 오른쪽, 머리·가슴까지 보이게
    fig = base.resize((int(BW * 560 / BH * 1.0), 560), Image.LANCZOS)
    fig = fig.crop((0, 0, fig.width, 470))                # 아래 레드 띠 위로
    c.alpha_composite(fig, (sx0 + 1546 - fig.width + 20, sy0 + 423 - 18 - fig.height + 30))
    # 채널 이름과 한 줄 소개 (안전 영역 왼쪽)
    t1 = F("Black", 150)
    d.text((sx0 + 40, sy0 + 70), CHANNEL, font=t1, fill=WHITE, stroke_width=0)
    d.text((sx0 + 44, sy0 + 250), TAGLINE, font=F("Bold", 50), fill=CREAM)
    chip_x, chip_y = sx0 + 44, sy0 + 330
    txt = "매주 1분 쇼츠 · 해설 차형"
    tw = F("Black", 40).getlength(txt)
    d.rounded_rectangle((chip_x, chip_y, chip_x + tw + 60, chip_y + 64), 32, fill=AMBER)
    d.text((chip_x + 30, chip_y + 32), txt, font=F("Black", 40), fill=INK, anchor="lm")
    return c, (sx0, sy0, sx0 + 1546, sy0 + 423)


def watermark():
    s = 600
    im = profile(s, AMBER, ring=True)
    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.paste(im, (0, 0), circle_mask(s))
    return out.resize((150, 150), Image.LANCZOS)


def keychain_car():
    """기준 그림의 앰버 자동차 열쇠고리를 아이콘으로"""
    import numpy as np
    from scipy import ndimage
    box = (10, 1085, 236, 1245)
    car = base.crop(box)
    a = np.array(car)
    r, g, b, al = [a[..., i].astype(int) for i in range(4)]
    red = (r > 150) & (g < 90) & (b < 90)               # 소매(레드) 제외
    keep = (al > 20) & ~red
    lab, _ = ndimage.label(keep)
    k = lab[1170 - box[1], 120 - box[0]]
    if k == 0:                                          # 시작점이 빈칸이면 가장 큰 덩어리
        sizes = np.bincount(lab.ravel()); sizes[0] = 0; k = sizes.argmax()
    m = ndimage.binary_dilation(lab == k, iterations=2) & (al > 0)
    a[..., 3] = np.where(m, a[..., 3], 0)
    out = Image.fromarray(a.astype("uint8"))
    return out.crop(out.getbbox())


def highlight(kind):
    W, H = 1080, 1920
    c = Image.new("RGBA", (W, H), PANEL + (255,))
    d = ImageDraw.Draw(c)
    cx, cy, r = W // 2, H // 2, 330
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=AMBER if kind != "notice" else RED)
    d.ellipse((cx - r + 20, cy - r + 20, cx + r - 20, cy + r - 20), outline=WHITE, width=10)
    if kind == "chahyung":
        h = HEAD.resize((520, 520), Image.LANCZOS)
        c.alpha_composite(h, (cx - 260, cy - 250))
    elif kind == "grandeur":
        car = keychain_car()
        car = car.resize((int(car.width * 480 / car.width), int(car.height * 480 / car.width)), Image.LANCZOS)
        c.alpha_composite(car, (cx - car.width // 2, cy - car.height // 2))
    elif kind == "quiz":
        d.text((cx, cy - 10), "?", font=F("Black", 420), fill=WHITE, anchor="mm", stroke_width=14, stroke_fill=INK)
    else:
        d.text((cx, cy - 10), "!", font=F("Black", 420), fill=WHITE, anchor="mm", stroke_width=14, stroke_fill=INK)
    return c


def check_circle(im, size=300):
    """원형으로 잘렸을 때 모습"""
    im = im.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    out.paste(im, (0, 0), circle_mask(size))
    return out


if __name__ == "__main__":
    profile(800).convert("RGB").save(os.path.join(OUT, "youtube_profile_800.png"))
    profile(1080).convert("RGB").save(os.path.join(OUT, "profile_1080.png"))
    b, safe = banner()
    b.convert("RGB").save(os.path.join(OUT, "youtube_banner_2560x1440.png"))
    watermark().save(os.path.join(OUT, "youtube_watermark_150.png"))
    for k in ("grandeur", "chahyung", "quiz", "notice"):
        highlight(k).convert("RGB").save(os.path.join(OUT, f"ig_highlight_{k}.png"))
    # 확인용: 배너 안전 영역 표시, 프로필 원형 미리보기
    chk = b.copy()
    ImageDraw.Draw(chk).rectangle(safe, outline=(0, 255, 120), width=6)
    chk.convert("RGB").resize((1280, 720)).save(os.path.join(OUT, "_check_banner_safe_area.png"))
    row = Image.new("RGBA", (300 * 6 + 70, 300), (230, 230, 230, 255))
    items = [profile(800), profile(1080)] + [highlight(k).crop((540 - 330, 960 - 330, 540 + 330, 960 + 330))
                                              for k in ("grandeur", "chahyung", "quiz", "notice")]
    for i, im in enumerate(items):
        row.alpha_composite(check_circle(im), (i * 314, 0))
    row.convert("RGB").save(os.path.join(OUT, "_check_circles.png"))
    print("saved to", OUT)
