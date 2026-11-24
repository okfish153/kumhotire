/* 샘플 테마 6. 과일 및 음식 (오리지널 SVG 일러스트) */
(function () {
  'use strict';
  const IT = globalThis.IT;
  const K = IT.SvgKit;
  const shine = (x, y, rx, ry, rot = -30, op = 0.55) => `<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" transform="rotate(${rot} ${x} ${y})" fill="#fff" opacity="${op}"/>`;
  const face = (x, y, s = 1) => `<g transform="translate(${x} ${y}) scale(${s})">${K.eye(-34, 0, 11, 14)}${K.eye(34, 0, 11, 14)}<ellipse cx="-58" cy="26" rx="16" ry="9" fill="#ff8fa3" opacity=".55"/><ellipse cx="58" cy="26" rx="16" ry="9" fill="#ff8fa3" opacity=".55"/><path d="M-12 18 Q0 32 12 18" stroke="#3a2226" stroke-width="5" fill="none" stroke-linecap="round"/></g>`;

  /* 사과 */
  const apple = K.svg(
    K.gingham('g', '#fff7f2', '#ffb3b3', 50) + K.rad('ap', [[0, '#ff7a7a'], [0.7, '#e3262f'], [1, '#a8141c']], 0.35, 0.3, 0.75) + K.shadow('sh', 14, 12, 0.25),
    `<rect width="600" height="800" fill="url(#g)"/>
     <ellipse cx="300" cy="640" rx="200" ry="30" fill="#000" opacity=".12"/>
     <g filter="url(#sh)">
       <path d="M300 250 C380 190 520 220 520 400 C520 560 420 650 360 640 C330 636 320 625 300 625 C280 625 270 636 240 640 C180 650 80 560 80 400 C80 220 220 190 300 250Z" fill="url(#ap)"/>
     </g>
     <path d="M300 255 Q296 200 318 160" stroke="#6b3a1f" stroke-width="14" fill="none" stroke-linecap="round"/>
     <path d="M318 190 Q380 130 450 160 Q400 220 318 190Z" fill="#59b84a"/><path d="M322 188 Q380 165 440 162" stroke="#3f8f33" stroke-width="3" fill="none"/>
     ${shine(190, 340, 40, 70)}${shine(215, 470, 12, 22, -20, 0.4)}
     ${face(300, 450, 1.2)}`
  );

  /* 배 */
  const pear = K.svg(
    K.lin('bg', [[0, '#eaf7d6'], [1, '#d3efb0']]) + K.rad('pr', [[0, '#f8f5a0'], [0.7, '#cfe06a'], [1, '#9cbc3a']], 0.35, 0.35, 0.75) + K.shadow('sh', 14, 12, 0.22),
    `<rect width="600" height="800" fill="url(#bg)"/>
     ${K.dots(26, 505, '#fff', 8, 22, 0.55)}
     <ellipse cx="300" cy="680" rx="190" ry="28" fill="#000" opacity=".1"/>
     <g filter="url(#sh)">
       <path d="M300 200 C360 200 380 270 390 330 C400 390 500 420 500 540 C500 640 410 680 300 680 C190 680 100 640 100 540 C100 420 200 390 210 330 C220 270 240 200 300 200Z" fill="url(#pr)"/>
     </g>
     ${K.dots(30, 506, '#b5a23a', 2, 4, 0.45, 150, 260, 300, 380)}
     <path d="M300 205 Q296 160 314 125" stroke="#6b3a1f" stroke-width="12" fill="none" stroke-linecap="round"/>
     <path d="M310 150 Q370 100 430 130 Q380 180 310 150Z" fill="#59b84a"/>
     ${shine(230, 320, 22, 60, -15)}${shine(170, 500, 22, 50, -20, 0.45)}
     ${face(300, 520, 1.15)}`
  );

  /* 딸기 */
  const strawberry = K.svg(
    K.lin('bg', [[0, '#ffe5ec'], [1, '#ffc2d4']]) + K.rad('sb', [[0, '#ff6b81'], [0.7, '#e8253f'], [1, '#b0162c']], 0.35, 0.3, 0.8) + K.shadow('sh', 12, 10, 0.25),
    `<rect width="600" height="800" fill="url(#bg)"/>
     ${[[90, 120], [500, 90], [520, 700], [70, 690], [140, 400], [480, 420]].map(([x, y], i) => K.heart(x, y, 1.6 + (i % 3) * 0.5, '#fff', 0.6)).join('')}
     <g filter="url(#sh)">
       <path d="M300 690 C200 650 110 520 120 400 C130 300 220 270 300 280 C380 270 470 300 480 400 C490 520 400 650 300 690Z" fill="url(#sb)"/>
     </g>
     ${Array.from({ length: 34 }, (_, i) => { const r = K.rng(600 + i); const x = 160 + r() * 280, y = 330 + r() * 300; const inside = Math.abs(x - 300) < 170 - (y - 330) * 0.35; return inside ? `<ellipse cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" rx="5" ry="8" fill="#ffe08a"/>` : ''; }).join('')}
     <g fill="#3fae49">
       <path d="M300 300 Q240 240 170 270 Q230 300 300 310Z"/><path d="M300 300 Q360 240 430 270 Q370 300 300 310Z"/>
       <path d="M300 300 Q260 230 220 220 Q250 270 296 312Z"/><path d="M300 300 Q340 230 380 220 Q350 270 304 312Z"/><path d="M300 300 Q300 240 300 220 Q290 270 300 312Z"/>
     </g>
     <path d="M300 230 Q306 190 330 170" stroke="#3a8a3f" stroke-width="10" fill="none" stroke-linecap="round"/>
     ${shine(190, 400, 26, 56, -25, 0.5)}
     <g transform="translate(300 470)">${K.eye(-40, 0, 13, 16)}${K.eye(40, 0, 13, 16)}<path d="M-14 22 Q0 38 14 22" stroke="#4a0f1a" stroke-width="5" fill="none" stroke-linecap="round"/></g>`
  );

  /* 수박 */
  const watermelon = K.svg(
    K.lin('bg', [[0, '#d7f5ff'], [1, '#b8ecff']]) + K.lin('flesh', [[0, '#ff6b81'], [1, '#ff3d5a']]) + K.shadow('sh', 12, 10, 0.22),
    `<rect width="600" height="800" fill="url(#bg)"/>
     ${K.dots(20, 707, '#fff', 10, 26, 0.6)}
     <g filter="url(#sh)">
       <path d="M60 300 L540 300 A240 240 0 0 1 60 300Z" fill="#2f9e44"/>
       <path d="M80 300 L520 300 A220 220 0 0 1 80 300Z" fill="#e9fbe5"/>
       <path d="M96 300 L504 300 A204 204 0 0 1 96 300Z" fill="url(#flesh)"/>
       <g transform="translate(0 190)">
         <path d="M120 400 L480 400 A180 180 0 0 1 120 400Z" fill="#2f9e44" transform="rotate(8 300 400)"/>
         <path d="M136 400 L464 400 A164 164 0 0 1 136 400Z" fill="#e9fbe5" transform="rotate(8 300 400)"/>
         <path d="M150 400 L450 400 A150 150 0 0 1 150 400Z" fill="url(#flesh)" transform="rotate(8 300 400)"/>
       </g>
     </g>
     ${[[170, 340], [230, 380], [300, 350], [370, 380], [430, 340], [260, 440], [340, 440], [300, 490]].map(([x, y]) => `<ellipse cx="${x}" cy="${y}" rx="7" ry="12" fill="#2b2233"/>`).join('')}
     ${[[230, 630], [300, 670], [370, 630]].map(([x, y]) => `<ellipse cx="${x}" cy="${y}" rx="6" ry="10" fill="#2b2233" transform="rotate(8 300 590)"/>`).join('')}
     <path d="M70 300 L530 300" stroke="#fff" stroke-width="4" opacity=".5"/>
     <circle cx="480" cy="130" r="60" fill="#ffe066"/>${[0, 45, 90, 135, 180, 225, 270, 315].map((a) => `<line x1="${(480 + Math.cos(a * Math.PI / 180) * 75).toFixed(1)}" y1="${(130 + Math.sin(a * Math.PI / 180) * 75).toFixed(1)}" x2="${(480 + Math.cos(a * Math.PI / 180) * 98).toFixed(1)}" y2="${(130 + Math.sin(a * Math.PI / 180) * 98).toFixed(1)}" stroke="#ffe066" stroke-width="8" stroke-linecap="round"/>`).join('')}
     ${face(300, 400, 0.9)}`
  );

  /* 디저트 (케이크와 마카롱) */
  const dessert = K.svg(
    K.lin('bg', [[0, '#fff0f5'], [1, '#ffe0ec']]) + K.lin('cake', [[0, '#fff3dc'], [1, '#f6d7a7']]) + K.lin('cream', [[0, '#ffffff'], [1, '#ffe4ef']]) +
      K.rad('cherry', [[0, '#ff6b81'], [1, '#c2183a']], 0.35, 0.3, 0.7) + K.shadow('sh', 10, 10, 0.2),
    `<rect width="600" height="800" fill="url(#bg)"/>
     ${K.dots(40, 808, '#ffc2d4', 4, 10, 0.7)}
     <ellipse cx="300" cy="640" rx="250" ry="40" fill="#fff" stroke="#f1c6d6" stroke-width="6"/>
     <g filter="url(#sh)">
       <rect x="130" y="420" width="340" height="210" rx="20" fill="url(#cake)"/>
       <rect x="130" y="500" width="340" height="26" fill="#ff8fab"/><rect x="130" y="570" width="340" height="18" fill="#ffd6e0"/>
       <path d="M120 430 Q120 380 170 380 L430 380 Q480 380 480 430 Q470 470 440 450 Q420 480 390 455 Q360 485 330 455 Q300 485 270 455 Q240 485 210 455 Q180 480 160 452 Q130 470 120 430Z" fill="url(#cream)"/>
       ${[180, 300, 420].map((x) => `<path d="M${x - 26} 380 Q${x - 30} 340 ${x} 330 Q${x + 30} 340 ${x + 26} 380Z" fill="#fff"/>`).join('')}
       <circle cx="300" cy="300" r="34" fill="url(#cherry)"/>
     </g>
     <path d="M300 268 Q310 220 340 200" stroke="#3a8a3f" stroke-width="6" fill="none" stroke-linecap="round"/>
     ${shine(288, 288, 8, 12, -20, 0.7)}
     ${[[90, 720, '#a5e3d0'], [510, 720, '#c9b6ff'], [300, 740, '#ffd59e']].map(([x, y, c]) => `<g filter="url(#sh)"><ellipse cx="${x}" cy="${y - 18}" rx="52" ry="22" fill="${c}"/><rect x="${x - 48}" y="${y - 12}" width="96" height="16" rx="8" fill="#fff8e7"/><ellipse cx="${x}" cy="${y + 14}" rx="52" ry="22" fill="${c}"/></g>`).join('')}
     ${[[120, 200, '#ff8fab'], [480, 180, '#a29bfe'], [90, 360, '#ffd166'], [520, 330, '#8fd3ff']].map(([x, y, c]) => `<rect x="${x}" y="${y}" width="14" height="5" rx="2.5" fill="${c}" transform="rotate(${x % 90} ${x} ${y})"/>`).join('')}
     ${K.sparkle(170, 300, 12, '#fff')}${K.sparkle(450, 270, 10, '#fff')}
     ${face(300, 500, 0.9)}`
  );

  IT.Samples.register({ key: 'food', name: '과일 및 음식', icon: '🍓' }, [
    { key: 'apple', name: '사과', svg: apple },
    { key: 'pear', name: '배', svg: pear },
    { key: 'strawberry', name: '딸기', svg: strawberry },
    { key: 'watermelon', name: '수박', svg: watermelon },
    { key: 'dessert', name: '디저트', svg: dessert },
  ]);
})();
