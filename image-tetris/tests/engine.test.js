/* IMAGE TETRIS – 순수 로직 단위 테스트 (Node.js 로 실행: node tests/engine.test.js) */
'use strict';
const path = require('path');
const assert = require('assert');
const root = path.join(__dirname, '..', 'js');
['util.js', 'core/pieces.js', 'core/engine.js', 'core/modes.js', 'image/palette.js'].forEach((f) => require(path.join(root, f)));
const IT = globalThis.IT;
const { Engine, Pieces, Modes, Palette, util } = IT;

let passed = 0, failed = 0;
function test(name, fn) {
  try { fn(); passed++; console.log('  ✓ ' + name); }
  catch (e) { failed++; console.log('  ✗ ' + name + '\n    ' + (e && e.stack || e)); }
}
const mk = (opts = {}) => { const e = new Engine(Object.assign({ rng: util.seededRandom(1) }, opts)); return e; };
const cellsStr = (cells) => cells.map((c) => `${c.x},${c.y}`).sort().join(' ');

console.log('\n[블록 정의 / SRS]');
test('7종 블록, 각 4칸, 4방향', () => {
  assert.deepStrictEqual(Pieces.TYPES, ['I', 'O', 'T', 'S', 'Z', 'J', 'L']);
  for (const t of Pieces.TYPES) for (const st of Pieces.PIECES[t].states) assert.strictEqual(st.length, 4);
});
test('T 블록 회전 상태가 SRS 표준과 일치', () => {
  const st = Pieces.PIECES.T.states;
  assert.strictEqual(cellsStr(st[0]), cellsStr([{ x: 1, y: 0 }, { x: 0, y: 1 }, { x: 1, y: 1 }, { x: 2, y: 1 }]));
  assert.strictEqual(cellsStr(st[1]), cellsStr([{ x: 1, y: 0 }, { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 1, y: 2 }]));
  assert.strictEqual(cellsStr(st[2]), cellsStr([{ x: 0, y: 1 }, { x: 1, y: 1 }, { x: 2, y: 1 }, { x: 1, y: 2 }]));
  assert.strictEqual(cellsStr(st[3]), cellsStr([{ x: 1, y: 0 }, { x: 0, y: 1 }, { x: 1, y: 1 }, { x: 1, y: 2 }]));
});
test('I 블록 R 상태는 3번째 열 (x=2)', () => {
  assert.ok(Pieces.PIECES.I.states[1].every((c) => c.x === 2));
  assert.ok(Pieces.PIECES.I.states[3].every((c) => c.x === 1));
});
test('텍스처 좌표(u,v)는 회전해도 블록 셀마다 유지', () => {
  for (const t of Pieces.TYPES) {
    const P = Pieces.PIECES[t];
    const uv0 = P.states[0].map((c) => c.u + ',' + c.v).sort().join(' ');
    for (const st of P.states) assert.strictEqual(st.map((c) => c.u + ',' + c.v).sort().join(' '), uv0);
    for (const c of P.states[0]) { assert.ok(c.u < P.texW && c.v < P.texH); }
  }
});
test('월킥 테이블: 8방향 × 5개', () => {
  for (const tbl of [Pieces.KICKS.JLSTZ, Pieces.KICKS.I]) {
    assert.strictEqual(Object.keys(tbl).length, 8);
    for (const k in tbl) assert.strictEqual(tbl[k].length, 5);
  }
  // 화면좌표 변환 확인: JLSTZ 0>R 3번째 = (-1, -1) (위로 1칸)
  assert.deepStrictEqual(Array.from(Pieces.KICKS.JLSTZ['0>1'][2]), [-1, -1]);
});

console.log('\n[7-bag 생성]');
test('처음 7개 블록에 7종이 모두 1개씩', () => {
  for (let s = 1; s < 30; s++) {
    const e = new Engine({ rng: util.seededRandom(s) });
    e.start();
    const seen = [e.piece.type, ...e.peek(6)];
    assert.deepStrictEqual(seen.slice().sort(), Pieces.TYPES.slice().sort());
  }
});
test('70개 연속에서 각 블록 정확히 10번', () => {
  const e = mk(); e.start();
  const counts = {};
  for (let i = 0; i < 70; i++) { counts[e.piece.type] = (counts[e.piece.type] || 0) + 1; e.clearBoard(); e.hardDrop(); e.clearBoard(); }
  for (const t of Pieces.TYPES) assert.strictEqual(counts[t], 10, t + ' ' + counts[t]);
});

