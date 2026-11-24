/* IMAGE TETRIS – 이미지 완성 영역 (조각 공개 애니메이션)
 * mode: 'reveal'  – RevealProgress 에 따라 조각 공개
 *       'preview' – 전체 이미지 표시 (이미지 배경/블록/테마 모드)
 *       'mystery' – 이미지 없이 물음표 (다음 이미지 미리보기 숨김)
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const U = IT.util;

  class RevealView {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.image = null;
      this.progress = null;
      this.mode = 'preview';
      this.anim = new Map(); // tileIndex → t(ms)
      this.theme = IT.Palette.DEFAULT_THEME;
      this.completeT = -1;
      this.dpr = 1;
    }
    set(image, progress, mode) {
      this.image = image; this.progress = progress || null; this.mode = mode || (progress ? 'reveal' : 'preview');
      this.anim.clear(); this.completeT = -1;
    }
    setTheme(t) { this.theme = t; }
    revealTiles(indices) { for (const i of indices) this.anim.set(i, 0); }
    celebrate() { this.completeT = 0; }
    get animating() { return this.anim.size > 0 || (this.completeT >= 0 && this.completeT < 1600); }

    resize() {
      const dpr = Math.min(3, globalThis.devicePixelRatio || 1);
      const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
      if (!w || !h) return false;
      this.dpr = dpr;
      if (this.canvas.width !== Math.round(w * dpr) || this.canvas.height !== Math.round(h * dpr)) {
        this.canvas.width = Math.round(w * dpr); this.canvas.height = Math.round(h * dpr);
      }
      return true;
    }

    render(dt) {
      if (!this.resize()) return;
      const ctx = this.ctx, dpr = this.dpr;
      const W = this.canvas.width / dpr, H = this.canvas.height / dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);
      const th = this.theme;
      const img = this.image;
      const aspect = img ? img.width / img.height : 3 / 4;
      const r = U.containRect(aspect * 100, 100, W - 4, H - 4);
      r.x += 2; r.y += 2;
      ctx.save();
      U.roundRect(ctx, r.x, r.y, r.w, r.h, 10);
      ctx.clip();
      ctx.fillStyle = U.shade(th.panel || '#222', -0.25);
      ctx.fillRect(r.x, r.y, r.w, r.h);

      if (this.mode === 'mystery' || !img) {
        this._cover(ctx, r.x, r.y, r.w, r.h, 0, true);
        ctx.restore();
        this._frame(ctx, r);
        return;
      }
      if (this.mode === 'preview') {
        ctx.drawImage(img, r.x, r.y, r.w, r.h);
        ctx.restore();
        this._frame(ctx, r);
        return;
      }
      const p = this.progress;
      const tw = r.w / p.cols, thh = r.h / p.rows;
      for (let i = 0; i < p.total; i++) {
        const cx = i % p.cols, cy = Math.floor(i / p.cols);
        const x = r.x + cx * tw, y = r.y + cy * thh;
        const sx = (cx / p.cols) * img.width, sy = (cy / p.rows) * img.height;
        const sw = img.width / p.cols, sh = img.height / p.rows;
        const revealed = p.isRevealed(i);
        if (!revealed) { this._cover(ctx, x, y, tw, thh, i, false); continue; }
        if (this.anim.has(i)) {
          const t = this.anim.get(i) + dt;
          this.anim.set(i, t);
          const k = Math.min(1, t / 520);
          // 카드 뒤집기: 덮개가 접히고 이미지가 펼쳐짐
          if (k < 0.5) {
            const s = 1 - k * 2;
            ctx.save(); ctx.translate(x + tw / 2, y); ctx.scale(Math.max(0.001, s), 1);
            this._cover(ctx, -tw / 2, 0, tw, thh, i, false); ctx.restore();
          } else {
            const s = (k - 0.5) * 2;
            ctx.save(); ctx.translate(x + tw / 2, y); ctx.scale(Math.max(0.001, s), 1);
            ctx.drawImage(img, sx, sy, sw, sh, -tw / 2, 0, tw, thh);
            ctx.fillStyle = `rgba(255,255,255,${0.55 * (1 - s)})`;
            ctx.fillRect(-tw / 2, 0, tw, thh);
            ctx.restore();
          }
          if (k >= 1) this.anim.delete(i);
        } else {
          ctx.drawImage(img, sx, sy, sw, sh, x, y, tw + 0.5, thh + 0.5);
        }
      }
      // 조각 경계선 (완성 전)
      if (!p.complete || this.completeT < 0) {
        ctx.strokeStyle = 'rgba(0,0,0,.25)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        for (let i = 1; i < p.cols; i++) { ctx.moveTo(r.x + i * tw, r.y); ctx.lineTo(r.x + i * tw, r.y + r.h); }
        for (let i = 1; i < p.rows; i++) { ctx.moveTo(r.x, r.y + i * thh); ctx.lineTo(r.x + r.w, r.y + i * thh); }
        ctx.stroke();
      }
      if (this.completeT >= 0) {
        this.completeT += dt;
        const k = Math.min(1, this.completeT / 1600);
        const bandX = r.x - r.w + k * r.w * 3;
        const g = ctx.createLinearGradient(bandX - 60, 0, bandX + 60, 0);
        g.addColorStop(0, 'rgba(255,255,255,0)');
        g.addColorStop(0.5, 'rgba(255,255,255,.55)');
        g.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = g;
        ctx.fillRect(r.x, r.y, r.w, r.h);
      }
      ctx.restore();
      this._frame(ctx, r, this.completeT >= 0);
    }

    _cover(ctx, x, y, w, h, i, big) {
      const th = this.theme;
      const pal = th.palette && th.palette.length ? th.palette : [th.accent];
      const base = U.shade(th.panel || '#2a2a44', 0.05 + ((i * 7) % 5) * 0.02);
      ctx.fillStyle = base;
      ctx.fillRect(x + 1, y + 1, w - 2, h - 2);
      ctx.fillStyle = U.rgba(pal[i % pal.length], 0.18);
      ctx.fillRect(x + 1, y + 1, w - 2, h * 0.35);
      ctx.fillStyle = 'rgba(255,255,255,.55)';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const fs = big ? Math.min(w, h) * 0.35 : Math.min(w, h) * 0.42;
      ctx.font = `900 ${fs}px ${IT.Render.FONT}`;
      ctx.fillText('?', x + w / 2, y + h / 2 + fs * 0.04);
    }
    _frame(ctx, r, glow) {
      ctx.save();
      ctx.lineWidth = glow ? 3 : 2;
      ctx.strokeStyle = glow ? '#ffe27a' : U.rgba(this.theme.accent || '#8b7bff', 0.7);
      if (glow) { ctx.shadowColor = '#ffe27a'; ctx.shadowBlur = 14; }
      U.roundRect(ctx, r.x, r.y, r.w, r.h, 10);
      ctx.stroke();
      ctx.restore();
    }
  }

  IT.RevealView = RevealView;
})();
