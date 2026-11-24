/* IMAGE TETRIS – 캔버스 렌더러
 * - BlockPainter : 블록 한 칸 그리기 (단색 / 이미지 텍스처 + 테두리), 스프라이트 캐시
 * - BoardRenderer: 게임판 (배경 이미지, 격자, 고정 블록, 고스트, 현재 블록, 효과)
 * - drawPiecePreview: HOLD / NEXT 미리보기
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const U = IT.util;
  const { PIECES } = IT.Pieces;
  const FONT = '"Pretendard","Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",system-ui,-apple-system,sans-serif';

  class BlockPainter {
    constructor(textures) {
      this.textures = textures;
      this.colors = Object.assign({}, IT.Pieces.CLASSIC_COLORS);
      this.cache = new Map();
    }
    setColors(colors) { this.colors = Object.assign({}, IT.Pieces.CLASSIC_COLORS, colors || {}); this.cache.clear(); }
    color(type) { return this.colors[type] || '#999'; }
    clearCache() { this.cache.clear(); }

    /** 셀 스프라이트 (기기 픽셀 크기 px) */
    sprite(type, cell, px) {
      const tex = cell && cell.skin ? this.textures.get(cell.skin, type) : null;
      const key = tex ? `${cell.skin}|${type}|${cell.u}|${cell.v}|${cell.r}|${px}` : `${type}|${px}`;
      let c = this.cache.get(key);
      if (c) return c;
      c = U.createCanvas(px, px);
      const ctx = c.getContext('2d');
      const col = this.color(type);
      const r = Math.max(1, px * 0.12);
      if (tex) {
        const S = IT.TextureManager.CELL;
        ctx.save();
        U.roundRect(ctx, 0, 0, px, px, r * 0.7);
        ctx.clip();
        ctx.translate(px / 2, px / 2);
        ctx.rotate((cell.r * Math.PI) / 2);
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(tex, cell.u * S, cell.v * S, S, S, -px / 2, -px / 2, px, px);
        ctx.restore();
        // 입체감: 위쪽 하이라이트, 아래쪽 그림자
        const g = ctx.createLinearGradient(0, 0, px, px);
        g.addColorStop(0, 'rgba(255,255,255,.28)');
        g.addColorStop(0.45, 'rgba(255,255,255,0)');
        g.addColorStop(1, 'rgba(0,0,0,.22)');
        ctx.fillStyle = g;
        U.roundRect(ctx, 0, 0, px, px, r * 0.7);
        ctx.fill();
        // 블록 색 테두리 (이미지와 외곽선 구분)
        const lw = Math.max(1.5, px * 0.085);
        ctx.lineWidth = lw;
        ctx.strokeStyle = col;
        U.roundRect(ctx, lw / 2 + 0.5, lw / 2 + 0.5, px - lw - 1, px - lw - 1, r * 0.6);
        ctx.stroke();
        ctx.lineWidth = Math.max(1, px * 0.03);
        ctx.strokeStyle = 'rgba(0,0,0,.55)';
        U.roundRect(ctx, 0.5, 0.5, px - 1, px - 1, r * 0.7);
        ctx.stroke();
      } else {
        const g = ctx.createLinearGradient(0, 0, 0, px);
        g.addColorStop(0, U.shade(col, 0.28));
        g.addColorStop(0.5, col);
        g.addColorStop(1, U.shade(col, -0.25));
        ctx.fillStyle = g;
        U.roundRect(ctx, 0.5, 0.5, px - 1, px - 1, r);
        ctx.fill();
        // 안쪽 면
        const inset = px * 0.2;
        const g2 = ctx.createLinearGradient(0, inset, 0, px - inset);
        g2.addColorStop(0, U.shade(col, 0.18));
        g2.addColorStop(1, U.shade(col, -0.05));
        ctx.fillStyle = g2;
        U.roundRect(ctx, inset, inset, px - inset * 2, px - inset * 2, r * 0.6);
        ctx.fill();
        // 하이라이트
        ctx.fillStyle = 'rgba(255,255,255,.35)';
        U.roundRect(ctx, px * 0.12, px * 0.1, px * 0.36, px * 0.1, px * 0.05);
        ctx.fill();
        ctx.lineWidth = Math.max(1, px * 0.04);
        ctx.strokeStyle = U.shade(col, -0.45);
        U.roundRect(ctx, 0.5, 0.5, px - 1, px - 1, r);
        ctx.stroke();
      }
      this.cache.set(key, c);
      if (this.cache.size > 3000) this.cache.delete(this.cache.keys().next().value);
      return c;
    }

    draw(ctx, x, y, size, type, cell, dpr, alpha) {
      const px = Math.max(2, Math.round(size * dpr));
      const sp = this.sprite(type, cell, px);
      if (alpha != null && alpha < 1) { ctx.globalAlpha = alpha; ctx.drawImage(sp, x, y, size, size); ctx.globalAlpha = 1; }
      else ctx.drawImage(sp, x, y, size, size);
    }
    ghost(ctx, x, y, size, type, cell, dpr, textured) {
      const col = this.color(type);
      if (textured) this.draw(ctx, x, y, size, type, cell, dpr, 0.22);
      ctx.fillStyle = U.rgba(col, textured ? 0.08 : 0.16);
      U.roundRect(ctx, x + 1.5, y + 1.5, size - 3, size - 3, size * 0.14);
      ctx.fill();
      ctx.lineWidth = Math.max(1.5, size * 0.07);
      ctx.strokeStyle = U.rgba(col, 0.85);
      U.roundRect(ctx, x + 2, y + 2, size - 4, size - 4, size * 0.14);
      ctx.stroke();
    }
  }

  class BoardRenderer {
    constructor(canvas, painter, effects) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.painter = painter;
      this.fx = effects;
      this.cols = 10; this.rows = 20;
      this.cell = 24;
      this.dpr = 1;
      this.bg = { image: null, opacity: 0.6, dim: 0.3, theme: IT.Palette.DEFAULT_THEME, grid: true, pattern: false };
      this.bgLayer = null;
      this.vis = null;
      this.overT = -1;
      this.textured = false;
    }

    layout(maxW, maxH) {
      const cell = Math.max(8, Math.floor(Math.min(maxW / this.cols, maxH / this.rows)));
      this.cell = cell;
      this.dpr = Math.min(3, globalThis.devicePixelRatio || 1);
      const w = cell * this.cols, h = cell * this.rows;
      this.canvas.style.width = w + 'px';
      this.canvas.style.height = h + 'px';
      this.canvas.width = Math.round(w * this.dpr);
      this.canvas.height = Math.round(h * this.dpr);
      this.painter.clearCache();
      this._buildBg();
      return { width: w, height: h, cell };
    }

    setBackground(opts) { Object.assign(this.bg, opts); this._buildBg(); }

    _buildBg() {
      const w = this.canvas.width, h = this.canvas.height;
      if (!w || !h) return;
      const c = this.bgLayer && this.bgLayer.width === w && this.bgLayer.height === h ? this.bgLayer : U.createCanvas(w, h);
      const ctx = c.getContext('2d');
      const th = this.bg.theme || IT.Palette.DEFAULT_THEME;
      ctx.clearRect(0, 0, w, h);
      const g = ctx.createLinearGradient(0, 0, 0, h);
      g.addColorStop(0, U.shade(th.board, 0.06));
      g.addColorStop(1, th.board);
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, w, h);
      if (this.bg.pattern) {
        // 테마 모드: 팔레트 색으로 은은한 무늬
        const pal = th.palette || [];
        ctx.globalAlpha = 0.16;
        for (let i = 0; i < 14; i++) {
          ctx.fillStyle = pal[i % pal.length] || th.accent;
          const r = (0.12 + ((i * 37) % 23) / 60) * w;
          ctx.beginPath();
          ctx.arc(((i * 173) % 100) / 100 * w, ((i * 97) % 100) / 100 * h, r, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.globalAlpha = 1;
        ctx.fillStyle = U.rgba(th.board, 0.55);
        ctx.fillRect(0, 0, w, h);
      }
      const img = this.bg.image;
      if (img) {
        // 비율 유지(cover) – 왜곡 없음
        const r = U.coverRect(img.width, img.height, w, h);
        ctx.globalAlpha = U.clamp(this.bg.opacity, 0, 1);
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(img, r.sx, r.sy, r.sw, r.sh, 0, 0, w, h);
        ctx.globalAlpha = 1;
        if (this.bg.dim > 0) { ctx.fillStyle = `rgba(0,0,0,${U.clamp(this.bg.dim, 0, 0.95)})`; ctx.fillRect(0, 0, w, h); }
      }
      // 비네트
      const v = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.3, w / 2, h / 2, Math.max(w, h) * 0.75);
      v.addColorStop(0, 'rgba(0,0,0,0)');
      v.addColorStop(1, 'rgba(0,0,0,.35)');
      ctx.fillStyle = v;
      ctx.fillRect(0, 0, w, h);
      if (this.bg.grid) {
        const cs = this.cell * this.dpr;
        ctx.strokeStyle = 'rgba(255,255,255,.07)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let x = 1; x < this.cols; x++) { const px = Math.round(x * cs) + 0.5; ctx.moveTo(px, 0); ctx.lineTo(px, h); }
        for (let y = 1; y < this.rows; y++) { const py = Math.round(y * cs) + 0.5; ctx.moveTo(0, py); ctx.lineTo(w, py); }
        ctx.stroke();
      }
      this.bgLayer = c;
    }

    resetVisual() { this.vis = null; this.overT = -1; }
    startGameOver() { this.overT = 0; }

    render(engine, dt, opts = {}) {
      const ctx = this.ctx, cell = this.cell, dpr = this.dpr;
      const W = cell * this.cols, H = cell * this.rows;
      const hidden = engine.hidden;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      if (this.bgLayer) ctx.drawImage(this.bgLayer, 0, 0);
      let sx = 0, sy = 0;
      if (this.fx.shake > 0) { sx = (Math.random() - 0.5) * this.fx.shake; sy = (Math.random() - 0.5) * this.fx.shake; }
      ctx.setTransform(dpr, 0, 0, dpr, sx * dpr, sy * dpr);

      // 고정된 블록
      const overRow = this.overT >= 0 ? this.rows - Math.floor(this.overT / 28) : 99;
      for (let y = hidden; y < engine.rows; y++) {
        const row = engine.board[y];
        const vy = y - hidden;
        for (let x = 0; x < this.cols; x++) {
          const c = row[x];
          if (!c) continue;
          if (vy >= overRow) this._grey(ctx, x * cell, vy * cell, cell);
          else this.painter.draw(ctx, x * cell, vy * cell, cell, c.t, c, dpr);
        }
      }
      if (this.overT >= 0) this.overT += dt;

      const p = engine.piece;
      if (p && !engine.over) {
        const cells = engine.cellsOf(p);
        // 고스트
        if (opts.ghost !== false) {
          const gy = engine.ghostY();
          if (gy !== p.y) {
            for (const c of engine.cellsOf(p, p.x, gy, p.r)) {
              if (c.y < hidden) continue;
              this.painter.ghost(ctx, c.x * cell, (c.y - hidden) * cell, cell, p.type, { u: c.u, v: c.v, r: p.r, skin: p.skin }, dpr, !!p.skin);
            }
          }
        }
        // 현재 블록 (부드러운 이동)
        let ox = 0, oy = 0;
        if (opts.smooth !== false) {
          if (!this.vis || this.vis.ref !== p || this.vis.r !== p.r) this.vis = { ref: p, x: p.x, y: p.y, r: p.r };
          const k = 1 - Math.exp(-dt / 28);
          this.vis.x += (p.x - this.vis.x) * k;
          this.vis.y += (p.y - this.vis.y) * k;
          if (Math.abs(p.x - this.vis.x) > 2) this.vis.x = p.x;
          if (Math.abs(p.y - this.vis.y) > 2) this.vis.y = p.y;
          ox = this.vis.x - p.x; oy = this.vis.y - p.y;
        }
        const lockK = engine.grounded() ? Math.min(1, engine.lockTimer / engine.lockDelay) : 0;
        for (const c of cells) {
          const vy = c.y - hidden + oy;
          if (vy < -1) continue;
          this.painter.draw(ctx, (c.x + ox) * cell, vy * cell, cell, p.type, { u: c.u, v: c.v, r: p.r, skin: p.skin }, dpr);
          if (lockK > 0.05) { ctx.fillStyle = `rgba(255,255,255,${0.22 * lockK})`; ctx.fillRect((c.x + ox) * cell, vy * cell, cell, cell); }
        }
      }

      this.fx.drawBoardLayer(ctx, cell, this.cols);
      this.fx.drawParticles(ctx, cell);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      this.fx.drawTexts(ctx, W, H, cell, FONT);
    }

    _grey(ctx, x, y, s) {
      ctx.fillStyle = '#5b5f73';
      ctx.fillRect(x + 0.5, y + 0.5, s - 1, s - 1);
      ctx.fillStyle = 'rgba(255,255,255,.12)';
      ctx.fillRect(x + 2, y + 2, s - 4, s * 0.25);
    }
  }

  /** HOLD / NEXT 등 작은 미리보기 캔버스에 블록 그리기 */
  function drawPiecePreview(canvas, types, painter, skinFor, opts = {}) {
    const dpr = Math.min(3, globalThis.devicePixelRatio || 1);
    const cssW = canvas.clientWidth || canvas.width / dpr;
    const cssH = canvas.clientHeight || canvas.height / dpr;
    if (canvas.width !== Math.round(cssW * dpr) || canvas.height !== Math.round(cssH * dpr)) {
      canvas.width = Math.round(cssW * dpr); canvas.height = Math.round(cssH * dpr);
    }
    const ctx = canvas.getContext('2d');
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const list = (Array.isArray(types) ? types : [types]).filter(Boolean);
    if (!list.length) return;
    const slotH = cssH / list.length;
    list.forEach((t, i) => {
      const P = PIECES[t];
      const cells = P.states[0];
      const minX = Math.min(...cells.map((c) => c.x)), minY = Math.min(...cells.map((c) => c.y));
      const size = Math.min((cssW * 0.86) / 4, (slotH * 0.8) / 2.2, opts.maxCell || 40) * (i === 0 || !opts.shrink ? 1 : 0.8);
      const ox = (cssW - P.texW * size) / 2, oy = i * slotH + (slotH - P.texH * size) / 2;
      const skin = skinFor ? skinFor(t) : null;
      for (const c of cells) {
        painter.draw(ctx, ox + (c.x - minX) * size, oy + (c.y - minY) * size, size, t, { u: c.u, v: c.v, r: 0, skin }, dpr, opts.dim ? 0.35 : 1);
      }
    });
  }

  IT.Render = { BlockPainter, BoardRenderer, drawPiecePreview, FONT };
})();
