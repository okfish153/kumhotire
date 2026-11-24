/* 샘플 테마 4. 자동차 (오리지널 SVG 일러스트, 특정 브랜드/모델 아님) */
(function () {
  'use strict';
  const IT = globalThis.IT;
  const K = IT.SvgKit;

  /* 클래식 자동차 */
  const classic = K.svg(
    K.lin('sky', [[0, '#ffd8a8'], [1, '#fff4e0']]) + K.lin('body', [[0, '#e8454f'], [1, '#b52a35']]) +
      K.lin('chrome', [[0, '#ffffff'], [0.5, '#c9d1db'], [1, '#8d97a5']]) + K.shadow('sh', 6, 6, 0.3),
    `<rect width="600" height="800" fill="url(#sky)"/>
     <circle cx="430" cy="210" r="90" fill="#ffb27a" opacity=".6"/>
     ${[[20, 260, 90, 260, '#e9b38a'], [120, 200, 80, 320, '#d99a74'], [210, 290, 100, 230, '#efc49e'], [320, 230, 70, 290, '#d99a74'], [400, 300, 110, 220, '#e9b38a'], [520, 240, 80, 280, '#d99a74']].map(([x, y, w, h, c]) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${c}"/>${Array.from({ length: Math.floor(h / 50) }, (_, r) => Array.from({ length: Math.floor(w / 30) }, (_, q) => `<rect x="${x + 10 + q * 30}" y="${y + 16 + r * 50}" width="14" height="24" fill="#fff3dd" opacity=".8"/>`).join('')).join('')}`).join('')}
     <rect y="530" width="600" height="270" fill="#6b6f7a"/><rect y="530" width="600" height="14" fill="#c9cdd6"/>
     ${[40, 200, 360, 520].map((x) => `<rect x="${x}" y="700" width="80" height="12" rx="6" fill="#f5f0e1"/>`).join('')}
     <g filter="url(#sh)">
       <path d="M60 620 Q60 560 120 548 L180 540 Q220 470 300 462 Q380 462 420 530 L500 545 Q550 556 552 610 L552 640 L60 640Z" fill="url(#body)"/>
       <path d="M200 540 Q232 486 300 482 L300 540Z" fill="#bfe5ff"/><path d="M314 540 L314 482 Q374 484 400 535Z" fill="#bfe5ff"/>
       <path d="M60 600 L552 600" stroke="#f5f0e1" stroke-width="10"/>
       <rect x="40" y="625" width="80" height="18" rx="9" fill="url(#chrome)"/><rect x="490" y="625" width="80" height="18" rx="9" fill="url(#chrome)"/>
       <circle cx="536" cy="580" r="14" fill="#fff3b0"/><circle cx="74" cy="584" r="10" fill="#ffb3b3"/>
       ${K.wheel(160, 640, 48, '#24262b', '#f5f0e1', '#9aa3ae')}${K.wheel(450, 640, 48, '#24262b', '#f5f0e1', '#9aa3ae')}
     </g>
     <path d="M210 500 Q240 475 280 472" stroke="#fff" stroke-width="5" fill="none" opacity=".6" stroke-linecap="round"/>
     <ellipse cx="300" cy="700" rx="270" ry="10" fill="#000" opacity=".12"/>`
  );

  /* 스포츠카 */
  const sports = K.svg(
    K.lin('sky', [[0, '#3b1c6b'], [0.5, '#e0457b'], [1, '#ffb36b']]) + K.lin('body', [[0, '#ffd23f'], [1, '#f59f00']]) +
      K.lin('road', [[0, '#2d2a3a'], [1, '#18161f']]) + K.rad('sun', [[0, '#fff3b0'], [1, '#ff8a5c']]) + K.shadow('sh', 6, 6, 0.35),
    `<rect width="600" height="800" fill="url(#sky)"/>
     <circle cx="300" cy="430" r="150" fill="url(#sun)"/>
     ${[0, 1, 2, 3, 4].map((i) => `<rect x="150" y="${470 + i * 18}" width="300" height="${6 + i}" fill="#e0457b"/>`).join('')}
     <path d="M0 470 L120 400 L220 460 L330 380 L460 450 L600 400 L600 560 L0 560Z" fill="#2b164f" opacity=".9"/>
     <path d="M0 560 L600 560 L600 800 L0 800Z" fill="url(#road)"/>
     <path d="M300 560 L250 800 M300 560 L350 800" stroke="#ff5fa2" stroke-width="3" opacity=".5"/>
     ${[0, 1, 2, 3].map((i) => `<rect x="${296 - i * 4}" y="${580 + i * 55}" width="${8 + i * 8}" height="${18 + i * 10}" fill="#ffd23f" opacity=".85"/>`).join('')}
     <g stroke="#fff" stroke-linecap="round" opacity=".55"><line x1="0" y1="590" x2="120" y2="590" stroke-width="4"/><line x1="10" y1="625" x2="90" y2="625" stroke-width="3"/><line x1="0" y1="660" x2="140" y2="660" stroke-width="4"/></g>
     <g filter="url(#sh)">
       <path d="M110 650 Q100 610 150 600 L240 590 Q290 548 360 546 Q420 548 470 590 L540 606 Q575 616 572 650 L572 662 L110 662Z" fill="url(#body)"/>
       <path d="M262 590 Q300 560 352 558 L352 590Z" fill="#2b2240"/><path d="M364 590 L364 558 Q410 562 440 592Z" fill="#2b2240"/>
       <path d="M140 630 L560 630" stroke="#1d1a26" stroke-width="5"/>
       <path d="M540 612 L572 620 L570 632 L536 626Z" fill="#fffbe6"/><path d="M108 622 L130 618 L130 632 L108 636Z" fill="#ff4d6d"/>
       <path d="M110 600 L170 592 L168 602 L112 610Z" fill="#1d1a26"/>
       ${K.wheel(200, 662, 40, '#15131b', '#444150', '#ffd23f')}${K.wheel(480, 662, 40, '#15131b', '#444150', '#ffd23f')}
     </g>
     <path d="M280 580 Q310 562 345 560" stroke="#fff" stroke-width="4" fill="none" opacity=".5" stroke-linecap="round"/>
     ${K.stars(30, 55, 0, 0, 600, 300, '#fff', 1.8)}`
  );

  /* 미래형 자동차 */
  const future = K.svg(
    K.lin('sky', [[0, '#050a24'], [0.6, '#1a1050'], [1, '#3a1a6b']]) + K.lin('body', [[0, '#eef3ff'], [0.5, '#b7c4e6'], [1, '#7f8fbf']]) +
      K.lin('glow', [[0, '#3df5ff', 0.9], [1, '#3df5ff', 0]]) + K.blur('b8', 8) + K.blur('b2', 2),
    `<rect width="600" height="800" fill="url(#sky)"/>
     ${K.stars(60, 91, 0, 0, 600, 300, '#cfe8ff', 1.6)}
     ${[[0, 300, 70, '#1f1b4f'], [60, 220, 60, '#2a1f66'], [130, 340, 80, '#1f1b4f'], [220, 180, 70, '#2a1f66'], [300, 280, 90, '#1f1b4f'], [400, 200, 60, '#2a1f66'], [470, 320, 80, '#1f1b4f'], [540, 250, 60, '#2a1f66']].map(([x, y, w, c]) => `<rect x="${x}" y="${y}" width="${w}" height="${560 - y}" fill="${c}"/>${Array.from({ length: Math.floor((560 - y) / 30) }, (_, r) => `<rect x="${x + 8}" y="${y + 12 + r * 30}" width="${w - 16}" height="5" fill="${r % 3 ? '#ff4fd8' : '#3df5ff'}" opacity="${r % 2 ? 0.35 : 0.7}"/>`).join('')}`).join('')}
     <rect y="560" width="600" height="240" fill="#0c0a26"/>
     ${[0, 1, 2, 3, 4, 5].map((i) => `<line x1="0" y1="${580 + i * 40}" x2="600" y2="${580 + i * 40}" stroke="#ff4fd8" stroke-width="2" opacity="${0.5 - i * 0.07}"/>`).join('')}
     ${[-3, -2, -1, 0, 1, 2, 3].map((i) => `<line x1="${300 + i * 40}" y1="560" x2="${300 + i * 200}" y2="800" stroke="#3df5ff" stroke-width="2" opacity=".35"/>`).join('')}
     <ellipse cx="310" cy="640" rx="210" ry="22" fill="#3df5ff" opacity=".55" filter="url(#b8)"/>
     <path d="M90 560 Q130 500 250 480 Q350 466 420 490 Q520 520 540 560 Q520 586 470 590 L150 590 Q100 586 90 560Z" fill="url(#body)"/>
     <path d="M230 496 Q320 470 400 494 Q370 520 300 522 Q250 520 230 496Z" fill="#0e1a4a"/><path d="M250 498 Q310 482 370 496" stroke="#3df5ff" stroke-width="3" fill="none" opacity=".7"/>
     <path d="M100 562 L540 562" stroke="#3df5ff" stroke-width="5" filter="url(#b2)"/><path d="M100 562 L540 562" stroke="#e6feff" stroke-width="2"/>
     <path d="M500 548 L548 556 L540 566 L496 560Z" fill="#e6feff"/><path d="M92 552 L120 548 L118 560 L94 562Z" fill="#ff4fd8"/>
     <ellipse cx="200" cy="592" rx="50" ry="10" fill="#3df5ff"/><ellipse cx="440" cy="592" rx="50" ry="10" fill="#3df5ff"/>
     <rect x="130" y="598" width="380" height="60" fill="url(#glow)" opacity=".5"/>
     <path d="M60 140 L140 140" stroke="#ff4fd8" stroke-width="4" stroke-linecap="round"/><circle cx="146" cy="140" r="6" fill="#ff4fd8"/>
     <path d="M420 100 L470 100" stroke="#3df5ff" stroke-width="3" stroke-linecap="round"/><circle cx="476" cy="100" r="4" fill="#3df5ff"/>`
  );

  /* 오프로드 자동차 */
  const offroad = K.svg(
    K.lin('sky', [[0, '#8ecae6'], [1, '#e8f6ff']]) + K.lin('body', [[0, '#5f9e4a'], [1, '#3e7a32']]) + K.lin('mud', [[0, '#a0703f'], [1, '#6e4a26']]) +
      K.shadow('sh', 6, 6, 0.3),
    `<rect width="600" height="800" fill="url(#sky)"/>
     ${K.cloud(120, 120, 0.9, '#fff')}${K.cloud(460, 170, 0.7, '#fff')}
     <path d="M0 420 L130 250 L230 360 L330 220 L460 380 L600 260 L600 520 L0 520Z" fill="#8a9bb5"/>
     <path d="M330 220 L360 262 L340 258 L330 272 L318 258 L300 262Z M130 250 L155 284 L140 282 L130 294 L120 282 L106 286Z" fill="#fff"/>
     <path d="M0 470 Q150 410 300 470 T600 450 L600 800 L0 800Z" fill="#c9a26b"/>
     <path d="M0 640 Q120 600 260 660 Q400 720 600 650 L600 800 L0 800Z" fill="url(#mud)"/>
     ${K.pine(50, 470, 0.9, '#2e6b3a', '#3f8a4c')}${K.pine(560, 470, 1.1, '#2e6b3a', '#3f8a4c')}
     <g filter="url(#sh)">
       <path d="M90 600 L100 520 L170 510 L200 430 L420 430 L450 510 L520 520 L530 600Z" fill="url(#body)"/>
       <path d="M215 445 L300 445 L300 505 L195 505Z" fill="#cdeaff"/><path d="M312 445 L405 445 L430 505 L312 505Z" fill="#cdeaff"/>
       <rect x="190" y="410" width="240" height="18" rx="6" fill="#2f3a2b"/><rect x="210" y="396" width="60" height="16" rx="4" fill="#d9822b"/><rect x="290" y="396" width="90" height="16" rx="4" fill="#4a5a44"/>
       <rect x="80" y="585" width="70" height="22" rx="6" fill="#2f3a2b"/><rect x="470" y="585" width="70" height="22" rx="6" fill="#2f3a2b"/>
       <circle cx="512" cy="545" r="13" fill="#fff6c4"/><rect x="100" y="535" width="20" height="16" rx="4" fill="#ff6b6b"/>
       <rect x="300" y="520" width="24" height="6" rx="3" fill="#2f3a2b"/>
       ${K.wheel(170, 610, 58, '#1d1f22', '#7a8088', '#cfd3d8')}${K.wheel(450, 610, 58, '#1d1f22', '#7a8088', '#cfd3d8')}
     </g>
     ${[[100, 690, 10], [140, 676, 7], [520, 690, 11], [560, 672, 6], [300, 700, 8]].map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="#6e4a26"/>`).join('')}
     <path d="M70 560 q-30 -10 -50 10 M60 580 q-30 0 -46 22" stroke="#a0703f" stroke-width="6" fill="none" stroke-linecap="round" opacity=".7"/>`
  );

  IT.Samples.register({ key: 'cars', name: '자동차', icon: '🚗' }, [
    { key: 'classic-car', name: '클래식 자동차', svg: classic },
    { key: 'sports-car', name: '스포츠카', svg: sports },
    { key: 'future-car', name: '미래형 자동차', svg: future },
    { key: 'offroad-car', name: '오프로드 자동차', svg: offroad },
  ]);
})();
