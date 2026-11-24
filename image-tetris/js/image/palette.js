/* IMAGE TETRIS – 이미지 대표 색상 추출 + 게임 테마 생성
 *
 * 1) k-means 로 대표 색 5~7개 추출
 * 2) 블록 7종 색상 생성: 비슷한 색이 많으면 색상(Hue)과 명도를 자동 보정해 구별되도록 함
 * 3) UI 색상(배경, 패널, 강조, 테두리) 구성
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const U = IT.util;
  const TYPES = IT.Pieces.TYPES;

  /** pixels: RGBA Uint8 배열 → [{r,g,b,share}] (점유율 순) */
  function kmeansPalette(pixels, k, rng) {
    rng = rng || U.seededRandom(7);
    const pts = [];
    for (let i = 0; i < pixels.length; i += 4) {
      if (pixels[i + 3] < 128) continue;
      pts.push([pixels[i], pixels[i + 1], pixels[i + 2]]);
    }
    if (!pts.length) return [{ r: 128, g: 128, b: 128, share: 1 }];
    k = Math.min(k, pts.length);
    const d2 = (a, b) => (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2;
    // k-means++ 초기화
    const cents = [pts[Math.floor(rng() * pts.length)].slice()];
    while (cents.length < k) {
      const dist = pts.map((p) => Math.min(...cents.map((c) => d2(p, c))));
      const sum = dist.reduce((a, b) => a + b, 0);
      if (sum === 0) break;
      let r = rng() * sum, idx = 0;
      for (; idx < dist.length - 1; idx++) { r -= dist[idx]; if (r <= 0) break; }
      cents.push(pts[idx].slice());
    }
    const assign = new Int32Array(pts.length);
    for (let iter = 0; iter < 10; iter++) {
      const sums = cents.map(() => [0, 0, 0, 0]);
      for (let i = 0; i < pts.length; i++) {
        let best = 0, bd = Infinity;
        for (let c = 0; c < cents.length; c++) { const d = d2(pts[i], cents[c]); if (d < bd) { bd = d; best = c; } }
        assign[i] = best;
        const s = sums[best]; s[0] += pts[i][0]; s[1] += pts[i][1]; s[2] += pts[i][2]; s[3]++;
      }
      for (let c = 0; c < cents.length; c++) if (sums[c][3]) cents[c] = [sums[c][0] / sums[c][3], sums[c][1] / sums[c][3], sums[c][2] / sums[c][3]];
    }
    const counts = cents.map(() => 0);
    for (let i = 0; i < pts.length; i++) counts[assign[i]]++;
    return cents
      .map((c, i) => ({ r: Math.round(c[0]), g: Math.round(c[1]), b: Math.round(c[2]), share: counts[i] / pts.length }))
      .filter((c) => c.share > 0)
      .sort((a, b) => b.share - a.share);
  }

  /** 캔버스/이미지 → 대표 색 hex 배열 */
  function extractPalette(source, count = 6) {
    const S = 64;
    const c = U.createCanvas(S, S);
    const ctx = c.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(source, 0, 0, S, S);
    const data = ctx.getImageData(0, 0, S, S).data;
    return kmeansPalette(data, count).map((p) => ({ hex: U.rgbToHex(p.r, p.g, p.b), share: p.share }));
  }

  const hueDist = (a, b) => { const d = Math.abs(a - b) % 360; return d > 180 ? 360 - d : d; };

  /** 대표 색 목록 → 블록 7색 (서로 구별 가능하도록 보정) */
  function buildPieceColors(paletteHex) {
    const hsl = paletteHex.map((h) => Object.assign({ hex: h }, U.hexToHsl(h)));
    const colorful = hsl.filter((c) => c.s > 0.18 && c.l > 0.12 && c.l < 0.92);
    // 기본 Hue 후보: 채도가 높은 순, 서로 22° 이상 떨어진 것만
    const hues = [];
    colorful.sort((a, b) => b.s * (1 - Math.abs(b.l - 0.5)) - a.s * (1 - Math.abs(a.l - 0.5)));
    for (const c of colorful) if (hues.every((h) => hueDist(h, c.h) >= 22)) hues.push(c.h);
    if (!hues.length) {
      // 흑백/무채색 이미지: 가장 진한 색의 Hue 를 기준으로 분산
      const base = hsl.length ? hsl.reduce((a, b) => (b.s > a.s ? b : a)).h : 210;
      hues.push(base || 210);
    }
    // 부족한 색은 Hue 원에서 가장 넓은 빈틈의 중앙에 추가
    while (hues.length < 7) {
      const sorted = hues.slice().sort((a, b) => a - b);
      let bestGap = -1, bestMid = 0;
      for (let i = 0; i < sorted.length; i++) {
        const a = sorted[i], b = i + 1 < sorted.length ? sorted[i + 1] : sorted[0] + 360;
        const gap = b - a;
        if (gap > bestGap) { bestGap = gap; bestMid = (a + gap / 2) % 360; }
      }
      hues.push(bestMid);
    }
    const picked = hues.slice(0, 7);
    const L = [0.6, 0.5, 0.68, 0.55, 0.63, 0.47, 0.72];
    const S = [0.78, 0.72, 0.82, 0.7, 0.76, 0.74, 0.8];
    let colors = picked.map((h, i) => U.hslToHex(h, S[i], L[i]));
    colors = ensureDistinct(colors);
    const out = {};
    TYPES.forEach((t, i) => { out[t] = colors[i]; });
    return out;
  }

  /** 서로 너무 비슷한 색(ΔE < 기준)은 명도/색상을 조금씩 이동 */
  function ensureDistinct(colors, minDE = 18) {
    const res = colors.slice();
    for (let pass = 0; pass < 24; pass++) {
      let changed = false;
      for (let i = 0; i < res.length; i++) {
        for (let j = 0; j < i; j++) {
          if (U.deltaE(res[i], res[j]) < minDE) {
            const c = U.hexToHsl(res[i]);
            const dir = (i + pass) % 2 ? 1 : -1;
            const l = U.clamp(c.l + dir * 0.07, 0.38, 0.8);
            res[i] = U.hslToHex(c.h + 17 * (pass % 3 === 2 ? -1 : 1), U.clamp(c.s + 0.05, 0.5, 0.95), l);
            changed = true;
          }
        }
      }
      if (!changed) break;
    }
    return res;
  }

  /** 대표 색 → UI 테마 전체 */
  function buildTheme(paletteHex) {
    const hsl = paletteHex.map((h) => Object.assign({ hex: h }, U.hexToHsl(h)));
    const byLight = hsl.slice().sort((a, b) => a.l - b.l);
    const dark = byLight[0] || { h: 230, s: 0.3, l: 0.1 };
    const accentSrc = hsl.slice().sort((a, b) => b.s * (1 - Math.abs(b.l - 0.55)) - a.s * (1 - Math.abs(a.l - 0.55)))[0] || { h: 260, s: 0.7 };
    const second = hsl.find((c) => hueDist(c.h, accentSrc.h) > 40 && c.s > 0.2) || { h: accentSrc.h + 40, s: accentSrc.s };
    const bgS = U.clamp(dark.s, 0.15, 0.45);
    return {
      bg: U.hslToHex(dark.h, bgS, 0.09),
      bg2: U.hslToHex(dark.h, bgS, 0.15),
      panel: U.hslToHex(dark.h, U.clamp(bgS, 0.12, 0.35), 0.17),
      board: U.hslToHex(dark.h, U.clamp(bgS, 0.1, 0.4), 0.07),
      accent: U.hslToHex(accentSrc.h, U.clamp(accentSrc.s, 0.55, 0.9), 0.6),
      accent2: U.hslToHex(second.h, U.clamp(second.s, 0.5, 0.9), 0.62),
      border: U.hslToHex(accentSrc.h, 0.35, 0.36),
      text: '#f4f6ff',
      pieces: buildPieceColors(paletteHex),
      palette: paletteHex.slice(),
    };
  }

  const DEFAULT_THEME = {
    bg: '#0f1024', bg2: '#1b1c3a', panel: '#1d1f40', board: '#0b0c1c',
    accent: '#8b7bff', accent2: '#ff7eb6', border: '#3b3d72', text: '#f4f6ff',
    pieces: Object.assign({}, IT.Pieces.CLASSIC_COLORS),
    palette: ['#8b7bff', '#ff7eb6', '#35c9f0', '#f7d31e', '#4cc463', '#f0444f'],
  };

  IT.Palette = { kmeansPalette, extractPalette, buildPieceColors, ensureDistinct, buildTheme, DEFAULT_THEME };
})();
