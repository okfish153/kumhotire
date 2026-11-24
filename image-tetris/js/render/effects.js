/* IMAGE TETRIS – 시각 효과 (파티클, 줄 제거 플래시, 착지 효과, 떠오르는 문구)
 * 효과는 게임 판정과 완전히 분리되어 있으며, 그리기 전용입니다.
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const MAX_PARTICLES = 500;

  class Effects {
    constructor() {
      this.particles = [];
      this.strips = [];
      this.flashes = [];
      this.texts = [];
      this.trails = [];
      this.reduced = false;
      this.shake = 0;
    }
    clear() { this.particles = []; this.strips = []; this.flashes = []; this.texts = []; this.trails = []; this.shake = 0; }

    lineClear(rows, colorOf, cols) {
      for (const row of rows) {
        this.strips.push({ y: row.y, t: 0, life: 320 });
        if (row.y < 0) continue;
        const per = this.reduced ? 1 : 3;
        for (let x = 0; x < cols; x++) {
          const color = colorOf(row.cells[x]);
          for (let k = 0; k < per; k++) {
            if (this.particles.length >= MAX_PARTICLES) break;
            const a = Math.random() * Math.PI * 2, sp = 0.04 + Math.random() * 0.18;
            this.particles.push({
              x: x + 0.5, y: row.y + 0.5,
              vx: Math.cos(a) * sp * (x < cols / 2 ? -1 : 1) * (0.4 + Math.random()), vy: Math.sin(a) * sp - 0.12,
              size: 0.18 + Math.random() * 0.3, color, t: 0, life: 600 + Math.random() * 500, rot: Math.random() * 6, vr: (Math.random() - 0.5) * 0.02,
            });
          }
        }
      }
      if (rows.length >= 4) this.shake = Math.max(this.shake, this.reduced ? 3 : 7);
    }
    land(cells, color) {
      this.flashes.push({ cells: cells.filter((c) => c.y >= 0), t: 0, life: 160, color });
    }
    hardDrop(cells, fromY, color) {
      if (this.reduced) return;
      const minY = Math.min(...cells.map((c) => c.y));
      const dist = minY - fromY;
      if (dist <= 0) return;
      const xs = Array.from(new Set(cells.map((c) => c.x)));
      for (const x of xs) {
        const top = Math.min(...cells.filter((c) => c.x === x).map((c) => c.y));
        this.trails.push({ x, y1: top - dist, y2: top, t: 0, life: 220, color });
      }
      this.shake = Math.max(this.shake, 2.5);
    }
    text(main, sub, color, big) {
      // 같은 시점 문구가 겹치지 않도록 위로 쌓기
      const offset = this.texts.filter((t) => t.t < 300).length;
      this.texts.push({ main, sub, color, big: !!big, t: 0, life: big ? 1300 : 1000, offset });
    }
    confetti(cols, rows, colors, amount = 160) {
      const n = this.reduced ? Math.floor(amount / 3) : amount;
      for (let i = 0; i < n && this.particles.length < MAX_PARTICLES; i++) {
        this.particles.push({
          x: Math.random() * cols, y: -1 - Math.random() * 4,
          vx: (Math.random() - 0.5) * 0.06, vy: 0.04 + Math.random() * 0.08,
          size: 0.2 + Math.random() * 0.25, color: colors[i % colors.length], t: 0, life: 1800 + Math.random() * 1200,
          rot: Math.random() * 6, vr: (Math.random() - 0.5) * 0.02, confetti: true,
        });
      }
    }

    update(dt) {
      const step = (arr) => { for (const p of arr) p.t += dt; return arr.filter((p) => p.t < p.life); };
      for (const p of this.particles) {
        p.x += p.vx * dt * 0.06; p.y += p.vy * dt * 0.06;
        p.vy += (p.confetti ? 0.00002 : 0.0004) * dt;
        if (p.confetti) p.vx += Math.sin((p.t + p.rot * 100) / 300) * 0.0002 * dt;
        p.rot += p.vr * dt;
      }
      this.particles = step(this.particles);
      this.strips = step(this.strips);
      this.flashes = step(this.flashes);
      this.texts = step(this.texts);
      this.trails = step(this.trails);
      this.shake = Math.max(0, this.shake - dt * 0.03);
    }

    drawBoardLayer(ctx, cell, cols) {
      // 하드드롭 잔상
      for (const tr of this.trails) {
        const k = 1 - tr.t / tr.life;
        const g = ctx.createLinearGradient(0, tr.y1 * cell, 0, tr.y2 * cell);
        g.addColorStop(0, 'rgba(255,255,255,0)');
        g.addColorStop(1, IT.util.rgba(tr.color, 0.32 * k));
        ctx.fillStyle = g;
        ctx.fillRect(tr.x * cell + cell * 0.1, tr.y1 * cell, cell * 0.8, (tr.y2 - tr.y1) * cell);
      }
      // 착지 플래시
      for (const f of this.flashes) {
        const k = 1 - f.t / f.life;
        ctx.fillStyle = `rgba(255,255,255,${0.55 * k})`;
        for (const c of f.cells) ctx.fillRect(c.x * cell, c.y * cell, cell, cell);
      }
      // 줄 제거 빛줄기
      for (const s of this.strips) {
        if (s.y < 0) continue;
        const k = s.t / s.life;
        const a = 1 - k;
        const h = cell * (1 + k * 0.6);
        const cy = s.y * cell + cell / 2;
        const g = ctx.createLinearGradient(0, cy - h / 2, 0, cy + h / 2);
        g.addColorStop(0, 'rgba(255,255,255,0)');
        g.addColorStop(0.5, `rgba(255,255,255,${0.9 * a})`);
        g.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = g;
        const w = cols * cell * Math.min(1, 0.3 + k * 2);
        ctx.fillRect((cols * cell - w) / 2, cy - h / 2, w, h);
      }
    }
    drawParticles(ctx, cell) {
      for (const p of this.particles) {
        const k = 1 - p.t / p.life;
        ctx.globalAlpha = Math.min(1, k * 1.6);
        ctx.fillStyle = p.color;
        const s = p.size * cell;
        ctx.save();
        ctx.translate(p.x * cell, p.y * cell);
        ctx.rotate(p.rot);
        if (p.confetti) ctx.fillRect(-s / 2, -s / 4, s, s / 2);
        else ctx.fillRect(-s / 2, -s / 2, s, s);
        ctx.restore();
      }
      ctx.globalAlpha = 1;
    }
    drawTexts(ctx, w, h, cell, font) {
      for (const t of this.texts) {
        const p = t.t / t.life;
        const appear = Math.min(1, t.t / 140);
        const scale = (t.big ? 1.25 : 1) * (0.7 + 0.3 * (1 - Math.pow(1 - appear, 3)));
        const alpha = p < 0.75 ? 1 : 1 - (p - 0.75) / 0.25;
        const y = h * 0.38 - t.offset * cell * 1.6 - p * cell * 1.2;
        ctx.save();
        ctx.globalAlpha = Math.max(0, alpha);
        ctx.translate(w / 2, y);
        ctx.scale(scale, scale);
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const size = Math.max(14, cell * 0.95);
        ctx.font = `900 ${size}px ${font}`;
        ctx.lineWidth = Math.max(3, cell * 0.16);
        ctx.strokeStyle = 'rgba(10,10,30,.85)';
        ctx.strokeText(t.main, 0, 0);
        ctx.fillStyle = t.color || '#fff';
        ctx.fillText(t.main, 0, 0);
        if (t.sub) {
          ctx.font = `800 ${size * 0.55}px ${font}`;
          ctx.lineWidth = Math.max(2, cell * 0.1);
          ctx.strokeText(t.sub, 0, size * 0.85);
          ctx.fillStyle = '#fff';
          ctx.fillText(t.sub, 0, size * 0.85);
        }
        ctx.restore();
      }
    }
  }

  IT.Effects = Effects;
})();
