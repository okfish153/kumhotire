"""차형 v3 기준 그림 한 장을 잘라 움직인다 (그림은 새로 그리지 않음).

부위: 머리(끄덕·갸웃·말할 때 들썩) / 몸 전체(점프·찌그러짐·흔들기·기울기) / 열쇠고리(흔들기·돌리기)
효과: ! ? 땀방울 반짝이 속도선 화살표 (그래픽으로 얹음)

    from tools.chahyung_motion import Chahyung
    ch = Chahyung(height=420)
    im = ch.frame("jump", t, energy=0.0)     # t: 동작 시작부터 지난 초, energy: 말소리 크기 0~1
    → RGBA 이미지, 발 가운데가 (im.width/2, im.height - ch.pad) 에 오도록 여백 포함

동작 이름: idle talk jump shock think awkward secret wind key_spin point_down nod cheer
시험 영상: python3 tools/chahyung_motion.py  → build/chahyung_motion/demo.mp4
"""
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "character", "chahyung_v3_base.png")
FONT = os.path.join(ROOT, "assets", "fonts", "Pretendard-Black.ttf")

HEAD_ELLIPSE = (180, -20, 1260, 985)      # 원본 좌표: 머리(귀·머리카락 포함)
NECK = (720, 975)                         # 머리 회전 중심
KEY_BOX = (0, 1012, 236, 1245)            # 열쇠고리(끈 + 자동차)
KEY_PIVOT = (128, 1012)                   # 주먹 아래 끈 시작점
FEET = (660, 2000)                        # 몸 전체 회전·찌그러짐 기준

AMBER, RED, INK, WHITE, SKY = (245, 166, 35), (220, 43, 44), (30, 30, 30), (255, 255, 255), (120, 190, 245)


def _ease(p):
    p = min(1, max(0, p))
    return p * p * (3 - 2 * p)


def _bounce(p):          # 0→1→0 한 번 튀기
    p = min(1, max(0, p))
    return math.sin(p * math.pi)


