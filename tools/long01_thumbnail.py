"""롱폼 01 썸네일 (1280×720): 왼쪽 2021 GV80(흑백) | 오른쪽 2026 GV90"""
import os, sys
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import long01_genesis as L
from PIL import Image, ImageDraw, ImageFilter
from video import rich_img, cover, paste
from ep_grandeur2 import INK, AMBER

W, H = 1920, 1080
c = Image.new("RGBA", (W, H), (0, 0, 0, 255))
left = cover(L.photo("gv80_white"), W // 2, H, 1.15, 0.45, 0.5)
left = Image.blend(left, left.convert("L").convert("RGBA"), 0.9)
right = cover(L.photo("gv90_gray_front"), W // 2, H, 1.2, 0.5, 0.55)
c.alpha_composite(left, (0, 0))
c.alpha_composite(right, (W // 2, 0))
c.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 110)))
ImageDraw.Draw(c).rectangle((W // 2 - 6, 0, W // 2 + 6, H), fill=(255, 212, 0))
paste(c, L.tag("2021 · 여러 번 구른 GV80", (120, 116, 110), (255, 255, 255), 54), W / 4, 110)
paste(c, L.tag("2026 · GV90", AMBER, INK, 54), W * 3 / 4, 110)
paste(c, rich_img("여러 번 구르고도", 120, 12), W / 2 - 150, 560)
paste(c, rich_img("*운전자는 살았다*", 150, 13), W / 2 - 150, 710)
paste(c, rich_img("이젠 *지붕 에어백*까지", 110, 12), W / 2 - 150, 870)
im = L.rig().frame("shock", 0.4, 0.5)
im = im.resize((int(im.width * 1.35), int(im.height * 1.35)))
c.alpha_composite(im, (W - im.width - 10, H - im.height + int(L.rig().pad * 1.35) - 20))
c.convert("RGB").resize((1280, 720)).save(os.path.join(L.ROOT, "output", "long01_genesis_gv90_thumbnail.jpg"), quality=92)
print("ok")
