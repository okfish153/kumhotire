/* IMAGE TETRIS – 샘플 일러스트용 SVG 도우미 (모든 샘플은 코드로 직접 그린 오리지널 일러스트) */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});

  const K = {
    W: 600,
    H: 800,
    svg(defs, body) {
      return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 800" width="600" height="800"><defs>${defs}</defs>${body}</svg>`;
    },
    stops(stops) {
      return stops.map(([o, c, a]) => `<stop offset="${o}" stop-color="${c}"${a != null ? ` stop-opacity="${a}"` : ''}/>`).join('');
    },
    lin(id, stops, x1 = 0, y1 = 0, x2 = 0, y2 = 1) {
      return `<linearGradient id="${id}" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}">${K.stops(stops)}</linearGradient>`;
    },
    rad(id, stops, cx = 0.5, cy = 0.5, r = 0.5, fx, fy) {
      return `<radialGradient id="${id}" cx="${cx}" cy="${cy}" r="${r}"${fx != null ? ` fx="${fx}" fy="${fy}"` : ''}>${K.stops(stops)}</radialGradient>`;
    },
    blur(id, sd) {
      return `<filter id="${id}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="${sd}"/></filter>`;
    },
    shadow(id, dy = 8, sd = 7, op = 0.25, color = '#000') {
      return `<filter id="${id}" x="-30%" y="-30%" width="160%" height="170%"><feDropShadow dx="0" dy="${dy}" stdDeviation="${sd}" flood-color="${color}" flood-opacity="${op}"/></filter>`;
    },
    /** 점토 질감용 노이즈 */
    grain(id, freq = 0.85) {
      return `<filter id="${id}" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="${freq}" numOctaves="2" seed="5" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter>`;
    },
    grainRect(id, op = 0.1) {
      return `<rect width="600" height="800" filter="url(#${id})" opacity="${op}" style="mix-blend-mode:multiply"/>`;
    },
    rng(seed) { return IT.util.seededRandom(seed); },
    stars(n, seed, x = 0, y = 0, w = 600, h = 800, color = '#fff', rMax = 2.2) {
      const r = K.rng(seed);
      let s = '';
      for (let i = 0; i < n; i++) {
        const rr = (0.4 + r() * r() * rMax).toFixed(2);
        s += `<circle cx="${(x + r() * w).toFixed(1)}" cy="${(y + r() * h).toFixed(1)}" r="${rr}" fill="${color}" opacity="${(0.4 + r() * 0.6).toFixed(2)}"/>`;
      }
      return s;
    },
    sparkle(x, y, s, color = '#fff', op = 1) {
      return `<path d="M${x} ${y - s} Q${x + s * 0.15} ${y - s * 0.15} ${x + s} ${y} Q${x + s * 0.15} ${y + s * 0.15} ${x} ${y + s} Q${x - s * 0.15} ${y + s * 0.15} ${x - s} ${y} Q${x - s * 0.15} ${y - s * 0.15} ${x} ${y - s}Z" fill="${color}" opacity="${op}"/>`;
    },
    cloud(x, y, s, fill = '#fff', op = 1) {
      return `<g transform="translate(${x} ${y}) scale(${s})" fill="${fill}" opacity="${op}"><ellipse cx="0" cy="10" rx="70" ry="24"/><circle cx="-30" cy="0" r="26"/><circle cx="8" cy="-12" r="34"/><circle cx="42" cy="4" r="22"/></g>`;
    },
    /** 둥근 나무 (잎 원 3개 + 줄기) */
    roundTree(x, y, s, leaf, leafDark, trunk = '#7a4b2a') {
      return `<g transform="translate(${x} ${y}) scale(${s})"><rect x="-7" y="-10" width="14" height="60" rx="5" fill="${trunk}"/><circle cx="0" cy="-40" r="42" fill="${leafDark}"/><circle cx="-24" cy="-28" r="30" fill="${leaf}"/><circle cx="18" cy="-52" r="30" fill="${leaf}"/><circle cx="-6" cy="-58" r="14" fill="#fff" opacity=".18"/></g>`;
    },
    pine(x, y, s, fill, fill2) {
      return `<g transform="translate(${x} ${y}) scale(${s})"><rect x="-5" y="-6" width="10" height="26" fill="#4a3224"/><path d="M0 -120 L34 -50 L18 -50 L44 0 L-44 0 L-18 -50 L-34 -50 Z" fill="${fill}"/><path d="M0 -120 L34 -50 L18 -50 L44 0 L0 0 Z" fill="${fill2}" opacity=".6"/></g>`;
    },
    wheel(x, y, r, tire = '#22252b', rim = '#cfd5de', hub = '#8d96a3') {
      return `<g><circle cx="${x}" cy="${y}" r="${r}" fill="${tire}"/><circle cx="${x}" cy="${y}" r="${r * 0.62}" fill="${rim}"/><circle cx="${x}" cy="${y}" r="${r * 0.5}" fill="none" stroke="${hub}" stroke-width="${r * 0.08}"/><circle cx="${x}" cy="${y}" r="${r * 0.18}" fill="${hub}"/>${[0, 72, 144, 216, 288].map((a) => `<line x1="${x}" y1="${y}" x2="${(x + Math.cos((a * Math.PI) / 180) * r * 0.48).toFixed(1)}" y2="${(y + Math.sin((a * Math.PI) / 180) * r * 0.48).toFixed(1)}" stroke="${hub}" stroke-width="${r * 0.07}" stroke-linecap="round"/>`).join('')}</g>`;
    },
    /** 귀여운 눈 (하이라이트 포함) */
    eye(x, y, rx, ry, color = '#2b2233') {
      return `<g><ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="${color}"/><circle cx="${x - rx * 0.3}" cy="${y - ry * 0.35}" r="${rx * 0.36}" fill="#fff"/><circle cx="${x + rx * 0.3}" cy="${y + ry * 0.3}" r="${rx * 0.16}" fill="#fff" opacity=".85"/></g>`;
    },
    paw(x, y, s, fill, op = 1) {
      return `<g transform="translate(${x} ${y}) scale(${s})" fill="${fill}" opacity="${op}"><ellipse cx="0" cy="8" rx="14" ry="11"/><circle cx="-14" cy="-8" r="6"/><circle cx="-5" cy="-15" r="6"/><circle cx="6" cy="-15" r="6"/><circle cx="15" cy="-8" r="6"/></g>`;
    },
    heart(x, y, s, fill, op = 1) {
      return `<path transform="translate(${x} ${y}) scale(${s})" d="M0 8 C-4 2 -14 -2 -14 -9 C-14 -15 -9 -18 -5 -18 C-2 -18 0 -16 0 -13 C0 -16 2 -18 5 -18 C9 -18 14 -15 14 -9 C14 -2 4 2 0 8Z" fill="${fill}" opacity="${op}"/>`;
    },
    dots(n, seed, color, rMin, rMax, op = 0.5, x = 0, y = 0, w = 600, h = 800) {
      const r = K.rng(seed);
      let s = '';
      for (let i = 0; i < n; i++) s += `<circle cx="${(x + r() * w).toFixed(1)}" cy="${(y + r() * h).toFixed(1)}" r="${(rMin + r() * (rMax - rMin)).toFixed(1)}" fill="${color}" opacity="${op}"/>`;
      return s;
    },
    gingham(id, c1, c2, size = 40) {
      return `<pattern id="${id}" width="${size}" height="${size}" patternUnits="userSpaceOnUse"><rect width="${size}" height="${size}" fill="${c1}"/><rect width="${size / 2}" height="${size}" fill="${c2}" opacity=".45"/><rect width="${size}" height="${size / 2}" fill="${c2}" opacity=".45"/></pattern>`;
    },
  };

  IT.SvgKit = K;
})();
