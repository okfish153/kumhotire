/* IMAGE TETRIS – 테트로미노 정의 + SRS 회전/월킥 테이블
 *
 * 각 블록은 '스폰 방향'의 셀 좌표와, 이미지 텍스처를 위한 (u, v) 좌표를 가집니다.
 * 회전 상태 r 의 셀은 스폰 셀을 n×n 상자 안에서 시계 방향으로 r번 회전해 얻습니다.
 * (u, v) 는 회전해도 바뀌지 않으므로, 텍스처를 r×90° 회전해 그리면
 * 이미지가 블록과 함께 자연스럽게 회전합니다.
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});

  const TYPES = ['I', 'O', 'T', 'S', 'Z', 'J', 'L'];

  // 화면 좌표계 (y 는 아래로 증가)
  const SPAWN = {
    I: { n: 4, cells: [[0, 1], [1, 1], [2, 1], [3, 1]] },
    O: { n: 2, cells: [[0, 0], [1, 0], [0, 1], [1, 1]] },
    T: { n: 3, cells: [[1, 0], [0, 1], [1, 1], [2, 1]] },
    S: { n: 3, cells: [[1, 0], [2, 0], [0, 1], [1, 1]] },
    Z: { n: 3, cells: [[0, 0], [1, 0], [1, 1], [2, 1]] },
    J: { n: 3, cells: [[0, 0], [0, 1], [1, 1], [2, 1]] },
    L: { n: 3, cells: [[2, 0], [0, 1], [1, 1], [2, 1]] },
  };

  const CLASSIC_COLORS = {
    I: '#35c9f0', O: '#f7d31e', T: '#b155d6', S: '#4cc463', Z: '#f0444f', J: '#4d72e6', L: '#f5922a',
  };

  const PIECES = {};
  for (const t of TYPES) {
    const { n, cells } = SPAWN[t];
    const xs = cells.map((c) => c[0]), ys = cells.map((c) => c[1]);
    const minX = Math.min(...xs), minY = Math.min(...ys);
    const texW = Math.max(...xs) - minX + 1, texH = Math.max(...ys) - minY + 1;
    const states = [];
    let cur = cells.map(([x, y]) => ({ x, y, u: x - minX, v: y - minY }));
    for (let r = 0; r < 4; r++) {
      states.push(Object.freeze(cur.map((c) => Object.freeze(c))));
      cur = cur.map((c) => ({ x: n - 1 - c.y, y: c.x, u: c.u, v: c.v }));
    }
    PIECES[t] = Object.freeze({ type: t, n, texW, texH, states: Object.freeze(states) });
  }

  // SRS 월킥 데이터 (표준 표기: y 는 위로 증가) → 화면 좌표로 변환 (y 부호 반전)
  const RAW_JLSTZ = {
    '0>1': [[0, 0], [-1, 0], [-1, 1], [0, -2], [-1, -2]],
    '1>0': [[0, 0], [1, 0], [1, -1], [0, 2], [1, 2]],
    '1>2': [[0, 0], [1, 0], [1, -1], [0, 2], [1, 2]],
    '2>1': [[0, 0], [-1, 0], [-1, 1], [0, -2], [-1, -2]],
    '2>3': [[0, 0], [1, 0], [1, 1], [0, -2], [1, -2]],
    '3>2': [[0, 0], [-1, 0], [-1, -1], [0, 2], [-1, 2]],
    '3>0': [[0, 0], [-1, 0], [-1, -1], [0, 2], [-1, 2]],
    '0>3': [[0, 0], [1, 0], [1, 1], [0, -2], [1, -2]],
  };
  const RAW_I = {
    '0>1': [[0, 0], [-2, 0], [1, 0], [-2, -1], [1, 2]],
    '1>0': [[0, 0], [2, 0], [-1, 0], [2, 1], [-1, -2]],
    '1>2': [[0, 0], [-1, 0], [2, 0], [-1, 2], [2, -1]],
    '2>1': [[0, 0], [1, 0], [-2, 0], [1, -2], [-2, 1]],
    '2>3': [[0, 0], [2, 0], [-1, 0], [2, 1], [-1, -2]],
    '3>2': [[0, 0], [-2, 0], [1, 0], [-2, -1], [1, 2]],
    '3>0': [[0, 0], [1, 0], [-2, 0], [1, -2], [-2, 1]],
    '0>3': [[0, 0], [-1, 0], [2, 0], [-1, 2], [2, -1]],
  };
  const toScreen = (tbl) => {
    const out = {};
    for (const k in tbl) out[k] = Object.freeze(tbl[k].map(([x, y]) => Object.freeze([x, -y || 0])));
    return Object.freeze(out);
  };
  const KICKS = { JLSTZ: toScreen(RAW_JLSTZ), I: toScreen(RAW_I), O: Object.freeze({}) };

  function kicksFor(type, from, to) {
    if (type === 'O') return [[0, 0]];
    const tbl = type === 'I' ? KICKS.I : KICKS.JLSTZ;
    return tbl[from + '>' + to];
  }

  IT.Pieces = { TYPES, PIECES, KICKS, CLASSIC_COLORS, kicksFor, STATE_NAMES: ['0', 'R', '2', 'L'] };
})();