class Chahyung:
    def __init__(self, height=420, pad=60):
        base = Image.open(SRC).convert("RGBA")
        self.k = height / base.height
        self.pad = pad
        W, H = base.size
        a = np.asarray(base).copy()
        yy, xx = np.mgrid[0:H, 0:W]
        alpha = a[..., 3] > 0
        # 머리 마스크: 목 위쪽 전부(주먹·소매 제외) + 턱 아래는 타원 안쪽만
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).ellipse(HEAD_ELLIPSE, fill=255)
        ell = np.asarray(m) > 0
        fist = (xx < 300) & (yy > 800)
        head_mask = alpha & ~fist & ((yy < 860) | (ell & (yy < 990)))
        # 열쇠고리 마스크: 상자 안에서 빨간 슈트가 아닌 픽셀, 주먹 외곽선은 빼고 끈만
        x0, y0, x1, y1 = KEY_BOX
        red = (a[..., 0] > 150) & (a[..., 1] < 90) & (a[..., 2] < 90)
        inbox = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
        key_mask = inbox & alpha & ~red & ((yy > 1085) | ((np.abs(xx - KEY_PIVOT[0]) < 14) & (yy > 1032)))
        # 자동차에 이어진 덩어리만 남김(소매 외곽선 조각 제거)
        from scipy import ndimage
        lab, _ = ndimage.label(key_mask)
        keep = lab[1170, 120]
        if keep:
            key_mask = lab == keep
        head = a.copy(); head[..., 3] = np.where(head_mask, a[..., 3], 0)
        key = a.copy(); key[..., 3] = np.where(key_mask, a[..., 3], 0)
        body = a.copy(); body[..., 3] = np.where(head_mask | key_mask, 0, a[..., 3])
        # 머리가 기울 때 턱 아래가 비지 않게 깃 색으로 채움
        fill = head_mask & (yy > 900)
        body[fill] = (44, 44, 44, 255)
        sz = lambda im: im.resize((max(1, int(W * self.k)), max(1, int(H * self.k))), Image.LANCZOS)
        self.head, self.body, self.key = (sz(Image.fromarray(x, "RGBA")) for x in (head, body, key))
        self.W, self.H = self.body.size
        self.font = lambda s: ImageFont.truetype(FONT, s)

    # ------------------------------------------------------------ 동작 → 부위별 값
    def pose(self, motion, t, energy=0.0):
        """dx, dy(위로 +), rot(몸, 도), sx, sy, head_rot, head_dy, key_rot, fx(효과 목록)"""
        idle_b = math.sin(t * 2.4)
        p = dict(dx=0.0, dy=0.0, rot=0.0, sx=1 + 0.008 * idle_b, sy=1 - 0.008 * idle_b,
                 head_rot=1.5 * math.sin(t * 1.3), head_dy=0.0, key_rot=8 * math.sin(t * 2.0), fx=[])
        e = energy
        if motion == "talk":
            p["head_rot"] += 4 * e * math.sin(t * 9)
            p["head_dy"] = 6 * e * abs(math.sin(t * 11))
            p["dy"] = 4 * e * abs(math.sin(t * 7))
        elif motion == "jump" or motion == "cheer":
            c = (t % 1.1) / 1.1
            if c < 0.15:
                q = _ease(c / 0.15); p["sx"], p["sy"] = 1 + 0.10 * q, 1 - 0.12 * q
            elif c < 0.7:
                q = (c - 0.15) / 0.55; p["dy"] = 150 * _bounce(q); p["sx"], p["sy"] = 0.95, 1.07
                p["key_rot"] = -40 * math.sin(q * math.pi * 2)
            else:
                q = (c - 0.7) / 0.3; p["sx"], p["sy"] = 1 + 0.08 * _bounce(q), 1 - 0.09 * _bounce(q)
            p["head_rot"] = 6 * math.sin(t * 6)
            p["fx"] = ["sparkle"]
            if motion == "cheer":
                p["fx"].append("stars")
        elif motion == "shock":
            q = min(1, t / 0.25)
            p["dy"] = 60 * _bounce(q) if t < 0.25 else 0
            shake = 10 * math.exp(-t * 3) * math.sin(t * 60)
            p["dx"] = shake
            p["sx"] = p["sy"] = 1 + 0.06 * math.exp(-t * 2)
            p["head_rot"] = -5 * math.exp(-t * 2)
            p["key_rot"] = 35 * math.sin(t * 14) * math.exp(-t * 1.5)
            p["fx"] = ["bang"]
        elif motion == "think":
            q = _ease(t / 0.4)
            p["head_rot"] = 12 * q + 1.5 * math.sin(t * 2)
            p["rot"] = 3 * q
            p["fx"] = ["question"]
        elif motion == "awkward":
            q = _ease(t / 0.3)
            p["head_rot"] = -9 * q + 2 * math.sin(t * 5)
            p["sx"], p["sy"] = 1 + 0.03 * q, 1 - 0.05 * q
            p["dx"] = 3 * math.sin(t * 8)
            p["fx"] = ["sweat"]
        elif motion == "secret":
            q = _ease(t / 0.35)
            p["rot"] = -6 * q
            p["sx"] = p["sy"] = 1 + 0.06 * q
            p["head_rot"] = -8 * q + 2 * math.sin(t * 3)
            p["fx"] = ["shh"]
        elif motion == "wind":
            p["rot"] = -9 + 2.5 * math.sin(t * 13)
            p["dx"] = -14 + 4 * math.sin(t * 17)
            p["head_rot"] = -6 + 3 * math.sin(t * 15)
            p["key_rot"] = 75 + 10 * math.sin(t * 20)
            p["fx"] = ["speed"]
        elif motion == "key_spin":
            p["key_rot"] = (t * 540) % 360
            p["head_rot"] = 4 * math.sin(t * 4)
            p["dy"] = 6 * abs(math.sin(t * 4))
            p["fx"] = ["sparkle"]
        elif motion == "point_down":
            c = (t % 0.7) / 0.7
            p["dy"] = -18 * _bounce(c)
            p["head_rot"] = 6 + 3 * math.sin(t * 9)
            p["rot"] = -2
            p["fx"] = ["arrow"]
        elif motion == "nod":
            p["head_rot"] = 0
            p["head_dy"] = -10 * abs(math.sin(t * 6))
        if motion != "talk" and e > 0:              # 어떤 동작이든 말하는 동안은 머리가 살짝 들썩
            p["head_rot"] += 2.5 * e * math.sin(t * 9)
            p["head_dy"] += 4 * e * abs(math.sin(t * 11))
        return p

    # ------------------------------------------------------------ 그리기
    def frame(self, motion="idle", t=0.0, energy=0.0):
        p = self.pose(motion, t, energy)
        k, pad = self.k, self.pad
        cw, chh = self.W + pad * 2, self.H + pad * 2 + 200
        fig = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        fig.alpha_composite(self.body)
        # 열쇠고리: 끈 시작점 기준 회전
        kp = (KEY_PIVOT[0] * k, KEY_PIVOT[1] * k)
        fig.alpha_composite(self.key.rotate(p["key_rot"], Image.BICUBIC, center=kp))
        # 머리: 목 기준 회전 + 위아래
        nk = (NECK[0] * k, NECK[1] * k)
        hd = self.head.rotate(p["head_rot"], Image.BICUBIC, center=nk, translate=(0, -p["head_dy"]))
        fig.alpha_composite(hd)
        # 몸 전체: 찌그러짐(발 기준) → 회전(발 기준)
        fw, fh = int(self.W * p["sx"]), int(self.H * p["sy"])
        fig2 = fig.resize((fw, fh), Image.BICUBIC)
        canvas = Image.new("RGBA", (cw, chh), (0, 0, 0, 0))
        foot = (cw / 2 + p["dx"], chh - pad - p["dy"])
        canvas.alpha_composite(fig2, (int(foot[0] - FEET[0] * k * p["sx"]), int(foot[1] - fh)))
        canvas = canvas.rotate(p["rot"], Image.BICUBIC, center=foot)
        self._effects(canvas, p["fx"], t, foot, fh)
        return canvas

    def _effects(self, c, fx, t, foot, fh):
        d = ImageDraw.Draw(c)
        top = foot[1] - fh
        cx = c.width / 2
        if "bang" in fx:
            s = 1 + 0.25 * math.exp(-t * 6)
            f = self.font(int(110 * s))
            d.text((cx + self.W * 0.42, top + 30), "!", font=f, fill=AMBER, stroke_width=8, stroke_fill=INK, anchor="mm")
        if "question" in fx:
            for i, (ox, oy, sz) in enumerate([(0.40, 20, 100), (0.55, -40, 70)]):
                b = 10 * math.sin(t * 4 + i)
                d.text((cx + self.W * ox, top + oy + b), "?", font=self.font(sz), fill=WHITE, stroke_width=7,
                       stroke_fill=INK, anchor="mm")
        if "sweat" in fx:
            y = top + 110 + (t * 60) % 60
            x = cx + self.W * 0.36
            d.ellipse((x - 16, y - 4, x + 16, y + 34), fill=SKY, outline=INK, width=5)
            d.polygon([(x - 14, y + 8), (x, y - 26), (x + 14, y + 8)], fill=SKY)
            d.line([(x - 14, y + 8), (x, y - 26), (x + 14, y + 8)], fill=INK, width=5)
        if "shh" in fx:
            bx, by = cx + self.W * 0.40, top + 20 + 6 * math.sin(t * 5)
            d.rounded_rectangle((bx - 70, by - 45, bx + 70, by + 45), 30, fill=WHITE, outline=INK, width=6)
            d.polygon([(bx - 40, by + 40), (bx - 70, by + 80), (bx - 10, by + 42)], fill=WHITE)
            d.text((bx, by - 2), "쉿!", font=self.font(54), fill=INK, anchor="mm")
        if "speed" in fx:
            for i in range(7):
                y = top + 80 + i * (fh - 120) / 7
                ph = (t * 3.2 + i * 0.37) % 1
                x0 = c.width * (1 - ph)
                d.line((x0, y, x0 + 90 + 40 * (i % 3), y), fill=WHITE, width=8)
        if "sparkle" in fx or "stars" in fx:
            pts = [(0.15, 0.15), (0.85, 0.25), (0.10, 0.55), (0.92, 0.6)]
            for i, (ox, oy) in enumerate(pts):
                ph = (t * 1.5 + i * 0.25) % 1
                r = 26 * math.sin(ph * math.pi)
                if r > 1:
                    x, y = ox * c.width, top + oy * fh
                    star = [(x, y - r), (x + r * 0.3, y - r * 0.3), (x + r, y), (x + r * 0.3, y + r * 0.3),
                            (x, y + r), (x - r * 0.3, y + r * 0.3), (x - r, y), (x - r * 0.3, y - r * 0.3)]
                    d.polygon(star, fill=(255, 212, 0), outline=INK)
        if "arrow" in fx:
            ay = foot[1] - fh * 0.45 + 18 * abs(math.sin(t * 8))
            ax = cx - self.W * 0.62
            d.polygon([(ax - 34, ay - 60), (ax + 34, ay - 60), (ax + 34, ay), (ax + 62, ay), (ax, ay + 60),
                       (ax - 62, ay), (ax - 34, ay)], fill=(255, 212, 0), outline=INK)
            d.line([(ax - 34, ay - 60), (ax + 34, ay - 60), (ax + 34, ay), (ax + 62, ay), (ax, ay + 60),
                    (ax - 62, ay), (ax - 34, ay), (ax - 34, ay - 60)], fill=INK, width=6)


