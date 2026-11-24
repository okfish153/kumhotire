/* 샘플 테마 5. 우주 및 미래도시 (오리지널 SVG 일러스트) */
(function () {
  'use strict';
  const IT = globalThis.IT;
  const K = IT.SvgKit;

  /* 지구와 달 */
  const earthMoon = K.svg(
    K.lin('sky', [[0, '#02030f'], [1, '#0b1238']]) + K.rad('ocean', [[0, '#5fc2ff'], [0.7, '#1c6fd1'], [1, '#0d3f8a']], 0.38, 0.35, 0.7) +
      K.rad('atmo', [[0.78, '#7fd3ff', 0], [0.9, '#7fd3ff', 0.55], [1, '#7fd3ff', 0]]) + K.rad('moon', [[0, '#f3f1ea'], [1, '#a9a69c']], 0.35, 0.35, 0.75) +
      K.rad('shade', [[0.45, '#000', 0], [1, '#000', 0.65]], 0.3, 0.3, 0.85) + K.blur('b6', 6) +
      '<clipPath id="ec"><circle cx="300" cy="470" r="210"/></clipPath>',
    `<rect width="600" height="800" fill="url(#sky)"/>
     ${K.stars(200, 101, 0, 0, 600, 800, '#fff', 2)}
     <circle cx="300" cy="470" r="250" fill="url(#atmo)"/>
     <circle cx="300" cy="470" r="210" fill="url(#ocean)"/>
     <g clip-path="url(#ec)" fill="#4cbf6b">
       <path d="M160 330 Q200 290 260 310 Q300 330 280 380 Q250 420 270 470 Q250 520 200 500 Q170 460 180 420 Q140 380 160 330Z"/>
       <path d="M330 400 Q380 380 430 410 Q470 450 450 520 Q420 580 370 590 Q340 560 350 510 Q320 470 330 400Z"/>
       <path d="M220 590 Q260 570 300 600 Q290 640 240 650 Q210 630 220 590Z" fill="#e8d28a"/>
       <path d="M400 300 Q440 290 460 320 Q440 340 410 330Z"/>
       <g fill="#fff" opacity=".75" filter="url(#b6)"><ellipse cx="240" cy="380" rx="90" ry="14" transform="rotate(-15 240 380)"/><ellipse cx="380" cy="520" rx="110" ry="12" transform="rotate(10 380 520)"/><ellipse cx="300" cy="300" rx="70" ry="10"/></g>
     </g>
     <circle cx="300" cy="470" r="210" fill="url(#shade)"/>
     <circle cx="470" cy="170" r="62" fill="url(#moon)"/>
     ${[[450, 150, 12], [490, 190, 9], [470, 200, 6], [500, 150, 7]].map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="#8f8c83" opacity=".55"/>`).join('')}
     <circle cx="470" cy="170" r="62" fill="url(#shade)"/>
     ${K.sparkle(90, 150, 14, '#fff')}${K.sparkle(100, 720, 10, '#cfe8ff')}`
  );

  /* 우주 행성 */
  const planets = K.svg(
    K.lin('sky', [[0, '#120a2e'], [1, '#2a0f4a']]) + K.rad('neb1', [[0, '#ff5fa2', 0.6], [1, '#ff5fa2', 0]]) + K.rad('neb2', [[0, '#4fd1ff', 0.5], [1, '#4fd1ff', 0]]) +
      K.lin('ring', [[0, '#ffe3a3'], [0.5, '#f7b267'], [1, '#ffe3a3']], 0, 0, 1, 0) + K.rad('pl1', [[0, '#ffd59e'], [1, '#e0823a']], 0.35, 0.3, 0.75) +
      K.rad('pl2', [[0, '#a6f0d0'], [1, '#2a9d8f']], 0.35, 0.3, 0.75) + K.rad('pl3', [[0, '#d0b8ff'], [1, '#6c4ab6']], 0.35, 0.3, 0.75) +
      '<clipPath id="front"><rect x="0" y="420" width="600" height="400"/></clipPath>',
    `<rect width="600" height="800" fill="url(#sky)"/>
     <ellipse cx="160" cy="250" rx="260" ry="200" fill="url(#neb1)"/><ellipse cx="470" cy="620" rx="260" ry="220" fill="url(#neb2)"/>
     ${K.stars(180, 202, 0, 0, 600, 800, '#fff', 2)}
     <ellipse cx="300" cy="420" rx="230" ry="50" fill="none" stroke="url(#ring)" stroke-width="22" opacity=".9" transform="rotate(-12 300 420)"/>
     <circle cx="300" cy="420" r="140" fill="url(#pl1)"/>
     <path d="M170 380 Q300 360 430 390 M165 440 Q300 420 435 450 M190 490 Q300 476 410 500" stroke="#c96a2a" stroke-width="14" fill="none" opacity=".35" stroke-linecap="round"/>
     <g clip-path="url(#front)"><ellipse cx="300" cy="420" rx="230" ry="50" fill="none" stroke="url(#ring)" stroke-width="22" transform="rotate(-12 300 420)"/></g>
     <circle cx="110" cy="660" r="60" fill="url(#pl2)"/><circle cx="90" cy="645" r="10" fill="#fff" opacity=".2"/>
     <circle cx="500" cy="150" r="44" fill="url(#pl3)"/><circle cx="520" cy="560" r="18" fill="#ffb3c7"/>
     ${K.sparkle(420, 700, 14, '#fff')}${K.sparkle(80, 120, 12, '#fff')}`
  );

  /* 미래 도시 */
  const futureCity = K.svg(
    K.lin('sky', [[0, '#1b0b3a'], [0.5, '#5a1f7a'], [1, '#ff7aa8']]) + K.rad('sun', [[0, '#ffe6a8'], [1, '#ff7aa8', 0]]) + K.blur('b3', 3),
    `<rect width="600" height="800" fill="url(#sky)"/>
     ${K.stars(70, 303, 0, 0, 600, 320, '#fff', 1.6)}
     <circle cx="300" cy="420" r="200" fill="url(#sun)" opacity=".8"/>
     ${[[10, 380, 60], [80, 300, 70], [160, 220, 55], [225, 330, 60], [295, 160, 70], [375, 280, 60], [445, 210, 65], [520, 340, 70]].map(([x, y, w], i) => `<rect x="${x}" y="${y}" width="${w}" height="${800 - y}" fill="${i % 2 ? '#2a1450' : '#351a62'}"/><rect x="${x}" y="${y}" width="${w}" height="6" fill="#4fe3ff" opacity=".8"/>${Array.from({ length: Math.floor((800 - y) / 26) }, (_, r) => Array.from({ length: Math.floor(w / 18) }, (_, q) => ((r * 7 + q * 3 + i) % 5 === 0 ? '' : `<rect x="${x + 6 + q * 18}" y="${y + 18 + r * 26}" width="9" height="12" fill="${(r + q + i) % 4 === 0 ? '#ff7ad9' : '#ffe08a'}" opacity="${(r + q) % 3 === 0 ? 0.9 : 0.45}"/>`)).join('')).join('')}`).join('')}
     <path d="M330 160 L330 90" stroke="#4fe3ff" stroke-width="4"/><circle cx="330" cy="86" r="6" fill="#ff7ad9"/>
     <ellipse cx="300" cy="600" rx="320" ry="40" fill="none" stroke="#4fe3ff" stroke-width="6" opacity=".7"/>
     <ellipse cx="300" cy="600" rx="320" ry="40" fill="none" stroke="#4fe3ff" stroke-width="14" opacity=".25" filter="url(#b3)"/>
     ${[[120, 140, 1], [430, 110, -1], [250, 260, 1]].map(([x, y, d]) => `<g transform="translate(${x} ${y}) scale(${d} 1)"><path d="M-30 0 Q-20 -16 10 -16 Q30 -14 36 0 Q30 8 -30 8Z" fill="#e6ecff"/><path d="M-6 -14 Q10 -24 24 -12Z" fill="#4fe3ff"/><rect x="-60" y="1" width="28" height="3" rx="1.5" fill="#ff7ad9" opacity=".8"/></g>`).join('')}`
  );

  /* 우주 탐사선 */
  const probe = K.svg(
    K.lin('sky', [[0, '#04061a'], [1, '#101a44']]) + K.rad('pl', [[0, '#ffb38a'], [0.7, '#d9583b'], [1, '#7a2416']], 0.4, 0.2, 0.8) +
      K.lin('panel', [[0, '#2f6be0'], [1, '#1b3f9a']], 0, 0, 1, 1) + K.lin('gold', [[0, '#ffe08a'], [1, '#c9922b']], 0, 0, 1, 1) + K.blur('b4', 4),
    `<rect width="600" height="800" fill="url(#sky)"/>
     ${K.stars(190, 404, 0, 0, 600, 800, '#fff', 2)}
     <circle cx="300" cy="1060" r="460" fill="url(#pl)"/>
     <path d="M-100 700 Q300 640 700 700" stroke="#ffd2b8" stroke-width="10" fill="none" opacity=".25"/>
     <g transform="translate(300 330) rotate(-14)">
       <rect x="-250" y="-40" width="160" height="80" rx="6" fill="url(#panel)" stroke="#9fc2ff" stroke-width="3"/>
       <rect x="90" y="-40" width="160" height="80" rx="6" fill="url(#panel)" stroke="#9fc2ff" stroke-width="3"/>
       ${[-210, -170, -130, 130, 170, 210].map((x) => `<line x1="${x}" y1="-40" x2="${x}" y2="40" stroke="#9fc2ff" stroke-width="2" opacity=".7"/>`).join('')}
       <line x1="-250" y1="0" x2="-90" y2="0" stroke="#9fc2ff" stroke-width="2" opacity=".7"/><line x1="90" y1="0" x2="250" y2="0" stroke="#9fc2ff" stroke-width="2" opacity=".7"/>
       <rect x="-90" y="-6" width="180" height="12" fill="#b8c0cc"/>
       <rect x="-55" y="-60" width="110" height="120" rx="10" fill="url(#gold)"/>
       <path d="M-55 -20 H55 M-55 20 H55" stroke="#b07a1e" stroke-width="3"/>
       <path d="M-70 -70 Q0 -170 70 -70Z" fill="#e8ecf4" stroke="#b8c0cc" stroke-width="3"/>
       <line x1="0" y1="-90" x2="0" y2="-150" stroke="#b8c0cc" stroke-width="4"/><circle cx="0" cy="-152" r="7" fill="#ff6b6b"/>
       <rect x="-20" y="60" width="40" height="30" fill="#8d96a3"/><path d="M-26 90 L26 90 L18 112 L-18 112Z" fill="#5a6270"/>
       <ellipse cx="0" cy="130" rx="16" ry="26" fill="#7fd3ff" opacity=".8" filter="url(#b4)"/>
     </g>
     ${K.sparkle(90, 120, 16, '#fff')}${K.sparkle(510, 520, 12, '#fff')}<circle cx="520" cy="110" r="18" fill="#cfd8ff" opacity=".85"/>`
  );

  IT.Samples.register({ key: 'space', name: '우주 및 미래도시', icon: '🚀' }, [
    { key: 'earth-moon', name: '지구와 달', svg: earthMoon },
    { key: 'planets', name: '우주 행성', svg: planets },
    { key: 'future-city', name: '미래 도시', svg: futureCity },
    { key: 'space-probe', name: '우주 탐사선', svg: probe },
  ]);
})();
