"""제미나이에서 만든 초록 배경(#00FF00) 그림의 배경을 지운다.

- 초록이 빨강·파랑보다 얼마나 센지로 투명도를 정하고, 가장자리의 초록 번짐을 없앤다.
- 캐릭터와 떨어진 작은 조각(제미나이 반짝이 표시 등)은 지운다.
- 그림 둘레를 여백 20px만 남기고 자른다.

사용법
  python3 tools/green_key.py 입력.png 출력.png
  python3 tools/green_key.py 폴더/*.png --out-dir assets/character/poses
"""
import argparse
import os

import numpy as np
from PIL import Image
from scipy import ndimage


def key(im, t0=25, t1=90, keep_ratio=0.02, margin=20):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    spill = g - np.maximum(r, b)
    alpha = 1 - np.clip((spill - t0) / (t1 - t0), 0, 1)
    # 가장자리 초록 번짐 제거
    over = g > np.maximum(r, b)
    a[..., 1] = np.where(over & (alpha < 1) | (spill > 8), np.maximum(r, b), g)
    # 작은 조각 지우기
    solid = alpha > 0.5
    lab, n = ndimage.label(solid)
    if n:
        sizes = ndimage.sum(solid, lab, range(1, n + 1))
        keep = np.isin(lab, 1 + np.flatnonzero(sizes >= sizes.max() * keep_ratio))
        keep = ndimage.binary_dilation(keep, iterations=3)
        alpha = alpha * keep
    out = Image.fromarray(np.dstack([a, alpha * 255]).clip(0, 255).astype(np.uint8), "RGBA")
    bb = out.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if bb:
        l, t, rr, bt = bb
        out = out.crop((max(0, l - margin), max(0, t - margin), min(out.width, rr + margin), min(out.height, bt + margin)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out-dir")
    a = ap.parse_args()
    if not a.out_dir and len(a.inputs) == 2:
        key(Image.open(a.inputs[0])).save(a.inputs[1])
        print(a.inputs[1])
        return
    os.makedirs(a.out_dir, exist_ok=True)
    for p in a.inputs:
        o = os.path.join(a.out_dir, os.path.splitext(os.path.basename(p))[0] + ".png")
        key(Image.open(p)).save(o)
        print(o)


if __name__ == "__main__":
    main()