console.log('\n[이동 / 충돌 / 회전]');
test('스폰 위치와 첫 칸 하강', () => {
  const e = mk({ sequence: ['T'] }); e.start();
  assert.strictEqual(e.piece.type, 'T');
  assert.strictEqual(e.piece.x, 3);
  assert.strictEqual(e.piece.y, 1);
});
test('벽 충돌: 왼쪽 끝 이상으로 이동 불가', () => {
  const e = mk({ sequence: ['O'] }); e.start();
  let moves = 0; while (e.move(-1)) moves++;
  assert.strictEqual(moves, 4);
  assert.strictEqual(e.piece.x, 0);
  assert.strictEqual(e.move(-1), false);
  let r = 0; while (e.move(1)) r++;
  assert.strictEqual(e.piece.x, 8);
});
test('블록 충돌: 쌓인 블록을 통과하지 않음', () => {
  const e = mk({ sequence: ['O'] }); e.start();
  e.setBoardFromStrings(['#####.....']);
  while (e.move(-1)); // x=0
  const gy = e.ghostY();
  // 바닥 바로 위 행(=rows-2)에 O 의 아래 칸이 놓임 → piece.y = rows-3
  assert.strictEqual(gy, e.rows - 3);
});
test('I 블록 오른쪽 벽 회전 → 월킥 성공', () => {
  const e = mk({ sequence: ['I'] }); e.start();
  e.rotateCW(); // 세로
  while (e.move(1)); // 오른쪽 끝
  const ok = e.rotateCW();
  assert.ok(ok, '회전 성공');
  for (const c of e.cellsOf()) assert.ok(c.x >= 0 && c.x < 10);
});
test('T 블록 왼쪽 벽에 붙어 회전 시 킥 적용', () => {
  const e = mk({ sequence: ['T'] }); e.start();
  e.rotateCCW(); // L 상태
  while (e.move(-1));
  const before = e.piece.x;
  assert.ok(e.rotateCCW()); // L->2 : 기본 위치에서 왼쪽 벽 넘으면 킥
  for (const c of e.cellsOf()) assert.ok(c.x >= 0);
  assert.ok(e.piece.x >= before);
});
test('회전 4번이면 원래 상태', () => {
  const e = mk({ sequence: ['L'] }); e.start();
  const s = cellsStr(e.cellsOf());
  for (let i = 0; i < 4; i++) e.rotateCW();
  assert.strictEqual(cellsStr(e.cellsOf()), s);
  for (let i = 0; i < 4; i++) e.rotateCCW();
  assert.strictEqual(cellsStr(e.cellsOf()), s);
});

console.log('\n[낙하 / 고정]');
test('하드 드롭: 거리×2 점수, 즉시 고정', () => {
  const e = mk({ sequence: ['O', 'T'] }); e.start();
  const y0 = e.piece.y;
  e.hardDrop();
  assert.strictEqual(e.score, (e.rows - 2 - y0) * 2);
  assert.ok(e.board[e.rows - 1][4] && e.board[e.rows - 1][5]);
  assert.strictEqual(e.piece.type, 'T');
});
test('락 딜레이: 바닥 착지 후 0.5초 뒤 고정', () => {
  const e = mk({ sequence: ['O', 'I'] }); e.start();
  while (!e.grounded()) e.softDropStep();
  e.update(400);
  assert.strictEqual(e.piece.type, 'O');
  e.update(150);
  assert.strictEqual(e.piece.type, 'I');
});
test('이동 리셋은 최대 15회', () => {
  const e = mk({ sequence: ['O', 'I'] }); e.start();
  while (!e.grounded()) e.softDropStep();
  for (let i = 0; i < 30; i++) { e.update(400); if (e.piece.type !== 'O') break; e.move(i % 2 ? 1 : -1); }
  assert.strictEqual(e.piece.type, 'I', '무한 이동 방지로 결국 고정');
});
test('중력: 레벨 1은 약 1초에 1칸', () => {
  const e = mk({ sequence: ['T'] }); e.start();
  const y = e.piece.y;
  e.update(999); assert.strictEqual(e.piece.y, y);
  e.update(2); assert.strictEqual(e.piece.y, y + 1);
});
test('소프트 드롭: 칸당 1점', () => {
  const e = mk({ sequence: ['T'] }); e.start();
  e.setSoftDrop(true);
  e.update(300);
  assert.ok(e.piece.y > 5);
  assert.strictEqual(e.score, e.piece.y - 1);
});

