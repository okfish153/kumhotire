/* IMAGE TETRIS – 이미지 블록 텍스처
 *
 * 스킨(skin) = 블록 7종 각각의 텍스처 캔버스 묶음.
 *  - slice   : 이미지 한 장을 블록 모양별 영역으로 잘라 적용
 *  - perPiece: 블록 7종에 각각 다른 이미지 적용
 * 각 텍스처 크기는 (texW × texH) 칸 × CELL px. 블록의 셀 (u,v) 위치를 잘라 그립니다.
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const U = IT.util;
  const { TYPES, PIECES } = IT.Pieces;
  const CELL = 96;

  // 한 장 분할 배치 (6×7 단위 격자 안에 7종 블록 상자를 겹치지 않게 배치)
  const SLICE_LAYOUT = {
    T: [0, 0], S: [3, 0], Z: [0, 2], J: [3, 2], L: [0, 4], O: [3, 4], I: [1, 6],
  };
  const SLICE_W = 6, SLICE_H = 7;

  function drawCover(ctx, img, sx, sy, sw, sh, dw, dh) {
    const r = U.coverRect(sw, sh, dw, dh);
    ctx.drawImage(img, sx + r.sx, sy + r.sy, r.sw, r.sh, 0, 0, dw, dh);
  }

  class TextureManager {
    constructor() { this.skins = new Map(); this._seq = 0; }

    _newKey(prefix) { return prefix + '#' + ++this._seq; }

    /** 이미지 한 장을 블록 모양별로 분할 */
    buildSlice(image) {
      const key = this._newKey('slice');
      const iw = image.width, ih = image.height;
      const unit = Math.min(iw / SLICE_W, ih / SLICE_H);
      const ox = (iw - unit * SLICE_W) / 2, oy = (ih - unit * SLICE_H) / 2;
      const pieces = {};
      for (const t of TYPES) {
        const P = PIECES[t];
        const [gx, gy] = SLICE_LAYOUT[t];
        const c = U.createCanvas(P.texW * CELL, P.texH * CELL);
        const ctx = c.getContext('2d');
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(image, ox + gx * unit, oy + gy * unit, P.texW * unit, P.texH * unit, 0, 0, c.width, c.height);
        pieces[t] = c;
      }
      this.skins.set(key, { pieces });
      return key;
    }

    /** 블록 7종에 각각 다른 이미지 (images: {T: canvas, ...}) */
    buildPerPiece(images) {
      const key = this._newKey('per');
      const pieces = {};
      for (const t of TYPES) {
        const img = images[t];
        if (!img) continue;
        const P = PIECES[t];
        const c = U.createCanvas(P.texW * CELL, P.texH * CELL);
        const ctx = c.getContext('2d');
        ctx.imageSmoothingQuality = 'high';
        drawCover(ctx, img, 0, 0, img.width, img.height, c.width, c.height);
        pieces[t] = c;
      }
      this.skins.set(key, { pieces });
      return key;
    }

    get(skin, type) {
      if (!skin) return null;
      const s = this.skins.get(skin);
      return s ? s.pieces[type] || null : null;
    }
    clear() { this.skins.clear(); }
  }

  TextureManager.CELL = CELL;
  TextureManager.SLICE_LAYOUT = SLICE_LAYOUT;
  IT.TextureManager = TextureManager;
})();
