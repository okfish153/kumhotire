/* 샘플 테마 3. 클레이 애니메이션 스타일 (오리지널 SVG 일러스트, 점토 질감 필터) */
(function () {
  'use strict';
  const IT = globalThis.IT;
  const K = IT.SvgKit;

  // 점토 느낌: 부드러운 그림자 + 하이라이트 + 미세 노이즈
  const CLAY_DEFS = K.shadow('clay', 9, 6, 0.22) + K.grain('grain', 0.9) + K.blur('soft', 2);
  const hi = (x, y, rx, ry, op = 0.35) => `<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="#fff" opacity="${op}" filter="url(#soft)"/>`;

  /* 귀여운 점토 캐릭터 */
  const character = K.svg(
    CLAY_DEFS + K.lin('bg', [[0, '#ffe3ef'], [1, '#d9e8ff']]) + K.rad('body', [[0, '#9ee6c8'], [1, '#55c39a']], 0.4, 0.3, 0.8),
    `<rect width="600" height="800" fill="url(#bg)"/>
     <g filter="url(#clay)">
       <ellipse cx="300" cy="700" rx="240" ry="60" fill="#c9b7ff"/>
       ${[[90, 620, '#ffb3c7'], [510, 640, '#ffd59e'], [150, 690, '#a8d8ff']].map(([x, y, c]) => `<g transform="translate(${x} ${y})">${[0, 72, 144, 216, 288].map((a) => `<circle cx="${(Math.cos(a * Math.PI / 180) * 18).toFixed(1)}" cy="${(Math.sin(a * Math.PI / 180) * 18).toFixed(1)}" r="14" fill="${c}"/>`).join('')}<circle r="11" fill="#fff4b8"/></g>`).join('')}
       <ellipse cx="180" cy="470" rx="40" ry="28" transform="rotate(-30 180 470)" fill="#55c39a"/>
       <ellipse cx="420" cy="430" rx="40" ry="28" transform="rotate(35 420 430)" fill="#55c39a"/>
       <path d="M300 220 C430 220 450 360 450 470 C450 600 390 660 300 660 C210 660 150 600 150 470 C150 360 170 220 300 220Z" fill="url(#body)"/>
       <ellipse cx="240" cy="670" rx="46" ry="24" fill="#3fa77f"/><ellipse cx="360" cy="670" rx="46" ry="24" fill="#3fa77f"/>
       <path d="M300 222 Q290 160 320 130" stroke="#3fa77f" stroke-width="12" fill="none" stroke-linecap="round"/>
       <circle cx="324" cy="124" r="22" fill="#ffd166"/>
     </g>
     ${hi(240, 300, 60, 34)}${hi(318, 116, 8, 6, 0.6)}
     <ellipse cx="250" cy="420" rx="34" ry="40" fill="#fff"/><ellipse cx="350" cy="420" rx="34" ry="40" fill="#fff"/>
     ${K.eye(256, 428, 20, 25, '#2b2233')}${K.eye(344, 428, 20, 25, '#2b2233')}
     <ellipse cx="205" cy="490" rx="24" ry="14" fill="#ff8fa3" opacity=".55"/><ellipse cx="395" cy="490" rx="24" ry="14" fill="#ff8fa3" opacity=".55"/>
     <path d="M265 500 Q300 545 335 500Z" fill="#7a2e3b"/><path d="M280 520 Q300 538 320 520 Q300 512 280 520Z" fill="#ff8fa3"/>
     ${K.sparkle(110, 160, 18, '#fff')}${K.sparkle(490, 220, 14, '#fff')}${K.sparkle(470, 110, 9, '#ffd166')}
     ${K.grainRect('grain', 0.12)}`
  );

  /* 동화 속 마을 (버섯 집) */
  const village = K.svg(
    CLAY_DEFS + K.lin('bg', [[0, '#bfe6ff'], [1, '#fff3d9']]) + K.lin('hill', [[0, '#a7e08f'], [1, '#79c26a']]),
    `<rect width="600" height="800" fill="url(#bg)"/>
     <g filter="url(#clay)">
       ${K.cloud(140, 120, 1, '#fff')}${K.cloud(450, 190, 0.8, '#fff')}
       <circle cx="500" cy="90" r="42" fill="#ffd166"/>
       <path d="M0 470 Q160 390 320 450 T600 420 L600 800 L0 800Z" fill="#b9e6a4"/>
       <path d="M0 560 Q200 500 360 560 T600 540 L600 800 L0 800Z" fill="url(#hill)"/>
       <!-- 큰 버섯 집 -->
       <rect x="170" y="430" width="150" height="190" rx="40" fill="#fff4e0"/>
       <path d="M120 450 Q130 300 245 290 Q360 300 370 450 Q245 480 120 450Z" fill="#ff6b6b"/>
       <rect x="215" y="530" width="60" height="90" rx="30" fill="#b5703a"/>
       <circle cx="262" cy="578" r="5" fill="#ffd166"/>
       <circle cx="200" cy="500" r="20" fill="#8fd3ff"/><circle cx="292" cy="490" r="16" fill="#8fd3ff"/>
       <!-- 작은 버섯 집 -->
       <rect x="400" y="500" width="100" height="120" rx="30" fill="#fff4e0"/>
       <path d="M370 515 Q380 410 450 405 Q520 410 530 515 Q450 535 370 515Z" fill="#a29bfe"/>
       <rect x="432" y="560" width="38" height="60" rx="19" fill="#b5703a"/>
       <circle cx="490" cy="545" r="12" fill="#8fd3ff"/>
       <!-- 길과 울타리 -->
       <path d="M245 620 Q230 700 180 800 L300 800 Q280 700 275 620Z" fill="#f3d9a4"/>
       ${[40, 80, 120, 520, 560].map((x) => `<rect x="${x}" y="600" width="16" height="60" rx="6" fill="#d9a066"/>`).join('')}
       <rect x="30" y="618" width="110" height="10" rx="5" fill="#d9a066"/><rect x="510" y="618" width="80" height="10" rx="5" fill="#d9a066"/>
       ${[[90, 720, '#ff8fb1'], [400, 700, '#ffd166'], [520, 740, '#8fd3ff'], [60, 520, '#ffd166']].map(([x, y, c]) => `<circle cx="${x}" cy="${y}" r="16" fill="${c}"/><circle cx="${x}" cy="${y}" r="6" fill="#fff"/>`).join('')}
     </g>
     ${[[175, 380, 18], [250, 340, 22], [320, 400, 16], [210, 430, 12], [420, 450, 13], [470, 430, 10]].map(([x, y, r]) => `<circle cx="${x}" cy="${y}" r="${r}" fill="#fff" opacity=".92"/>`).join('')}
     ${hi(200, 330, 50, 18)}${hi(430, 425, 34, 12)}
     ${K.grainRect('grain', 0.12)}`
  );

  /* 작은 숲속 동물 (고슴도치) */
  const critter = K.svg(
    CLAY_DEFS + K.lin('bg', [[0, '#d8f3dc'], [1, '#fdf6e3']]),
    `<rect width="600" height="800" fill="url(#bg)"/>
     <g filter="url(#clay)">
       ${[[60, 300, 1.3], [540, 330, 1.5], [470, 230, 0.9]].map(([x, y, s]) => K.roundTree(x, y, s, '#8fd694', '#5fb76a', '#a0703f')).join('')}
       <path d="M0 600 Q300 540 600 600 L600 800 L0 800Z" fill="#9bd48a"/>
       <path d="M0 680 Q300 640 600 680 L600 800 L0 800Z" fill="#82c472"/>
       <path d="M140 600 C140 420 470 400 470 600Z" fill="#8a5a3c"/>
       ${Array.from({ length: 14 }, (_, i) => { const a = Math.PI + (i / 13) * Math.PI; const x = 305 + Math.cos(a) * 175, y = 600 + Math.sin(a) * 165; const x2 = 305 + Math.cos(a) * 215, y2 = 600 + Math.sin(a) * 205; return `<path d="M${(x - Math.sin(a) * 22).toFixed(1)} ${(y + Math.cos(a) * 22).toFixed(1)} L${x2.toFixed(1)} ${y2.toFixed(1)} L${(x + Math.sin(a) * 22).toFixed(1)} ${(y - Math.cos(a) * 22).toFixed(1)}Z" fill="#6e4429"/>`; }).join('')}
       <path d="M150 600 C150 440 460 420 460 600Z" fill="#8a5a3c"/>
       <ellipse cx="200" cy="560" rx="90" ry="70" fill="#f3d3ae"/>
       <ellipse cx="200" cy="640" rx="70" ry="20" fill="#e0b98c"/>
       <!-- 버섯 -->
       <rect x="450" y="560" width="34" height="70" rx="14" fill="#fff4e0"/><path d="M420 570 Q425 510 467 506 Q510 510 514 570Z" fill="#ff6b6b"/>
       <rect x="92" y="640" width="22" height="40" rx="10" fill="#fff4e0"/><path d="M74 646 Q78 610 103 608 Q128 610 132 646Z" fill="#ffb347"/>
       <!-- 사과 -->
       <circle cx="330" cy="430" r="26" fill="#ff5d5d"/><path d="M330 404 q8 -16 22 -14 q-8 12 -22 14z" fill="#5fb76a"/>
     </g>
     <circle cx="458" cy="530" r="8" fill="#fff"/><circle cx="480" cy="548" r="6" fill="#fff"/><circle cx="100" cy="624" r="5" fill="#fff"/>
     ${K.eye(178, 545, 13, 16)}
     <circle cx="118" cy="572" r="14" fill="#3a2621"/>
     <ellipse cx="200" cy="590" rx="18" ry="10" fill="#ff8fa3" opacity=".6"/>
     <path d="M150 594 q12 10 24 2" stroke="#3a2621" stroke-width="4" fill="none" stroke-linecap="round"/>
     ${hi(320, 420, 9, 6, 0.6)}${hi(250, 500, 40, 16, 0.25)}
     ${K.grainRect('grain', 0.12)}`
  );

  /* 파스텔톤 판타지 세계 */
  const fantasy = K.svg(
    CLAY_DEFS + K.lin('bg', [[0, '#c9b6ff'], [0.5, '#ffc6e0'], [1, '#ffe9c7']]),
    `<rect width="600" height="800" fill="url(#bg)"/>
     ${K.stars(40, 77, 0, 0, 600, 360, '#fff', 2.5)}
     <g fill="none" stroke-linecap="round" stroke-width="22" opacity=".85">
       <path d="M40 520 A260 260 0 0 1 560 520" stroke="#ff9aa2"/><path d="M62 520 A238 238 0 0 1 538 520" stroke="#ffdac1"/>
       <path d="M84 520 A216 216 0 0 1 516 520" stroke="#e2f0cb"/><path d="M106 520 A194 194 0 0 1 494 520" stroke="#b5ead7"/>
       <path d="M128 520 A172 172 0 0 1 472 520" stroke="#c7ceea"/>
     </g>
     <g filter="url(#clay)">
       ${K.cloud(110, 560, 1.4, '#fff')}${K.cloud(480, 570, 1.5, '#fff')}${K.cloud(300, 640, 2.2, '#fff')}
       <!-- 성 -->
       <rect x="215" y="390" width="170" height="200" rx="12" fill="#fff0f6"/>
       <rect x="185" y="330" width="60" height="260" rx="10" fill="#ffe0ee"/><rect x="355" y="330" width="60" height="260" rx="10" fill="#ffe0ee"/>
       <rect x="270" y="290" width="60" height="140" rx="10" fill="#fff6fb"/>
       <path d="M175 335 L215 250 L255 335Z" fill="#a29bfe"/><path d="M345 335 L385 250 L425 335Z" fill="#a29bfe"/><path d="M260 295 L300 200 L340 295Z" fill="#ff8fc7"/>
       <rect x="272" y="500" width="56" height="90" rx="28" fill="#b38bfa"/>
       <circle cx="215" cy="400" r="14" fill="#8fd3ff"/><circle cx="385" cy="400" r="14" fill="#8fd3ff"/><circle cx="300" cy="350" r="14" fill="#8fd3ff"/>
       <path d="M300 200 L300 165" stroke="#b38bfa" stroke-width="5"/><path d="M300 165 L330 175 L300 185Z" fill="#ffd166"/>
       ${K.cloud(300, 720, 2.6, '#fff')}
     </g>
     ${K.sparkle(90, 140, 20, '#fff')}${K.sparkle(500, 120, 16, '#fff')}${K.sparkle(450, 300, 10, '#fff')}${K.sparkle(140, 330, 12, '#fff')}
     ${hi(205, 360, 14, 40, 0.3)}${hi(375, 360, 14, 40, 0.3)}
     ${K.grainRect('grain', 0.1)}`
  );

  IT.Samples.register({ key: 'clay', name: '클레이 애니메이션', icon: '🧸' }, [
    { key: 'clay-character', name: '귀여운 점토 캐릭터', svg: character },
    { key: 'fairy-village', name: '동화 속 마을', svg: village },
    { key: 'forest-critter', name: '작은 숲속 동물', svg: critter },
    { key: 'pastel-fantasy', name: '파스텔톤 판타지 세계', svg: fantasy },
  ]);
})();
