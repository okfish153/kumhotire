/* IMAGE TETRIS – 공통 유틸리티
 * 모든 스크립트는 전역 네임스페이스 IT 아래에 기능을 등록합니다.
 * (ES 모듈을 쓰지 않으므로 file:// 로 index.html 을 직접 열어도 동작합니다.)
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});

  class Emitter {
    constructor() { this._l = Object.create(null); }
    on(ev, fn) { (this._l[ev] = this._l[ev] || []).push(fn); return () => this.off(ev, fn); }
    off(ev, fn) { const a = this._l[ev]; if (a) { const i = a.indexOf(fn); if (i >= 0) a.splice(i, 1); } }
    emit(ev, data) { const a = this._l[ev]; if (a) for (const fn of a.slice()) fn(data); }
  }

  const util = {
    clamp(v, a, b) { return v < a ? a : v > b ? b : v; },
    lerp(a, b, t) { return a + (b - a) * t; },
    uid(prefix) { return (prefix || '') + Date.now().toString(36) + Math.random().toString(36).slice(2, 8); },
    range(n) { return Array.from({ length: n }, (_, i) => i); },
    shuffle(arr, rng) {
      rng = rng || Math.random;
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(rng() * (i + 1));
        const t = arr[i]; arr[i] = arr[j]; arr[j] = t;
      }
      return arr;
    },
    /** 재현 가능한 난수 (테스트용) */
    seededRandom(seed) {
      let s = seed >>> 0 || 1;
      return function () {
        s = (s + 0x6d2b79f5) >>> 0;
        let t = s;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
      };
    },
    formatTime(ms) {
      const total = Math.max(0, Math.floor(ms / 1000));
      const h = Math.floor(total / 3600), m = Math.floor((total % 3600) / 60), s = total % 60;
      const mm = String(m).padStart(2, '0'), ss = String(s).padStart(2, '0');
      return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
    },
    formatDuration(ms) {
      const total = Math.floor(ms / 1000);
      const h = Math.floor(total / 3600), m = Math.floor((total % 3600) / 60), s = total % 60;
      if (h) return `${h}시간 ${m}분`;
      if (m) return `${m}분 ${s}초`;
      return `${s}초`;
    },
    formatNum(n) { return Math.round(n).toLocaleString('ko-KR'); },
    formatDate(ts) {
      const d = new Date(ts);
      const p = (x) => String(x).padStart(2, '0');
      return `${d.getFullYear()}.${p(d.getMonth() + 1)}.${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
    },
    debounce(fn, ms) {
      let t = null;
      return function (...args) { clearTimeout(t); t = setTimeout(() => fn.apply(this, args), ms); };
    },
    escapeHtml(s) {
      return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    },

    /* ---------- 색상 ---------- */
    hexToRgb(hex) {
      let h = String(hex).replace('#', '').trim();
      if (h.length === 3) h = h.split('').map((c) => c + c).join('');
      const n = parseInt(h, 16);
      return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
    },
    rgbToHex(r, g, b) {
      if (typeof r === 'object') { g = r.g; b = r.b; r = r.r; }
      const c = (v) => util.clamp(Math.round(v), 0, 255).toString(16).padStart(2, '0');
      return '#' + c(r) + c(g) + c(b);
    },
    rgbToHsl(r, g, b) {
      r /= 255; g /= 255; b /= 255;
      const max = Math.max(r, g, b), min = Math.min(r, g, b);
      let h = 0, s = 0;
      const l = (max + min) / 2;
      if (max !== min) {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        if (max === r) h = (g - b) / d + (g < b ? 6 : 0);
        else if (max === g) h = (b - r) / d + 2;
        else h = (r - g) / d + 4;
        h *= 60;
      }
      return { h, s, l };
    },
    hslToRgb(h, s, l) {
      h = ((h % 360) + 360) % 360;
      const c = (1 - Math.abs(2 * l - 1)) * s;
      const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
      const m = l - c / 2;
      let r = 0, g = 0, b = 0;
      if (h < 60) { r = c; g = x; } else if (h < 120) { r = x; g = c; } else if (h < 180) { g = c; b = x; }
      else if (h < 240) { g = x; b = c; } else if (h < 300) { r = x; b = c; } else { r = c; b = x; }
      return { r: (r + m) * 255, g: (g + m) * 255, b: (b + m) * 255 };
    },
    hslToHex(h, s, l) { return util.rgbToHex(util.hslToRgb(h, s, l)); },
    hexToHsl(hex) { const c = util.hexToRgb(hex); return util.rgbToHsl(c.r, c.g, c.b); },
    /** 밝기 조절: amt -1(검정) ~ +1(흰색) */
    shade(hex, amt) {
      const c = util.hexToRgb(hex);
      const t = amt < 0 ? 0 : 255, p = Math.abs(amt);
      return util.rgbToHex(c.r + (t - c.r) * p, c.g + (t - c.g) * p, c.b + (t - c.b) * p);
    },
    rgba(hex, a) { const c = util.hexToRgb(hex); return `rgba(${c.r},${c.g},${c.b},${a})`; },
    /** CIE Lab (D65) – 색 차이 계산용 */
    rgbToLab(r, g, b) {
      const f = (v) => { v /= 255; return v > 0.04045 ? Math.pow((v + 0.055) / 1.055, 2.4) : v / 12.92; };
      const R = f(r), G = f(g), B = f(b);
      let x = (R * 0.4124 + G * 0.3576 + B * 0.1805) / 0.95047;
      let y = (R * 0.2126 + G * 0.7152 + B * 0.0722) / 1.0;
      let z = (R * 0.0193 + G * 0.1192 + B * 0.9505) / 1.08883;
      const g3 = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
      x = g3(x); y = g3(y); z = g3(z);
      return { L: 116 * y - 16, a: 500 * (x - y), b: 200 * (y - z) };
    },
    deltaE(hexA, hexB) {
      const a = util.hexToRgb(hexA), b = util.hexToRgb(hexB);
      const la = util.rgbToLab(a.r, a.g, a.b), lb = util.rgbToLab(b.r, b.g, b.b);
      return Math.hypot(la.L - lb.L, la.a - lb.a, la.b - lb.b);
    },
    luminance(hex) {
      const c = util.hexToRgb(hex);
      const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
      return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b);
    },

    /* ---------- DOM / Canvas (브라우저 전용) ---------- */
    createCanvas(w, h) {
      const c = document.createElement('canvas');
      c.width = Math.max(1, Math.round(w)); c.height = Math.max(1, Math.round(h));
      return c;
    },
    /** 비율을 유지하며 대상 영역을 가득 채우는 소스 영역 (cover) */
    coverRect(sw, sh, dw, dh) {
      const s = Math.max(dw / sw, dh / sh);
      const w = dw / s, h = dh / s;
      return { sx: (sw - w) / 2, sy: (sh - h) / 2, sw: w, sh: h };
    },
    /** 비율을 유지하며 대상 영역 안에 맞추는 배치 (contain) */
    containRect(sw, sh, dw, dh) {
      const s = Math.min(dw / sw, dh / sh);
      const w = sw * s, h = sh * s;
      return { x: (dw - w) / 2, y: (dh - h) / 2, w, h, scale: s };
    },
    roundRect(ctx, x, y, w, h, r) {
      r = Math.min(r, w / 2, h / 2);
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    },
  };

  IT.Emitter = Emitter;
  IT.util = util;
  if (typeof module !== 'undefined' && module.exports) module.exports = IT;
})();
