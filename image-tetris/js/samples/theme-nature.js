/* 샘플 테마 1. 자연 풍경 (오리지널 SVG 일러스트) */
(function () {
  'use strict';
  const IT = globalThis.IT;
  const K = IT.SvgKit;

  /* 푸른 산과 호수 */
  const mountainLake = K.svg(
    K.lin('sky', [[0, '#5aa9e6'], [0.55, '#a9d6f5'], [1, '#e6f4ff']]) +
      K.lin('lake', [[0, '#3f8fc9'], [1, '#1d4f80']]) +
      K.lin('m1', [[0, '#7d8fd6'], [1, '#5468b0']]) +
      K.lin('m2', [[0, '#3f9c7a'], [1, '#226b55']]) +
      K.rad('sun', [[0, '#fffbe6'], [0.5, '#fff1a8', 0.9], [1, '#fff1a8', 0]]) +
      K.blur('b4', 4),
    `<rect width="600" height="800" fill="url(#sky)"/>
     <circle cx="450" cy="150" r="120" fill="url(#sun)"/><circle cx="450" cy="150" r="46" fill="#fffdf0"/>
     ${K.cloud(140, 130, 1.1, '#fff', 0.95)}${K.cloud(360, 240, 0.7, '#fff', 0.85)}
     <path d="M0 440 L90 300 L150 360 L250 210 L340 330 L420 250 L520 360 L600 290 L600 470 L0 470Z" fill="url(#m1)"/>
     <path d="M250 210 L282 252 L265 250 L250 266 L236 248 L220 254Z M420 250 L446 282 L430 280 L418 292 L405 278Z M90 300 L112 330 L98 328 L88 340 L76 326Z" fill="#fff" opacity=".92"/>
     <path d="M0 470 L120 380 L200 430 L300 350 L400 440 L480 400 L600 460 L600 500 L0 500Z" fill="url(#m2)"/>
     <rect y="498" width="600" height="302" fill="url(#lake)"/>
     <g opacity=".35" transform="translate(0 996) scale(1 -1)">
       <path d="M0 470 L120 380 L200 430 L300 350 L400 440 L480 400 L600 460 L600 500 L0 500Z" fill="#2f7d62"/>
     </g>
     <g opacity=".22" filter="url(#b4)"><path d="M0 556 L90 696 L150 636 L250 786 L340 666 L420 746 L520 636 L600 706 L600 530 L0 530Z" fill="#8fa0e6"/></g>
     <g stroke="#e6f4ff" stroke-linecap="round" opacity=".55">
       <line x1="60" y1="560" x2="150" y2="560" stroke-width="3"/><line x1="330" y1="600" x2="460" y2="600" stroke-width="3"/>
       <line x1="200" y1="650" x2="260" y2="650" stroke-width="2"/><line x1="410" y1="700" x2="520" y2="700" stroke-width="2"/>
       <line x1="380" y1="540" x2="420" y2="540" stroke-width="2"/><line x1="40" y1="680" x2="90" y2="680" stroke-width="2"/>
     </g>
     ${K.pine(40, 520, 0.9, '#1f5e46', '#2c7a5c')}${K.pine(90, 530, 1.2, '#1a523c', '#2c7a5c')}${K.pine(560, 525, 1.05, '#1f5e46', '#2c7a5c')}
     <path d="M0 760 Q150 730 300 760 T600 750 L600 800 L0 800Z" fill="#2c6e4f"/>
     <path d="M0 780 Q160 760 320 785 T600 775 L600 800 L0 800Z" fill="#245c42"/>
     <path d="M250 610 l60 0 l-8 12 l-44 0z" fill="#8a5a3c"/><line x1="282" y1="610" x2="282" y2="566" stroke="#5a3a28" stroke-width="3"/><path d="M284 568 L312 600 L284 600Z" fill="#fff"/>`
  );

  /* 가을 숲 */
  const autumn = K.svg(
    K.lin('sky', [[0, '#f7b267'], [0.6, '#fbd8a0'], [1, '#fdf0d5']]) +
      K.lin('hill', [[0, '#c9783a'], [1, '#9b5426']]) +
      K.lin('path', [[0, '#e8c39e'], [1, '#c99a6c']]),
    `<rect width="600" height="800" fill="url(#sky)"/>
     <circle cx="120" cy="170" r="70" fill="#fff3d6" opacity=".9"/>
     <path d="M0 430 Q150 360 300 410 T600 380 L600 800 L0 800Z" fill="#e39b5a" opacity=".7"/>
     ${K.roundTree(60, 420, 1, '#e86f3c', '#c84f2a')}${K.roundTree(170, 400, 0.9, '#f2b134', '#d98d1c')}${K.roundTree(300, 410, 1.05, '#d9452f', '#b0321f')}
     ${K.roundTree(430, 395, 0.95, '#f2c14e', '#d99a1c')}${K.roundTree(550, 415, 1.1, '#e0662f', '#bb4a1d')}
     <path d="M0 520 Q160 470 320 510 T600 490 L600 800 L0 800Z" fill="url(#hill)"/>
     ${K.roundTree(110, 600, 1.5, '#f08a3c', '#d1622a')}${K.roundTree(500, 610, 1.6, '#e5492f', '#bc3020')}${K.roundTree(380, 560, 1.2, '#f6c445', '#da9f1e')}
     <path d="M240 800 Q290 700 300 640 Q320 600 360 560 L380 565 Q350 610 345 650 Q340 720 380 800Z" fill="url(#path)"/>
     <path d="M0 700 Q100 680 180 720 L180 800 L0 800Z" fill="#8a4a22"/><path d="M420 720 Q520 690 600 710 L600 800 L420 800Z" fill="#8a4a22"/>
     ${[[80, 300, '#e86f3c', 20], [250, 260, '#f2b134', -30], [380, 320, '#d9452f', 45], [520, 250, '#f2c14e', 10], [200, 470, '#e86f3c', 70], [460, 480, '#f2b134', -60], [320, 720, '#d9452f', 30], [70, 760, '#f2c14e', -20], [560, 760, '#e0662f', 50]].map(([x, y, c, a]) => `<path transform="translate(${x} ${y}) rotate(${a})" d="M0 -14 Q10 -4 0 14 Q-10 -4 0 -14Z" fill="${c}"/><line transform="translate(${x} ${y}) rotate(${a})" x1="0" y1="-12" x2="0" y2="16" stroke="#7a3d1a" stroke-width="1.4"/>`).join('')}`
  );

  /* 아름다운 해변 */
  const beach = K.svg(
    K.lin('sky', [[0, '#4fc3f7'], [1, '#d4f1ff']]) +
      K.lin('sea', [[0, '#1aa7c9'], [0.6, '#38c6d9'], [1, '#7fe3e0']]) +
      K.lin('sand', [[0, '#f9dfa8'], [1, '#efc47a']]) +
      K.rad('sun', [[0, '#fff'], [0.4, '#fff7b0'], [1, '#fff7b0', 0]]),
    `<rect width="600" height="800" fill="url(#sky)"/>
     <circle cx="470" cy="140" r="110" fill="url(#sun)"/>
     ${K.cloud(140, 150, 0.9, '#fff', 0.95)}${K.cloud(330, 90, 0.6, '#fff', 0.8)}
     <path d="M80 220 q12 -12 24 0 q12 -12 24 0" fill="none" stroke="#2a4d69" stroke-width="3" stroke-linecap="round"/>
     <path d="M200 260 q9 -9 18 0 q9 -9 18 0" fill="none" stroke="#2a4d69" stroke-width="2.5" stroke-linecap="round"/>
     <rect y="360" width="600" height="250" fill="url(#sea)"/>
     <rect y="358" width="600" height="6" fill="#e6fbff" opacity=".6"/>
     <g stroke="#e9fdff" stroke-width="3" stroke-linecap="round" opacity=".7" fill="none">
       <path d="M40 420 q20 -8 40 0"/><path d="M300 400 q25 -10 50 0"/><path d="M460 450 q20 -8 40 0"/><path d="M150 480 q25 -10 50 0"/><path d="M380 520 q30 -10 60 0"/>
     </g>
     <path d="M0 600 Q150 570 300 590 T600 580 L600 800 L0 800Z" fill="url(#sand)"/>
     <path d="M0 600 Q150 570 300 590 T600 580 L600 600 Q450 615 300 605 T0 620Z" fill="#fff" opacity=".75"/>
     <path d="M470 760 Q480 600 430 450" fill="none" stroke="#8b5a2b" stroke-width="18" stroke-linecap="round"/>
     <g fill="#2e9e5b"><path d="M430 450 Q370 420 330 460 Q380 440 430 455Z"/><path d="M430 450 Q400 390 340 390 Q400 410 432 452Z"/><path d="M430 450 Q460 390 520 395 Q465 415 433 452Z"/><path d="M430 450 Q500 430 540 480 Q490 450 432 456Z"/><path d="M430 450 Q430 400 460 370 Q440 410 434 452Z"/></g>
     <circle cx="425" cy="462" r="9" fill="#7a4a1e"/><circle cx="440" cy="466" r="8" fill="#7a4a1e"/>
     <line x1="150" y1="740" x2="190" y2="600" stroke="#7a5a3a" stroke-width="5"/>
     <path d="M90 625 Q190 540 290 625Z" fill="#ff6b6b"/><path d="M123 625 Q190 545 190 545 Q190 545 157 625Z" fill="#fff" opacity=".85"/><path d="M223 625 Q190 545 190 545 Q190 545 257 625Z" fill="#fff" opacity=".85"/>
     <ellipse cx="300" cy="730" rx="70" ry="10" fill="#e0b56c"/><rect x="235" y="700" width="130" height="28" rx="6" fill="#ffd166"/><rect x="235" y="700" width="130" height="8" rx="4" fill="#ff9f43"/>
     <path d="M90 760 l8 -14 l8 14 l14 2 l-10 10 l2 14 l-14 -7 l-14 7 l2 -14 l-10 -10Z" fill="#ff8c69"/>
     <ellipse cx="520" cy="740" rx="16" ry="10" fill="#fff"/><path d="M506 740 q14 -16 28 0" fill="#f7c5d0"/>`
  );

  /* 별이 가득한 밤하늘 */
  const starryNight = K.svg(
    K.lin('sky', [[0, '#0b1033'], [0.55, '#1f2a6b'], [1, '#43407f']]) +
      K.lin('milky', [[0, '#9fb4ff', 0], [0.5, '#c9b8ff', 0.55], [1, '#9fb4ff', 0]], 0, 0, 1, 1) +
      K.blur('b20', 22) + K.blur('b3', 3) +
      K.rad('moonGlow', [[0, '#fff8d8', 0.7], [1, '#fff8d8', 0]]) +
      '<mask id="crescent"><rect width="600" height="800" fill="#fff"/><circle cx="484" cy="124" r="44" fill="#000"/></mask>',
    `<rect width="600" height="800" fill="url(#sky)"/>
     <g filter="url(#b20)"><path d="M-40 520 Q200 300 640 120 L660 220 Q260 380 -20 620Z" fill="url(#milky)"/></g>
     ${K.stars(170, 11, 0, 0, 600, 600, '#fff', 2.4)}${K.stars(40, 12, 0, 0, 600, 560, '#ffe9a8', 2.6)}
     ${K.sparkle(120, 120, 14, '#fff')}${K.sparkle(500, 330, 10, '#fff')}${K.sparkle(300, 210, 8, '#ffe9a8')}
     <circle cx="460" cy="140" r="110" fill="url(#moonGlow)"/>
     <circle cx="460" cy="140" r="48" fill="#fff6d0" mask="url(#crescent)"/>
     <path d="M80 80 L230 160" stroke="#fff" stroke-width="3" stroke-linecap="round" opacity=".9"/><path d="M80 80 L180 133" stroke="#fff" stroke-width="7" stroke-linecap="round" opacity=".25" filter="url(#b3)"/>
     <path d="M0 610 L90 520 L160 570 L260 470 L360 560 L440 500 L520 560 L600 520 L600 800 L0 800Z" fill="#141a45"/>
     <path d="M0 680 Q150 630 300 670 T600 650 L600 800 L0 800Z" fill="#0d1230"/>
     ${K.pine(60, 690, 1.1, '#0a0e26', '#141a45')}${K.pine(120, 700, 0.8, '#0a0e26', '#141a45')}${K.pine(540, 680, 1.2, '#0a0e26', '#141a45')}
     <path d="M300 720 L360 640 L420 720Z" fill="#f2a65a"/><path d="M360 640 L380 720 L360 720Z" fill="#c96f2a"/><path d="M350 720 L360 690 L370 720Z" fill="#ffe08a"/>
     <circle cx="300" cy="740" r="4" fill="#ffd27a"/><circle cx="300" cy="740" r="20" fill="#ffd27a" opacity=".2"/>`
  );

  IT.Samples.register({ key: 'nature', name: '자연 풍경', icon: '🏞️' }, [
    { key: 'mountain-lake', name: '푸른 산과 호수', svg: mountainLake },
    { key: 'autumn-forest', name: '가을 숲', svg: autumn },
    { key: 'beach', name: '아름다운 해변', svg: beach },
    { key: 'starry-night', name: '별이 가득한 밤하늘', svg: starryNight },
  ]);
})();
