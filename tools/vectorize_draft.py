"""차형 기준 그림 → 색 단위 SVG 벡터 초안 (외부 패키지 없이 numpy+Pillow).
색을 설정서 팔레트로 나눈 뒤, 색마다 경계선을 따라 경로를 만들고 부드럽게 다듬는다.
디자이너가 다듬을 출발점용 초안이다. 실행: python3 tools/vectorize_draft.py
"""
import os
from collections import defaultdict
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "character", "chahyung_base.png")
OUT = os.path.join(ROOT, "assets", "character", "ip", "chahyung_vector_draft.svg")
SCALE = 0.5          # 작업 해상도 (원본의 절반)
TOL = 0.9            # 경로 단순화 허용 오차 (작업 픽셀)
MIN_AREA = 6         # 이보다 작은 조각은 버림
# 칠하는 순서 = 아래에서 위로. 외곽선(검정)은 맨 위.
PALETTE = [("white", "#FFFDF8"), ("pink", "#F8B4A6"), ("beige", "#D8C3A0"),
           ("navy", "#1F3A5F"), ("amber", "#F5A623"), ("line", "#1E1E1E")]


def hex2rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)


def labels(img):
    a = np.asarray(img).astype(float)
    rgb, alpha = a[..., :3], a[..., 3]
    pal = np.stack([hex2rgb(h) for _, h in PALETTE])
    dist = ((rgb[:, :, None, :] - pal[None, None]) ** 2).sum(-1)
    lab = dist.argmin(-1).astype(np.uint8) + 1
    lab[alpha < 128] = 0
    # 잡티 제거: 다수결 필터
    lab = np.asarray(Image.fromarray(lab).filter(ImageFilter.ModeFilter(5)))
    return lab


def loops(mask):
    """마스크 경계를 픽셀 모서리 좌표의 닫힌 고리들로 (안쪽이 왼쪽)."""
    h, w = mask.shape
    m = np.pad(mask, 1)
    nxt = defaultdict(list)
    # 위쪽 경계: (y,x) 안, (y-1,x) 밖 → 오른쪽→왼쪽 방향 등, 시계 반대 규칙
    ys, xs = np.nonzero(m[1:-1, 1:-1] & ~m[:-2, 1:-1]);   [nxt[(x + 1, y)].append((x, y)) for y, x in zip(ys, xs)]
    ys, xs = np.nonzero(m[1:-1, 1:-1] & ~m[2:, 1:-1]);    [nxt[(x, y + 1)].append((x + 1, y + 1)) for y, x in zip(ys, xs)]
    ys, xs = np.nonzero(m[1:-1, 1:-1] & ~m[1:-1, :-2]);   [nxt[(x, y)].append((x, y + 1)) for y, x in zip(ys, xs)]
    ys, xs = np.nonzero(m[1:-1, 1:-1] & ~m[1:-1, 2:]);    [nxt[(x + 1, y + 1)].append((x + 1, y)) for y, x in zip(ys, xs)]
    out = []
    while nxt:
        start = next(iter(nxt))
        ring, p = [start], start
        while True:
            q = nxt[p].pop()
            if not nxt[p]:
                del nxt[p]
            if q == start:
                break
            ring.append(q)
            p = q
            if p not in nxt:
                break
        if len(ring) >= 4:
            out.append(np.array(ring, float))
    return out


def rdp(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a
    n = np.hypot(*ab)
    v = pts - a
    d = np.abs(ab[0] * v[:, 1] - ab[1] * v[:, 0]) / n if n else np.hypot(*(pts - a).T)
    i = int(d.argmax())
    if d[i] > tol:
        return np.vstack([rdp(pts[:i + 1], tol)[:-1], rdp(pts[i:], tol)])
    return np.vstack([a, b])


def ring_path(r, k):
    # 닫힌 고리를 두 점에서 끊어 단순화
    j = len(r) // 2
    s = np.vstack([rdp(r[:j + 1], TOL)[:-1], rdp(np.vstack([r[j:], r[:1]]), TOL)[:-1]])
    if len(s) < 3:
        return ""
    s = s / k
    mids = (s + np.roll(s, -1, 0)) / 2
    f = lambda p: f"{p[0]:.1f} {p[1]:.1f}"
    d = [f"M{f(mids[-1])}"] + [f"Q{f(s[i])} {f(mids[i])}" for i in range(len(s))]
    return "".join(d) + "Z"


def area(r):
    x, y = r[:, 0], r[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def main():
    src = Image.open(SRC).convert("RGBA")
    W, H = src.size
    img = src.resize((int(W * SCALE), int(H * SCALE)), Image.LANCZOS)
    lab = labels(img)
    parts = []
    for idx, (name, hx) in enumerate(PALETTE, start=1):
        rings = [r for r in loops(lab == idx) if area(r) >= MIN_AREA]
        d = "".join(ring_path(r, SCALE) for r in rings)
        if d:
            parts.append(f'  <path id="{name}" fill="{hx}" fill-rule="evenodd" d="{d}"/>')
        print(name, len(rings), "paths")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">\n'
           f'  <!-- 차형 벡터 초안 (자동 변환, 디자이너 보정 전) -->\n' + "\n".join(parts) + "\n</svg>\n")
    open(OUT, "w").write(svg)
    print(OUT, f"{len(svg) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