def demo():
    out = os.path.join(ROOT, "build", "chahyung_motion")
    os.makedirs(out, exist_ok=True)
    ch = Chahyung(height=560)
    moves = [("idle", "기본(숨쉬기·열쇠고리 흔들림)"), ("talk", "말하기(목소리에 맞춰 들썩)"), ("jump", "만세 점프"),
             ("shock", "깜짝 놀람"), ("think", "곰곰이"), ("awkward", "머쓱"), ("secret", "쉿, 비밀"),
             ("key_spin", "열쇠 돌리기"), ("wind", "센 바람(225마력)"), ("point_down", "댓글은 아래로"),
             ("cheer", "신남(반짝반짝)"), ("nod", "끄덕끄덕")]
    W, H, FPS, SEG = 1080, 1080, 30, 2.2
    f = ImageFont.truetype(FONT, 54)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                          os.path.join(out, "demo.mp4")], stdin=subprocess.PIPE)
    for name, label in moves:
        for i in range(int(SEG * FPS)):
            t = i / FPS
            bg = Image.new("RGBA", (W, H), (40, 44, 52, 255))
            energy = 0.5 + 0.5 * math.sin(t * 7) if name == "talk" else 0
            im = ch.frame(name, t, energy)
            bg.alpha_composite(im, ((W - im.width) // 2, H - im.height - 40))
            ImageDraw.Draw(bg).text((W / 2, 70), label, font=f, fill=WHITE, anchor="mm")
            p.stdin.write(bg.convert("RGB").tobytes())
    p.stdin.close(); p.wait()
    print(os.path.join(out, "demo.mp4"))


if __name__ == "__main__":
    demo()