console.log('\n[줄 제거 / 점수]');
test('싱글 100점 × 레벨', () => {
  const e = mk({ sequence: ['I', 'O'] }); e.start();
  e.setBoardFromStrings(['.........#', '....######']);
  // I 를 왼쪽 끝 바닥에 가로로
  while (e.move(-1));
  let cleared = null; e.on('clear', (d) => { cleared = d; });
  const before = e.score; e.hardDrop();
  assert.ok(cleared); assert.strictEqual(cleared.lines, 1);
  assert.strictEqual(cleared.points, 100);
  assert.strictEqual(e.lines, 1);
  assert.ok(e.score - before >= 100);
});
test('테트리스(4줄) 800점, Back-to-Back 1.5배', () => {
  const e = mk({ sequence: ['I', 'I', 'O'] }); e.start();
  const row = '#########.';
  e.setBoardFromStrings([row, row, row, row, row, row, row, row]);
  e.rotateCW(); while (e.move(1));
  const got = []; e.on('clear', (d) => got.push(d));
  e.hardDrop();
  e.rotateCW(); while (e.move(1));
  e.hardDrop();
  assert.strictEqual(got.length, 2);
  assert.strictEqual(got[0].lines, 4); assert.strictEqual(got[0].points, 800);
  assert.strictEqual(got[1].lines, 4); assert.ok(got[1].b2b);
  // 레벨은 4줄 뒤 1 → 두 번째도 레벨 1 (lines=4), b2b 1200 + 콤보 50
  assert.strictEqual(got[1].points, 1200 + 50 + 2000 * 1); // 마지막 제거는 보드가 비어 퍼펙트 클리어
  assert.ok(got[1].perfect);
});
test('콤보: 연속 줄 제거 시 50×콤보×레벨', () => {
  const e = mk({ sequence: ['I', 'I'] }); e.start();
  e.setBoardFromStrings(['#####.####', '#####.####', '#####.####', '#####.####', '..........', '....######', '....######'.replace(/######$/, '######')]);
  e.setBoardFromStrings(['####.#####', '####.#####', '####.#####', '####.#####', '####.#####', '####.#####', '####.#####', '####.#####']);
  // 세로 I 두 번 → 각각 4줄
  const got = []; e.on('clear', (d) => got.push(d));
  e.rotateCW(); e.move(-1); e.hardDrop();
  e.rotateCW(); e.move(-1); e.hardDrop();
  assert.strictEqual(got.length, 2);
  assert.strictEqual(got[1].combo, 1);
});
test('T-Spin Double 감지 (1200점)', () => {
  const e = mk({ sequence: ['T', 'O'] }); e.start();
  // 표준 TSD 구멍 (x=3 위쪽 돌출부 때문에 위에서 그냥 떨어뜨려 넣을 수 없음)
  e.setBoardFromStrings([
    '...#......',
    '#...######',
    '##.#######',
  ]);
  e.piece.r = 1; e.piece.x = 1; e.piece.y = e.rows - 3; // R 상태로 구멍 옆에 위치
  assert.ok(!e.collides(e.piece, e.piece.x, e.piece.y, e.piece.r), 'R 상태 위치 비어 있음');
  let got = null; e.on('clear', (d) => { got = d; });
  const ok = e.rotateCW(); // R -> 2 (킥 포함)
  assert.ok(ok, '회전 성공');
  e.hardDrop();
  assert.ok(got, '줄 제거 이벤트');
  assert.strictEqual(got.tspin, 'full');
  assert.strictEqual(got.lines, 2);
  assert.strictEqual(got.points, 1200);
});
test('회전 없이 넣으면 T-Spin 아님', () => {
  const e = mk({ sequence: ['T', 'O'] }); e.start();
  e.setBoardFromStrings(['###...####']);
  e.rotateCW(); e.rotateCW(); // 아래 방향 상태로 만든 후 이동 → lastRotate 해제
  e.move(-1); e.move(1);
  let got = null; e.on('clear', (d) => { got = d; });
  e.hardDrop();
  assert.ok(!got || got.tspin === 'none');
});
test('레벨 업: 10줄마다', () => {
  const e = mk(); e.start();
  let lv = 0; e.on('levelup', (d) => { lv = d.level; });
  e._applyScore(4, 'none'); e._applyScore(4, 'none'); assert.strictEqual(e.level, 1);
  e._applyScore(2, 'none'); assert.strictEqual(e.level, 2); assert.strictEqual(lv, 2);
});
test('시작 레벨 반영 (중급=3)', () => {
  const e = new Engine({ startLevel: 3 }); e.start();
  assert.strictEqual(e.level, 3);
  assert.ok(e.gravityMs() < e.gravityMs(1));
});

console.log('\n[홀드 / 일시정지 / 게임오버]');
test('홀드: 교체 후 같은 블록 차례에 재홀드 불가', () => {
  const e = mk({ sequence: ['T', 'S', 'Z'] }); e.start();
  assert.ok(e.hold()); assert.strictEqual(e.holdType, 'T'); assert.strictEqual(e.piece.type, 'S');
  assert.strictEqual(e.hold(), false);
  e.hardDrop();
  assert.ok(e.hold()); assert.strictEqual(e.holdType, 'Z'); assert.strictEqual(e.piece.type, 'T');
});
test('일시정지 중에는 진행/조작 안 됨', () => {
  const e = mk({ sequence: ['T'] }); e.start();
  e.setPaused(true);
  const y = e.piece.y; e.update(5000);
  assert.strictEqual(e.piece.y, y);
  assert.strictEqual(e.move(1), false);
  e.setPaused(false);
  assert.ok(e.move(1));
});
test('블록이 쌓여 스폰 불가 → 게임 오버', () => {
  const e = mk(); e.start();
  let over = null; e.on('gameover', (d) => { over = d; });
  for (let i = 0; i < 200 && !e.over; i++) e.hardDrop();
  assert.ok(e.over); assert.ok(over);
  assert.strictEqual(e.hardDrop(), false);
});
test('장시간 시뮬레이션 (10만 프레임) 안정성', () => {
  const rng = util.seededRandom(42);
  let games = 0, pieces = 0;
  const t0 = Date.now();
  let e = new Engine({ rng });
  e.start();
  for (let f = 0; f < 100000; f++) {
    const r = rng();
    if (r < 0.1) e.move(-1); else if (r < 0.2) e.move(1); else if (r < 0.25) e.rotateCW(); else if (r < 0.28) e.rotateCCW();
    else if (r < 0.29) e.hardDrop(); else if (r < 0.295) e.hold();
    e.update(16.7);
    if (e.over) { games++; pieces += e.stats.pieces; e = new Engine({ rng }); e.start(); }
    // 보드 무결성 확인
    if (f % 1000 === 0) { assert.strictEqual(e.board.length, e.rows); for (const row of e.board) assert.strictEqual(row.length, 10); }
  }
  console.log(`    (${games}게임, ${Date.now() - t0}ms)`);
});

console.log('\n[이미지 완성 모드 진행률]');
test('초급 10줄: 줄마다 진행률 10%, 10줄에서 100%·전체 공개', () => {
  const p = new Modes.RevealProgress(10, 3 / 4, util.seededRandom(3));
  assert.strictEqual(p.total >= 10, true);
  let revealed = 0;
  for (let i = 1; i <= 10; i++) {
    revealed += p.addLines(1).length;
    assert.ok(Math.abs(p.percent - i * 10) < 1e-9);
  }
  assert.ok(p.complete);
  assert.strictEqual(revealed, p.total);
});
test('2·3·4줄 동시 제거 → 해당 개수만큼 증가', () => {
  const p = new Modes.RevealProgress(20, 1, util.seededRandom(3));
  p.addLines(2); assert.strictEqual(p.percent, 10);
  p.addLines(3); assert.strictEqual(p.percent, 25);
  p.addLines(4); assert.strictEqual(p.percent, 45);
  assert.strictEqual(p.revealedCount, Math.floor(9 * p.total / 20));
});
test('목표 초과 줄은 100%에서 멈춤', () => {
  const p = new Modes.RevealProgress(10, 1);
  p.addLines(8); p.addLines(4);
  assert.strictEqual(p.percent, 100); assert.strictEqual(p.revealedCount, p.total);
  assert.deepStrictEqual(p.addLines(1), []);
});
test('격자: 20줄/정사각 → 조각 20개 근처, 사용자 목표(37) 처리', () => {
  for (const [t, a] of [[10, 0.75], [20, 1], [40, 0.75], [37, 1.5], [1, 1], [200, 0.5]]) {
    const g = Modes.revealGrid(t, a);
    assert.ok(g.cols * g.rows >= t && g.cols * g.rows <= Math.ceil(t * 1.5), `${t}: ${g.cols}x${g.rows}`);
  }
});
test('난이도: 초급10/중급20/고급40/사용자', () => {
  assert.strictEqual(Modes.resolveDifficulty('easy').target, 10);
  assert.strictEqual(Modes.resolveDifficulty('normal').target, 20);
  assert.strictEqual(Modes.resolveDifficulty('hard').target, 40);
  assert.strictEqual(Modes.resolveDifficulty('custom', { target: 33, startLevel: 4 }).target, 33);
  assert.strictEqual(Modes.resolveDifficulty('custom', { target: 9999 }).target, 200);
});

console.log('\n[랜덤 챌린지 이미지 선택]');
test('한 바퀴 동안 중복 없음, 연속 중복 없음', () => {
  const ids = ['a', 'b', 'c', 'd', 'e'];
  const pk = new Modes.ImagePicker(ids, util.seededRandom(9));
  const seq = []; for (let i = 0; i < 50; i++) seq.push(pk.next());
  for (let k = 0; k < 10; k++) assert.strictEqual(new Set(seq.slice(k * 5, k * 5 + 5)).size, 5);
  for (let i = 1; i < seq.length; i++) assert.notStrictEqual(seq[i], seq[i - 1]);
});
test('이미지 1장이면 계속 그 이미지', () => {
  const pk = new Modes.ImagePicker(['x']);
  assert.strictEqual(pk.next(), 'x'); assert.strictEqual(pk.next(), 'x');
});

console.log('\n[테마 색상]');
test('k-means 대표색 추출', () => {
  const px = [];
  for (let i = 0; i < 300; i++) px.push(250, 10, 10, 255);
  for (let i = 0; i < 200; i++) px.push(10, 10, 250, 255);
  for (let i = 0; i < 100; i++) px.push(10, 240, 10, 255);
  const pal = Palette.kmeansPalette(new Uint8Array(px), 3);
  assert.strictEqual(pal.length, 3);
  assert.ok(pal[0].r > 200 && pal[0].share > 0.45);
});
test('비슷한 색만 있는 이미지도 7색이 서로 구별됨 (ΔE ≥ 15)', () => {
  for (const pal of [['#2a5a8a', '#2c5e90', '#285585', '#305f92', '#244f7c'], ['#777777', '#808080', '#6a6a6a'], ['#ff0000']]) {
    const pc = Palette.buildPieceColors(pal);
    const cols = Object.values(pc);
    assert.strictEqual(cols.length, 7);
    for (let i = 0; i < 7; i++) for (let j = 0; j < i; j++) {
      const d = util.deltaE(cols[i], cols[j]);
      assert.ok(d >= 15, `${cols[i]} vs ${cols[j]} ΔE=${d.toFixed(1)}`);
    }
  }
});
test('테마: 어두운 배경 + 밝은 강조색', () => {
  const th = Palette.buildTheme(['#f2c14e', '#f78154', '#4d9078', '#b4436c', '#5fad56', '#1d3557']);
  assert.ok(util.luminance(th.bg) < 0.03);
  assert.ok(util.luminance(th.accent) > 0.15);
  assert.strictEqual(Object.keys(th.pieces).length, 7);
});

console.log(`\n결과: ${passed} 통과, ${failed} 실패\n`);
process.exit(failed ? 1 : 0);
