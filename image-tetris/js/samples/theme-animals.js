/* 샘플 테마 2. 귀여운 동물 (오리지널 SVG 일러스트) */
(function () {
  'use strict';
  const IT = globalThis.IT;
  const K = IT.SvgKit;

  const blush = (x, y, c = '#ff8fa3') => `<ellipse cx="${x}" cy="${y}" rx="26" ry="15" fill="${c}" opacity=".45"/>`;

  /* 고양이 */
  const cat = K.svg(
    K.rad('bg', [[0, '#fff4e8'], [1, '#ffd6b8']], 0.5, 0.45, 0.75) +
      K.rad('fur', [[0, '#ffb66b'], [1, '#f08a2e']], 0.45, 0.35, 0.7) +
      K.shadow('sh', 10, 10, 0.18),
    `<rect width="600" height="800" fill="url(#bg)"/>
     ${K.paw(80, 110, 1.6, '#f5b48a', 0.5)}${K.paw(520, 170, 1.3, '#f5b48a', 0.5)}${K.paw(70, 640, 1.2, '#f5b48a', 0.5)}${K.paw(530, 700, 1.7, '#f5b48a', 0.5)}${K.paw(470, 60, 0.9, '#f5b48a', 0.4)}
     <g filter="url(#sh)">
       <ellipse cx="300" cy="700" rx="185" ry="140" fill="url(#fur)"/>
       <ellipse cx="300" cy="700" rx="95" ry="110" fill="#fff6ea"/>
       <path d="M480 690 Q560 640 540 560 Q530 520 555 500" fill="none" stroke="#f08a2e" stroke-width="34" stroke-linecap="round"/>
       <path d="M150 330 L170 170 L275 280Z" fill="#f08a2e"/><path d="M450 330 L430 170 L325 280Z" fill="#f08a2e"/>
       <path d="M175 300 L186 210 L245 276Z" fill="#ffb3c1"/><path d="M425 300 L414 210 L355 276Z" fill="#ffb3c1"/>
       <ellipse cx="300" cy="430" rx="200" ry="170" fill="url(#fur)"/>
     </g>
     <path d="M270 285 q8 34 0 54 M300 278 q0 40 0 60 M330 285 q-8 34 0 54" stroke="#d96f1a" stroke-width="12" stroke-linecap="round" fill="none"/>
     <path d="M110 410 q30 -6 46 6 M104 450 q32 -2 48 4 M490 410 q-30 -6 -46 6 M496 450 q-32 -2 -48 4" stroke="#d96f1a" stroke-width="10" stroke-linecap="round" fill="none"/>
     <ellipse cx="300" cy="505" rx="90" ry="66" fill="#fff6ea"/>
     ${K.eye(222, 430, 32, 40)}${K.eye(378, 430, 32, 40)}
     ${blush(170, 492)}${blush(430, 492)}
     <path d="M286 478 h28 q-2 16 -14 20 q-12 -4 -14 -20z" fill="#ff7d93"/>
     <path d="M300 498 q-6 24 -34 18 M300 498 q6 24 34 18" stroke="#4b2e2a" stroke-width="5" fill="none" stroke-linecap="round"/>
     <g stroke="#4b2e2a" stroke-width="3" stroke-linecap="round" opacity=".7"><line x1="210" y1="500" x2="120" y2="488"/><line x1="210" y1="514" x2="122" y2="520"/><line x1="390" y1="500" x2="480" y2="488"/><line x1="390" y1="514" x2="478" y2="520"/></g>
     ${K.heart(300, 610, 2.2, '#ff7d93', 0.9)}`
  );

  /* 강아지 */
  const dog = K.svg(
    K.lin('bg', [[0, '#cdeffd'], [1, '#e9f9ff']]) +
      K.rad('face', [[0, '#fff1dc'], [1, '#f4cf9e']], 0.45, 0.35, 0.75) +
      K.shadow('sh', 10, 10, 0.18),
    `<rect width="600" height="800" fill="url(#bg)"/>
     ${K.dots(30, 31, '#9fdcf5', 6, 18, 0.55)}
     <g filter="url(#sh)">
       <ellipse cx="300" cy="720" rx="190" ry="140" fill="#f4cf9e"/>
       <ellipse cx="300" cy="740" rx="100" ry="110" fill="#fff6ea"/>
       <ellipse cx="135" cy="390" rx="62" ry="140" transform="rotate(18 135 390)" fill="#a8683b"/>
       <ellipse cx="465" cy="390" rx="62" ry="140" transform="rotate(-18 465 390)" fill="#a8683b"/>
       <ellipse cx="300" cy="410" rx="185" ry="175" fill="url(#face)"/>
     </g>
     <path d="M200 300 Q230 250 290 270 Q260 320 200 330Z" fill="#c98c55" opacity=".8"/>
     <ellipse cx="300" cy="500" rx="105" ry="78" fill="#fffaf2"/>
     ${K.eye(225, 405, 28, 34)}${K.eye(375, 405, 28, 34)}
     <path d="M205 360 q20 -14 42 -4 M353 356 q22 -10 42 4" stroke="#8a5530" stroke-width="7" fill="none" stroke-linecap="round"/>
     ${blush(175, 470)}${blush(425, 470)}
     <ellipse cx="300" cy="462" rx="30" ry="21" fill="#3a2621"/><ellipse cx="292" cy="455" rx="9" ry="5" fill="#fff" opacity=".6"/>
     <path d="M300 482 v20 M300 502 q-22 22 -44 6 M300 502 q22 22 44 6" stroke="#3a2621" stroke-width="5" fill="none" stroke-linecap="round"/>
     <path d="M278 512 q22 54 44 0z" fill="#ff7d93"/><line x1="300" y1="516" x2="300" y2="540" stroke="#e55e78" stroke-width="3"/>
     <path d="M160 590 Q300 640 440 590 L446 616 Q300 670 154 616Z" fill="#ff5d73"/>
     <circle cx="300" cy="650" r="20" fill="#ffd166"/><circle cx="300" cy="650" r="8" fill="#e8a91d"/>
     <g fill="#fff" opacity=".9"><ellipse cx="110" cy="180" rx="50" ry="18" transform="rotate(-20 110 180)"/><circle cx="72" cy="182" r="18"/><circle cx="76" cy="160" r="18"/><circle cx="148" cy="198" r="18"/><circle cx="150" cy="174" r="18"/></g>`
  );

  /* 토끼 */
  const rabbit = K.svg(
    K.lin('bg', [[0, '#e9f7df'], [1, '#c6ecb0']]) +
      K.rad('fur', [[0, '#ffffff'], [1, '#e8e4f0']], 0.45, 0.35, 0.7) +
      K.shadow('sh', 10, 10, 0.15),
    `<rect width="600" height="800" fill="url(#bg)"/>
     ${K.dots(18, 41, '#fff', 4, 10, 0.8, 0, 0, 600, 300)}
     <path d="M0 690 Q300 640 600 690 L600 800 L0 800Z" fill="#9fd88a"/>
     <g filter="url(#sh)">
       <ellipse cx="225" cy="190" rx="52" ry="155" transform="rotate(-10 225 190)" fill="url(#fur)"/>
       <ellipse cx="375" cy="190" rx="52" ry="155" transform="rotate(10 375 190)" fill="url(#fur)"/>
       <ellipse cx="300" cy="690" rx="165" ry="120" fill="url(#fur)"/>
       <ellipse cx="300" cy="420" rx="175" ry="155" fill="url(#fur)"/>
     </g>
     <ellipse cx="225" cy="200" rx="26" ry="120" transform="rotate(-10 225 200)" fill="#ffc2d1"/>
     <ellipse cx="375" cy="200" rx="26" ry="120" transform="rotate(10 375 200)" fill="#ffc2d1"/>
     ${K.eye(230, 415, 26, 32, '#3a2a40')}${K.eye(370, 415, 26, 32, '#3a2a40')}
     ${blush(180, 470)}${blush(420, 470)}
     <path d="M288 460 h24 q-2 12 -12 16 q-10 -4 -12 -16z" fill="#ff8fa3"/>
     <path d="M300 476 q-4 18 -26 14 M300 476 q4 18 26 14" stroke="#5a4050" stroke-width="4.5" fill="none" stroke-linecap="round"/>
     <rect x="287" y="490" width="12" height="16" rx="3" fill="#fff" stroke="#d6cfe0" stroke-width="2"/><rect x="301" y="490" width="12" height="16" rx="3" fill="#fff" stroke="#d6cfe0" stroke-width="2"/>
     <g transform="translate(390 620) rotate(-35)">
       <path d="M0 0 Q14 -6 24 0 L16 120 Q12 130 8 120Z" fill="#ff8c2b"/>
       <path d="M2 30 h10 M5 60 h10 M7 90 h8" stroke="#d9661a" stroke-width="3" stroke-linecap="round"/>
       <path d="M12 0 Q0 -40 -14 -46 Q8 -30 12 0 Q16 -44 36 -50 Q20 -30 12 0Z" fill="#4cb050"/>
     </g>
     <ellipse cx="235" cy="560" rx="34" ry="26" fill="#fff" stroke="#e6e0ee" stroke-width="3"/><ellipse cx="365" cy="560" rx="34" ry="26" fill="#fff" stroke="#e6e0ee" stroke-width="3"/><ellipse cx="300" cy="680" rx="80" ry="70" fill="#fbf8ff"/>
     ${['#ff8fb1', '#ffd166', '#a29bfe'].map((c, i) => `<g transform="translate(${80 + i * 220} ${740 - (i % 2) * 20})"><circle r="12" fill="${c}"/><circle r="5" fill="#fff8c4"/></g>`).join('')}`
  );

  /* 판다 */
  const panda = K.svg(
    K.lin('bg', [[0, '#dff5e3'], [1, '#b9e4c2']]) +
      K.rad('fur', [[0, '#ffffff'], [1, '#e9ecef']], 0.45, 0.35, 0.7) +
      K.shadow('sh', 10, 10, 0.18),
    `<rect width="600" height="800" fill="url(#bg)"/>
     ${[60, 130, 470, 545].map((x, i) => `<g><rect x="${x}" y="0" width="${i % 2 ? 22 : 28}" height="800" fill="${i % 2 ? '#7cc47f' : '#5aa85f'}"/>${[120, 300, 480, 660].map((y) => `<rect x="${x - 2}" y="${y + i * 30}" width="${(i % 2 ? 22 : 28) + 4}" height="8" rx="4" fill="#3f8a46"/>`).join('')}<path d="M${x + 14} ${200 + i * 40} q40 -30 70 -10 q-40 6 -70 10z" fill="#6fbf6f"/></g>`).join('')}
     <g filter="url(#sh)">
       <ellipse cx="300" cy="710" rx="190" ry="140" fill="#2b2b33"/>
       <ellipse cx="300" cy="730" rx="120" ry="110" fill="url(#fur)"/>
       <circle cx="160" cy="275" r="62" fill="#2b2b33"/><circle cx="440" cy="275" r="62" fill="#2b2b33"/>
       <ellipse cx="300" cy="420" rx="200" ry="175" fill="url(#fur)"/>
     </g>
     <ellipse cx="220" cy="420" rx="50" ry="64" transform="rotate(28 220 420)" fill="#2b2b33"/>
     <ellipse cx="380" cy="420" rx="50" ry="64" transform="rotate(-28 380 420)" fill="#2b2b33"/>
     <circle cx="228" cy="414" r="22" fill="#fff"/><circle cx="372" cy="414" r="22" fill="#fff"/>
     <circle cx="232" cy="418" r="13" fill="#1a1a22"/><circle cx="368" cy="418" r="13" fill="#1a1a22"/>
     <circle cx="227" cy="412" r="5" fill="#fff"/><circle cx="363" cy="412" r="5" fill="#fff"/>
     ${blush(165, 500)}${blush(435, 500)}
     <ellipse cx="300" cy="490" rx="26" ry="17" fill="#2b2b33"/>
     <path d="M300 506 v12 M300 518 q-16 18 -34 6 M300 518 q16 18 34 6" stroke="#2b2b33" stroke-width="5" fill="none" stroke-linecap="round"/>
     <g transform="translate(300 640) rotate(-20)"><rect x="-10" y="-70" width="20" height="140" rx="8" fill="#7cc47f"/><rect x="-12" y="-20" width="24" height="7" rx="3" fill="#3f8a46"/><path d="M8 -50 q40 -30 64 -8 q-36 0 -64 8z" fill="#5aa85f"/></g>
     <ellipse cx="230" cy="650" rx="46" ry="38" fill="#2b2b33"/><ellipse cx="370" cy="650" rx="46" ry="38" fill="#2b2b33"/>`
  );

  /* 다람쥐 */
  const squirrel = K.svg(
    K.lin('bg', [[0, '#fff1cf'], [1, '#ffd99a']]) +
      K.rad('fur', [[0, '#e6955a'], [1, '#bf6a33']], 0.4, 0.35, 0.75) +
      K.lin('tail', [[0, '#d27a3e'], [1, '#a5532a']], 0, 0, 1, 1) +
      K.shadow('sh', 10, 10, 0.18),
    `<rect width="600" height="800" fill="url(#bg)"/>
     ${K.roundTree(70, 260, 1.2, '#f2b134', '#d98d1c')}${K.roundTree(540, 230, 1.0, '#e86f3c', '#c84f2a')}
     <path d="M0 640 Q300 600 600 640 L600 800 L0 800Z" fill="#8bbf5a"/><path d="M0 700 Q300 670 600 700 L600 800 L0 800Z" fill="#76a948"/>
     <g filter="url(#sh)">
       <path d="M400 640 C560 620 600 430 520 330 C460 250 380 260 360 330 C350 380 420 380 430 340 C440 300 500 330 500 400 C500 500 430 560 360 580Z" fill="url(#tail)"/>
       <path d="M470 330 C500 350 510 420 480 480" stroke="#f2b07a" stroke-width="14" fill="none" stroke-linecap="round" opacity=".6"/>
       <ellipse cx="300" cy="560" rx="125" ry="135" fill="url(#fur)"/>
       <ellipse cx="290" cy="590" rx="72" ry="95" fill="#fff1dc"/>
       <path d="M190 260 L210 180 L250 250Z" fill="#bf6a33"/><path d="M360 250 L395 180 L410 262Z" fill="#bf6a33"/>
       <ellipse cx="300" cy="340" rx="125" ry="112" fill="url(#fur)"/>
     </g>
     <path d="M205 248 L214 205 L236 245Z" fill="#ffc2a0"/><path d="M372 244 L392 205 L398 250Z" fill="#ffc2a0"/>
     <ellipse cx="300" cy="380" rx="70" ry="52" fill="#fff1dc"/>
     ${K.eye(248, 330, 22, 28)}${K.eye(352, 330, 22, 28)}
     ${blush(210, 385)}${blush(390, 385)}
     <ellipse cx="300" cy="370" rx="13" ry="9" fill="#4a2a1e"/>
     <path d="M300 380 q-4 14 -20 12 M300 380 q4 14 20 12" stroke="#4a2a1e" stroke-width="4" fill="none" stroke-linecap="round"/>
     <g transform="translate(300 500)">
       <ellipse cx="0" cy="20" rx="44" ry="48" fill="#b5713a"/><ellipse cx="-12" cy="10" rx="10" ry="18" fill="#d9965b" opacity=".7"/>
       <path d="M-50 -6 Q0 -40 50 -6 Q50 10 0 8 Q-50 10 -50 -6Z" fill="#6b4226"/><line x1="0" y1="-26" x2="6" y2="-46" stroke="#6b4226" stroke-width="6" stroke-linecap="round"/>
       <path d="M-34 -2 l8 -8 M-14 -8 l8 -8 M8 -8 l8 -8 M28 -4 l8 -8" stroke="#8a5a36" stroke-width="3"/>
     </g>
     <ellipse cx="248" cy="500" rx="26" ry="20" fill="#bf6a33"/><ellipse cx="352" cy="500" rx="26" ry="20" fill="#bf6a33"/>
     <ellipse cx="240" cy="690" rx="40" ry="20" fill="#a5532a"/><ellipse cx="360" cy="690" rx="40" ry="20" fill="#a5532a"/>`
  );

  IT.Samples.register({ key: 'animals', name: '귀여운 동물', icon: '🐾' }, [
    { key: 'cat', name: '고양이', svg: cat },
    { key: 'dog', name: '강아지', svg: dog },
    { key: 'rabbit', name: '토끼', svg: rabbit },
    { key: 'panda', name: '판다', svg: panda },
    { key: 'squirrel', name: '다람쥐', svg: squirrel },
  ]);
})();
