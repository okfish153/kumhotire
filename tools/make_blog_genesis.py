"""제네시스 블로그 4편용 이미지 → assets/blog/genesis/
- 실사진: 1600px, 아래쪽에 저작자·라이선스 한 줄
- 설명 그림: 롱폼 01 장면을 자막·캐릭터 없이 깨끗하게 그려서 저장
사용법: python3 tools/make_blog_genesis.py
"""
import os, sys
sys.argv = sys.argv[:1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import long01_genesis as L
from PIL import Image
from video import text_img, paste

OUT = os.path.join(ROOT, "assets", "blog", "genesis")
os.makedirs(OUT, exist_ok=True)
L.CREDIT["eq900"] = "사진: Benespit · CC BY-SA 4.0 · Wikimedia Commons (크롭)"
L.FILES["eq900"] = "eq900_benespit.jpg"


def photo(key, name, fy=0.5):
    from video import cover
    im = cover(L.photo(key), 1600, 900, 1.0, 0.5, fy).convert("RGB").convert("RGBA")
    cr = L.CREDIT[key].replace(" (크롭·스티커 흐림)", " (크롭·일부 흐림)")
    t = text_img(cr, 24, (235, 235, 235), "SemiBold", shadow=3)
    band = Image.new("RGBA", (1600, 44), (0, 0, 0, 150))
    im.alpha_composite(band, (0, 856))
    im.alpha_composite(t, (20, 878 - t.height // 2))
    im.convert("RGB").save(os.path.join(OUT, name), quality=90)


def scene(k, frac, name):
    """롱폼 k번 장면을 그 문장의 frac 지점에서, 자막·캐릭터 없이"""
    st, en = L.TL["lines"][k - 1]
    t = st + (en - st) * frac
    c = Image.new("RGBA", (L.W, L.H), (0, 0, 0, 255))
    cr = L.scene(c, k, t)
    c.alpha_composite(L.vignette())
    if cr:
        L.credit(c, cr)
    c.convert("RGB").resize((1600, 900), Image.LANCZOS).save(os.path.join(OUT, name), quality=90)


L.load_timeline()
# 1편: 첫 제네시스
photo("bh_show", "01_1_bh_show.jpg")
photo("bh_front", "01_2_bh_front.jpg")
scene(9, 0.95, "01_3_award.jpg")
scene(5, 0.98, "01_4_timeline.jpg")
# 2편: 브랜드 독립과 GV80
scene(12, 0.97, "02_1_brand.jpg")
photo("eq900", "02_2_eq900.jpg")
photo("gv80_show", "02_3_gv80_show.jpg")
scene(14, 0.97, "02_4_gv80_face.jpg")
# 3편: 2021년 2월
photo("gv80_white", "03_1_gv80_white.jpg")
scene(17, 0.97, "03_2_speed.jpg")
scene(22, 0.98, "03_3_quote.jpg")
scene(23, 0.97, "03_4_cabin.jpg")
# 4편: GV90
photo("gv90_gray_front", "04_1_gv90_front.jpg", 0.55)
photo("gv90_green_door", "04_2_gv90_door.jpg", 0.5)
scene(26, 0.97, "04_3_battery.jpg")
scene(35, 0.97, "04_4_roof_airbag.jpg")
scene(37, 0.97, "04_5_2021_2026.jpg")
print(sorted(os.listdir(OUT)))
