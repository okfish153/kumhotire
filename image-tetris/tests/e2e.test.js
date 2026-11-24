/* IMAGE TETRIS – 브라우저 통합 테스트 (Playwright + Chromium)
 * 실행: node tests/e2e.test.js        (playwright 가 설치되어 있어야 함)
 * 스크린샷: tests/screenshots/ 에 저장
 */
'use strict';
const path = require('path');
const fs = require('fs');
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) {
  try { ({ chromium } = require(path.join(require('child_process').execSync('npm root -g').toString().trim(), 'playwright'))); }
  catch (e2) { console.error('playwright 를 찾을 수 없습니다. (npm i -D playwright)'); process.exit(2); }
}

const URL = 'file://' + path.join(__dirname, '..', 'index.html');
const SHOTS = path.join(__dirname, 'screenshots');
fs.mkdirSync(SHOTS, { recursive: true });

const results = [];
async function test(name, fn) {
  const t0 = Date.now();
  try { const note = await fn(); results.push({ name, ok: true, note, ms: Date.now() - t0 }); console.log(`  ✓ ${name}${note ? ' – ' + note : ''}`); }
  catch (e) { results.push({ name, ok: false, note: e.message, ms: Date.now() - t0 }); console.log(`  ✗ ${name}\n    ${e.stack || e}`); }
}
function assert(c, msg) { if (!c) throw new Error(msg || 'assertion failed'); }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function newPage(browser, opts = {}) {
  const ctx = opts.ctx || await browser.newContext(Object.assign({ viewport: { width: 1366, height: 860 } }, opts.context || {}));
  const page = await ctx.newPage();
  page._errors = [];
  page.on('pageerror', (e) => page._errors.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') page._errors.push('console: ' + m.text()); });
  await page.goto(URL);
  await page.waitForFunction(() => document.body.classList.contains('ready'), null, { timeout: 15000 });
  return { page, ctx };
}
async function startMode(page, mode, extra = {}) {
  await page.evaluate(([m, x]) => { Object.assign(IT.app.config, { mode: m }, x); IT.app.saveConfig(); IT.app.startGame(); }, [mode, extra]);
  await page.waitForFunction(() => IT.app.session && IT.app.session.state === 'playing', null, { timeout: 15000 });
}
/** 보드에 거의 찬 줄 n개를 만들고 I 블록 세로 드롭으로 n줄(최대 4) 제거 */
async function clearLines(page, n) {
  return page.evaluate((n) => {
    const s = IT.app.session, e = s.engine;
    const rows = [];
    for (let i = 0; i < n; i++) rows.push('#########.');
    rows.unshift('#.........'); // 남는 블록 (퍼펙트 클리어 방지)
    e.setBoardFromStrings(rows);
    e.piece = { type: 'I', x: 0, y: 0, r: 1, skin: s.skin };
    while (e.move(1));
    const before = e.lines;
    e.hardDrop();
    return e.lines - before;
  }, n);
}

/** 테스트용 이미지 파일 생성 (브라우저 캔버스로 인코딩) */
async function makeImages(page) {
  return page.evaluate(async () => {
    const mk = async (w, h, type, alpha, q) => {
      const c = document.createElement('canvas'); c.width = w; c.height = h;
      const x = c.getContext('2d');
      if (!alpha) { const g = x.createLinearGradient(0, 0, w, h); g.addColorStop(0, '#ff5577'); g.addColorStop(0.5, '#44aaff'); g.addColorStop(1, '#ffdd33'); x.fillStyle = g; x.fillRect(0, 0, w, h); }
      x.fillStyle = 'rgba(30,200,120,0.8)'; x.beginPath(); x.arc(w * 0.5, h * 0.5, Math.min(w, h) * 0.3, 0, 7); x.fill();
      x.fillStyle = '#000'; x.fillRect(0, 0, w * 0.1, h * 0.1); // 왼쪽 위 표시 (방향 확인용)
      const url = c.toDataURL(type, q);
      return url.split(',')[1];
    };
    return {
      big: await mk(4000, 3000, 'image/jpeg', false, 0.85),
      png: await mk(800, 600, 'image/png', true),
      webp: await mk(640, 960, 'image/webp', false, 0.9),
      jpg: await mk(1200, 800, 'image/jpeg', false, 0.9),
    };
  });
}

(async () => {
  const browser = await chromium.launch();
  console.log('\n[브라우저 통합 테스트] ' + URL + '\n');

  const { page, ctx } = await newPage(browser);
  // 데스크톱 테스트는 터치 버튼을 끔 (Playwright 의 fullPage 스크린샷이 pointer 에뮬레이션을 바꾸는 문제 회피)
  await page.evaluate(() => { IT.app.settings.touchControls = 'off'; IT.app.saveSettings(); });

  await test('첫 실행: 오류 없이 메인 화면 표시 + 샘플 6테마 26장', async () => {
    const info = await page.evaluate(() => ({ themes: IT.Samples.themes.length, items: IT.Samples.all().length, screen: IT.app.screen, persistent: IT.app.db.persistent }));
    assert(info.screen === 'menu', 'menu');
    assert(info.themes === 6 && info.items === 26, JSON.stringify(info));
    assert(page._errors.length === 0, page._errors.join('\n'));
    await page.screenshot({ path: path.join(SHOTS, '01-menu.png') });
    return `IndexedDB 영구 저장: ${info.persistent}`;
  });

  await test('샘플 이미지 26장 모두 래스터화·테마 추출 성공', async () => {
    const r = await page.evaluate(async () => {
      const out = [];
      for (const s of IT.Samples.all()) {
        const c = await IT.app.library.getBase(s.id);
        const th = await IT.app.library.getTheme(s.id);
        out.push([s.id, c.width, c.height, Object.keys(th.pieces).length]);
      }
      return out;
    });
    for (const [id, w, h, n] of r) assert(w > 100 && h > 100 && n === 7, id);
    return `${r.length}장`;
  });

  await test('기본 테트리스: 이동·회전·하드드롭·홀드·점수 (키보드)', async () => {
    await startMode(page, 'C', { difficulty: 'easy' });
    const before = await page.evaluate(() => { const e = IT.app.session.engine; return { x: e.piece.x, r: e.piece.r, type: e.piece.type }; });
    await page.keyboard.press('ArrowLeft');
    let st = await page.evaluate(() => IT.app.session.engine.piece.x);
    assert(st === before.x - 1, '왼쪽 이동');
    await page.keyboard.press('ArrowUp');
    st = await page.evaluate(() => IT.app.session.engine.piece.r);
    assert(st === (before.r + 1) % 4 || before.type === 'O', '시계 회전');
    await page.keyboard.press('KeyZ');
    st = await page.evaluate(() => IT.app.session.engine.piece.r);
    assert(st === before.r || before.type === 'O', '반시계 회전');
    await page.keyboard.press('KeyC');
    const held = await page.evaluate(() => IT.app.session.engine.holdType);
    assert(held === before.type, '홀드');
    await page.keyboard.press('Space');
    const sc = await page.evaluate(() => ({ score: IT.app.session.engine.score, pieces: IT.app.session.engine.stats.pieces }));
    assert(sc.pieces === 1 && sc.score > 0, '하드드롭 고정 + 점수');
    await page.keyboard.down('ArrowRight'); await sleep(450); await page.keyboard.up('ArrowRight');
    const x = await page.evaluate(() => IT.app.session.engine.piece.x);
    assert(x >= 6, 'DAS 자동 반복 이동 (x=' + x + ')');
    await page.screenshot({ path: path.join(SHOTS, '02-game-C.png') });
  });

  await test('일시정지(P) 중 진행 멈춤 → 재개', async () => {
    await page.keyboard.press('KeyP');
    await page.waitForSelector('.pause-modal');
    const y1 = await page.evaluate(() => IT.app.session.engine.piece.y);
    await sleep(1300);
    const y2 = await page.evaluate(() => IT.app.session.engine.piece.y);
    assert(y1 === y2 && (await page.evaluate(() => IT.app.session.state)) === 'paused', '일시정지');
    await page.screenshot({ path: path.join(SHOTS, '03-pause.png') });
    await page.click('.pause-modal .btn-primary');
    await page.waitForFunction(() => IT.app.session.state === 'playing');
  });

  await test('이미지 완성: 줄 제거 수와 진행률/공개 조각 일치 (1·2·3·4줄)', async () => {
    let total = 0;
    for (const n of [1, 2, 3, 4]) {
      const got = await clearLines(page, n);
      assert(got === n, `${n}줄 제거 (실제 ${got})`);
      total += n;
      const p = await page.evaluate(() => { const pr = IT.app.session.progress; return { lines: pr.lines, pct: pr.percent, rev: pr.revealedCount, total: pr.total, bar: document.getElementById('reveal-bar').style.width, txt: document.getElementById('reveal-pct').textContent }; });
      await sleep(60);
      assert(p.lines === total, 'lines');
      assert(Math.abs(p.pct - total * 10) < 1e-9, 'percent ' + p.pct);
      assert(p.rev === Math.floor(total * p.total / 10), 'revealed tiles');
    }
    const ui = await page.evaluate(() => [document.getElementById('reveal-pct').textContent, document.getElementById('reveal-lines').textContent]);
    assert(ui[0] === '100%' && ui[1] === '10 / 10줄', 'HUD ' + ui.join(','));
    return '10줄 → 100%';
  });

  await test('이미지 완성 → 축하 → 컬렉션 저장 → 다음 이미지 자동 진행', async () => {
    await page.waitForSelector('.stage-modal', { timeout: 6000 });
    await page.screenshot({ path: path.join(SHOTS, '04-stage-complete.png') });
    const before = await page.evaluate(() => ({ id: IT.app.session.currentId, col: IT.app.collection.count() }));
    assert(before.col >= 1, '컬렉션 저장');
    await page.click('.stage-modal .btn-primary');
    await page.waitForFunction(() => IT.app.session.state === 'playing' && IT.app.session.stageNo === 2, null, { timeout: 8000 });
    const after = await page.evaluate(() => ({ id: IT.app.session.currentId, pct: IT.app.session.progress.percent, board: IT.app.session.engine.board.flat().filter(Boolean).length }));
    assert(after.id !== before.id, '다음 이미지로 변경');
    assert(after.pct === 0 && after.board === 0, '새 스테이지 초기화');
    return `${before.id} → ${after.id}`;
  });

  await test('게임 오버 → 결과 화면 → 기록 저장', async () => {
    await page.evaluate(() => { const e = IT.app.session.engine; for (let i = 0; i < 100 && !e.over; i++) e.hardDrop(); });
    await page.waitForSelector('.result-modal', { timeout: 8000 });
    const txt = await page.textContent('.result-modal');
    assert(/최종 점수/.test(txt) && /제거한 줄/.test(txt) && /최고 콤보/.test(txt) && /플레이 시간/.test(txt) && /완성한 이미지 1장/.test(txt), '결과 항목');
    await page.screenshot({ path: path.join(SHOTS, '05-result.png') });
    const rec = await page.evaluate(() => IT.Storage.loadRecords());
    assert(rec.plays >= 1 && rec.best.C && rec.best.C.length >= 1 && rec.completed >= 1, '기록');
    await page.click('.result-modal .btn-primary'); // 다시 시작
    await page.waitForFunction(() => IT.app.session && IT.app.session.state === 'playing' && IT.app.session.engine.score === 0, null, { timeout: 10000 });
    return `최고 ${rec.best.C[0].score}점`;
  });

  await test('다중 이미지 업로드 (4000×3000 JPEG, 투명 PNG, WebP, JPG) + 오류 파일 처리', async () => {
    await page.evaluate(() => IT.app.go('library', { tab: 'user' }));
    const imgs = await makeImages(page);
    const files = [
      { name: 'huge-photo.jpg', mimeType: 'image/jpeg', buffer: Buffer.from(imgs.big, 'base64') },
      { name: 'alpha.png', mimeType: 'image/png', buffer: Buffer.from(imgs.png, 'base64') },
      { name: 'tall.webp', mimeType: 'image/webp', buffer: Buffer.from(imgs.webp, 'base64') },
      { name: 'landscape.jpeg', mimeType: 'image/jpeg', buffer: Buffer.from(imgs.jpg, 'base64') },
      { name: 'broken.jpg', mimeType: 'image/jpeg', buffer: Buffer.from('this is not an image at all') },
      { name: 'anim.gif', mimeType: 'image/gif', buffer: Buffer.from('GIF89a') },
      { name: 'note.txt', mimeType: 'text/plain', buffer: Buffer.from('hello') },
    ];
    const t0 = Date.now();
    await page.setInputFiles('#file-input', files);
    await page.waitForSelector('.modal .error-list', { timeout: 30000 });
    const ms = Date.now() - t0;
    const errText = await page.textContent('.error-list');
    assert(/broken\.jpg/.test(errText) && /anim\.gif/.test(errText) && /note\.txt/.test(errText), errText);
    await page.screenshot({ path: path.join(SHOTS, '06-upload-errors.png') });
    await page.click('.modal .btn-primary');
    const u = await page.evaluate(() => IT.app.library.user.map((x) => ({ n: x.name, w: x.width, h: x.height, ow: x.originalWidth, size: x.blob.size, type: x.blob.type })));
    assert(u.length === 4, '4장 등록: ' + JSON.stringify(u));
    const big = u.find((x) => x.n === 'huge-photo');
    assert(big.ow === 4000 && Math.max(big.w, big.h) <= 2048, '고해상도 최적화 ' + JSON.stringify(big));
    assert(u.find((x) => x.n === 'alpha').type === 'image/png', '투명 PNG 유지');
    const main = await page.evaluate(() => IT.app.config.mainImage);
    assert(main.startsWith('img_'), '첫 업로드 이미지가 대표 이미지로 지정');
    await page.screenshot({ path: path.join(SHOTS, '07-library.png'), fullPage: true });
    return `등록 4장 / 거부 3개, ${ms}ms, 4000×3000 → ${big.w}×${big.h}`;
  });

  await test('이미지 편집: 1:2 자르기·회전·밝기 저장 → 비율 유지 확인', async () => {
    const id = await page.evaluate(() => IT.app.library.user.find((x) => x.name === 'landscape').id);
    await page.evaluate((id) => { IT.app.libSel = id; IT.app.renderLibrary(); }, id);
    await page.click('#btn-edit');
    await page.waitForSelector('.editor-modal canvas');
    await page.click('.editor-modal .chip:has-text("게임판 1:2")');
    await page.click('.editor-modal button:has-text("오른쪽 90°")');
    await page.click('.editor-modal .chip:has-text("게임판 1:2")');
    const sliders = await page.$$('.editor-modal input[type=range]');
    await sliders[1].fill('130');
    await sliders[1].dispatchEvent('input');
    await sleep(300);
    await page.screenshot({ path: path.join(SHOTS, '08-editor.png') });
    await page.click('.editor-modal .btn-primary');
    await sleep(400);
    const r = await page.evaluate(async (id) => {
      const a = IT.app.library.getAdjust(id);
      const c = await IT.app.library.getAdjusted(id, 800);
      return { a, w: c.width, h: c.height };
    }, id);
    assert(r.a.rot === 1 && r.a.brightness === 130 && r.a.crop, JSON.stringify(r.a));
    assert(Math.abs(r.w / r.h - 0.5) < 0.02, '비율 1:2 → ' + r.w + 'x' + r.h);
    return `${r.w}×${r.h}`;
  });

  await test('데이터 저장·복구: 새로고침 후 이미지/편집값/설정/컬렉션 유지', async () => {
    const before = await page.evaluate(() => ({ n: IT.app.library.user.length, main: IT.app.config.mainImage, col: IT.app.collection.count(), adj: IT.app.library.user.map((u) => !!u.adjust).filter(Boolean).length }));
    await page.evaluate(() => { IT.app.settings.sfxVolume = 0.33; IT.app.saveSettings(); });
    await page.reload();
    await page.waitForFunction(() => document.body.classList.contains('ready'));
    const after = await page.evaluate(() => ({ n: IT.app.library.user.length, main: IT.app.config.mainImage, col: IT.app.collection.count(), adj: IT.app.library.user.map((u) => !!u.adjust).filter(Boolean).length, vol: IT.app.settings.sfxVolume, persistent: IT.app.db.persistent }));
    assert(after.persistent, 'IndexedDB 사용');
    assert(after.n === before.n && after.main === before.main && after.col === before.col && after.adj === before.adj && after.vol === 0.33, JSON.stringify({ before, after }));
    return `이미지 ${after.n}장, 컬렉션 ${after.col}장 복구`;
  });

  await test('이미지 블록: 7종 개별 지정 + 회전 시 텍스처도 90° 회전', async () => {
    const ok = await page.evaluate(async () => {
      const app = IT.app;
      const ids = app.library.user.map((u) => u.id);
      app.config.blockMode = 'perPiece';
      IT.Pieces.TYPES.forEach((t, i) => { app.config.pieceImages[t] = ids[i % ids.length]; });
      app.saveConfig();
      // 텍스처 회전 검증: 같은 셀(u,v)을 r=0 과 r=1 로 그려 픽셀 비교
      const tm = new IT.TextureManager();
      const c = document.createElement('canvas'); c.width = 300; c.height = 200;
      const x = c.getContext('2d');
      for (let i = 0; i < 300; i += 10) for (let j = 0; j < 200; j += 10) { x.fillStyle = `rgb(${i % 255},${j % 255},${(i * j) % 255})`; x.fillRect(i, j, 10, 10); }
      const skin = tm.buildPerPiece({ T: c, I: c, O: c, S: c, Z: c, J: c, L: c });
      const bp = new IT.Render.BlockPainter(tm);
      const px = 64;
      const a = bp.sprite('T', { u: 1, v: 1, r: 0, skin }, px).getContext('2d').getImageData(0, 0, px, px).data;
      const b = bp.sprite('T', { u: 1, v: 1, r: 1, skin }, px).getContext('2d').getImageData(0, 0, px, px).data;
      // 시계 방향 90°: b(x,y) = a(y, px-1-x)
      let diff = 0, n = 0;
      for (let y = 14; y < px - 14; y += 3) for (let xx = 14; xx < px - 14; xx += 3) {
        const ib = (y * px + xx) * 4, ia = ((px - 1 - xx) * px + y) * 4;
        diff += Math.abs(a[ia] - b[ib]) + Math.abs(a[ia + 1] - b[ib + 1]) + Math.abs(a[ia + 2] - b[ib + 2]); n++;
      }
      return diff / n / 3;
    });
    assert(ok < 6, '회전 텍스처 평균 오차 ' + ok.toFixed(2));
    await startMode(page, 'B');
    await page.evaluate(() => { const e = IT.app.session.engine; e.rotateCW(); });
    await sleep(200);
    const skin = await page.evaluate(() => IT.app.session.engine.piece.skin);
    assert(skin && skin.startsWith('per'), '7종 개별 스킨 적용');
    await page.screenshot({ path: path.join(SHOTS, '09-game-B-perpiece.png') });
    return '평균 픽셀 오차 ' + ok.toFixed(2);
  });

  await test('이미지 배경(A) · 테마(D) · 랜덤 챌린지(E) 모드 실행', async () => {
    await startMode(page, 'A');
    const a = await page.evaluate(() => !!IT.app.session.renderer.bg.image);
    await page.screenshot({ path: path.join(SHOTS, '10-game-A.png') });
    await startMode(page, 'D');
    const d = await page.evaluate(() => ({ pattern: IT.app.session.renderer.bg.pattern, colors: Object.values(IT.app.session.painter.colors) }));
    await page.screenshot({ path: path.join(SHOTS, '11-game-D.png') });
    await startMode(page, 'E', { difficulty: 'easy' });
    const first = await page.evaluate(() => IT.app.session.currentId);
    const hidden = await page.evaluate(() => !document.getElementById('next-image').classList.contains('hidden'));
    for (let i = 0; i < 3; i++) await clearLines(page, 4);
    await page.waitForSelector('.stage-modal', { timeout: 6000 });
    await page.click('.stage-modal .btn-primary');
    await page.waitForFunction(() => IT.app.session.stageNo === 2 && IT.app.session.state === 'playing', null, { timeout: 8000 });
    const second = await page.evaluate(() => IT.app.session.currentId);
    await page.screenshot({ path: path.join(SHOTS, '12-game-E.png') });
    assert(a, '배경 이미지');
    assert(d.pattern && new Set(d.colors).size === 7, '테마 7색');
    assert(hidden && first !== second, '미스터리 + 다른 이미지');
  });

  await test('장시간 플레이 성능 (자동 입력 30초 실시간)', async () => {
    await startMode(page, 'B');
    const r = await page.evaluate(() => new Promise((resolve) => {
      const s = IT.app.session;
      const frames = [];
      let last = performance.now(), games = 1, pieces = 0;
      const t0 = last;
      const acts = ['move', 'move', 'cw', 'ccw', 'hard', 'hold'];
      const iv = setInterval(() => {
        const e = s.engine;
        // 게임 오버 대신 높이 쌓이면 보드 정리 (결과 창이 뜨지 않게 계속 플레이)
        if (e.board.slice(0, 8).some((row) => row.some(Boolean))) { e.clearBoard(); games++; }
        const a = acts[Math.floor(Math.random() * acts.length)];
        if (a === 'move') e.move(Math.random() < 0.5 ? -1 : 1); else if (a === 'cw') e.rotateCW(); else if (a === 'ccw') e.rotateCCW();
        else if (a === 'hard') { e.hardDrop(); pieces++; } else e.hold();
      }, 40);
      const f = (ts) => {
        frames.push(ts - last); last = ts;
        if (ts - t0 < 30000) requestAnimationFrame(f);
        else {
          clearInterval(iv);
          frames.sort((a, b) => a - b);
          const avg = frames.reduce((a, b) => a + b, 0) / frames.length;
          resolve({ n: frames.length, avg, p95: frames[Math.floor(frames.length * 0.95)], max: frames[frames.length - 1], games, pieces, cache: s.painter.cache.size, particles: s.fx.particles.length, heap: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : -1 });
        }
      };
      requestAnimationFrame(f);
    }));
    assert(r.avg < 25, '평균 프레임 ' + r.avg.toFixed(1) + 'ms');
    assert(r.cache <= 3000 && r.particles <= 500, '캐시/파티클 상한');
    return `${r.n}프레임, 평균 ${r.avg.toFixed(1)}ms, p95 ${r.p95.toFixed(1)}ms, 보드 정리 ${r.games}회/${r.pieces}블록, 힙 ${r.heap}MB`;
  });

  await test('브라우저 크기 변경: 게임판이 화면 안에 맞게 재배치', async () => {
    const sizes = [[1366, 860], [1024, 700], [800, 1100], [1920, 1080], [600, 900]];
    const out = [];
    for (const [w, h] of sizes) {
      await page.setViewportSize({ width: w, height: h });
      await sleep(350);
      const r = await page.evaluate(() => {
        const b = document.getElementById('board').getBoundingClientRect();
        return { cell: IT.app.session.renderer.cell, bottom: b.bottom, right: b.right, left: b.left, top: b.top, sw: document.documentElement.scrollWidth, iw: innerWidth, ih: innerHeight, compact: document.getElementById('screen-game').classList.contains('compact') };
      });
      assert(r.left >= 0 && r.top >= 0 && r.right <= r.iw + 1 && r.bottom <= r.ih + 1 && r.sw <= r.iw + 1, `${w}x${h} 넘침 ${JSON.stringify(r)}`);
      out.push(`${w}×${h}:${r.cell}px${r.compact ? '(모바일 배치)' : ''}`);
    }
    await page.setViewportSize({ width: 1366, height: 860 });
    return out.join(', ');
  });

  await test('사운드: 효과음 20종 + 배경음 합성 (오류 없음, 켜기/끄기)', async () => {
    const r = await page.evaluate(async () => {
      const snd = IT.app.sound;
      const ok = snd.unlock();
      const names = ['move', 'rotate', 'softdrop', 'harddrop', 'lock', 'hold', 'clear', 'tetris', 'tspin', 'combo', 'levelup', 'reveal', 'complete', 'gameover', 'count', 'go', 'pause', 'click', 'error', 'upload'];
      for (const n of names) { snd._lastPlay = {}; snd.play(n, 2); }
      snd.startBgm();
      await new Promise((res) => setTimeout(res, 1200));
      const steps = snd._step;
      snd.stopBgm();
      IT.app.toggleSound('sfx'); const off = !IT.app.settings.sfxOn; IT.app.toggleSound('sfx');
      IT.app.toggleSound('bgm'); const boff = !IT.app.settings.bgmOn; IT.app.toggleSound('bgm');
      return { ok, state: snd.ctx && snd.ctx.state, steps, off, boff, n: names.length };
    });
    assert(r.ok && r.steps > 0 && r.off && r.boff, JSON.stringify(r));
    return `AudioContext ${r.state}, 배경음 ${r.steps}스텝 스케줄`;
  });

  await test('설정 화면 / 기록 화면 / 컬렉션 화면 렌더링', async () => {
    await page.evaluate(() => IT.app.go('settings'));
    await sleep(300);
    await page.screenshot({ path: path.join(SHOTS, '13-settings.png'), fullPage: true });
    await page.evaluate(() => IT.app.go('records'));
    await page.screenshot({ path: path.join(SHOTS, '14-records.png'), fullPage: true });
    await page.evaluate(() => IT.app.go('collection'));
    await sleep(200);
    const n = await page.$$eval('#collection-grid .thumb', (x) => x.length);
    await page.screenshot({ path: path.join(SHOTS, '15-collection.png'), fullPage: true });
    assert(n >= 2, '컬렉션 ' + n);
    await page.click('#collection-grid .thumb');
    await page.waitForSelector('.viewer-modal img');
    await sleep(300);
    await page.screenshot({ path: path.join(SHOTS, '16-viewer.png') });
    await page.keyboard.press('Escape');
    return `컬렉션 ${n}장`;
  });

  await test('이미지 삭제 시 지정 해제 + 기본 이미지로 초기화', async () => {
    await page.evaluate(() => IT.app.go('library', { tab: 'user' }));
    const main = await page.evaluate(() => IT.app.config.mainImage);
    await page.evaluate((id) => { IT.app.libSel = id; IT.app.renderLibrary(); }, main);
    await page.click('#btn-delete');
    await page.click('.modal .btn-danger');
    await sleep(400);
    const r = await page.evaluate((id) => ({ exists: IT.app.library.exists(id), main: IT.app.config.mainImage, pieces: Object.values(IT.app.config.pieceImages).includes(id) }), main);
    assert(!r.exists && r.main !== main && !r.pieces, JSON.stringify(r));
    await page.click('#btn-reset-default');
    await page.click('.modal .btn-primary');
    await sleep(400);
    const c = await page.evaluate(() => IT.app.config);
    assert(c.mainImage === 'sample:mountain-lake' && !c.bgImage && !Object.keys(c.pieceImages).length, '초기화');
  });

  assert(page._errors.length === 0, page._errors.join('\n'));
  await ctx.close();

  // ---------------- 모바일 ----------------
  const mctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const { page: mp } = await newPage(browser, { ctx: mctx });

  await test('모바일 메인/이미지 설정 화면 (390×844)', async () => {
    // 주의: Playwright 모바일 에뮬레이션에서 fullPage 스크린샷은 터치(pointer: coarse) 에뮬레이션을 해제하므로 사용하지 않음
    await mp.screenshot({ path: path.join(SHOTS, '20-mobile-menu.png') });
    await mp.evaluate(() => IT.app.go('library', { tab: 'samples' }));
    await sleep(500);
    await mp.screenshot({ path: path.join(SHOTS, '21-mobile-library.png') });
    const sw = await mp.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1);
    assert(sw, '가로 스크롤 없음');
  });

  await test('모바일 터치 버튼: 이동·회전·즉시 낙하·홀드 (중복 입력 없음)', async () => {
    await startMode(mp, 'C');
    const vis = await mp.evaluate(() => getComputedStyle(document.getElementById('touch-controls')).display !== 'none');
    assert(vis, '터치 버튼 표시');
    const x0 = await mp.evaluate(() => IT.app.session.engine.piece.x);
    await mp.tap('[data-act=left]');
    const x1 = await mp.evaluate(() => IT.app.session.engine.piece.x);
    assert(x1 === x0 - 1, `탭 1번 = 1칸 (${x0}→${x1})`);
    const r0 = await mp.evaluate(() => IT.app.session.engine.piece.r);
    await mp.tap('[data-act=cw]');
    const p1 = await mp.evaluate(() => ({ r: IT.app.session.engine.piece.r, t: IT.app.session.engine.piece.type }));
    assert(p1.t === 'O' || p1.r === (r0 + 1) % 4, '회전 1번');
    await mp.tap('[data-act=hold]');
    const held = await mp.evaluate(() => IT.app.session.engine.holdType);
    assert(held === p1.t, '홀드');
    const pc = await mp.evaluate(() => IT.app.session.engine.stats.pieces);
    await mp.tap('[data-act=hard]');
    const pc2 = await mp.evaluate(() => IT.app.session.engine.stats.pieces);
    assert(pc2 === pc + 1, '즉시 낙하 1번 = 블록 1개');
    await mp.screenshot({ path: path.join(SHOTS, '22-mobile-game.png') });
  });

  await test('모바일 스와이프: 좌우 드래그 이동 / 탭 회전 / 아래로 튕기기 즉시 낙하', async () => {
    const res = await mp.evaluate(async () => {
      const el = document.getElementById('board-wrap');
      const cell = IT.app.session.renderer.cell;
      const r = el.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      const ev = (type, x, y) => el.dispatchEvent(new PointerEvent(type, { pointerId: 7, pointerType: 'touch', clientX: x, clientY: y, bubbles: true, cancelable: true, isPrimary: true }));
      const wait = (ms) => new Promise((rs) => setTimeout(rs, ms));
      const e = IT.app.session.engine;
      const out = {};
      // 1) 오른쪽으로 2칸 드래그
      const x0 = e.piece.x;
      ev('pointerdown', cx, cy); for (let i = 1; i <= 10; i++) { ev('pointermove', cx + (cell * 2.0 * i) / 10, cy); await wait(10); } ev('pointerup', cx + cell * 2, cy);
      out.dx = e.piece.x - x0;
      await wait(50);
      // 2) 탭 → 회전
      const r0 = e.piece.r, t0 = e.piece.type;
      ev('pointerdown', cx, cy); await wait(60); ev('pointerup', cx, cy);
      out.rot = t0 === 'O' ? 1 : (e.piece.r - r0 + 4) % 4;
      await wait(50);
      // 3) 아래로 빠르게 튕기기 → 즉시 낙하
      const pcs = e.stats.pieces;
      ev('pointerdown', cx, cy - cell * 3);
      for (let i = 1; i <= 4; i++) { ev('pointermove', cx, cy - cell * 3 + cell * 1.5 * i); await wait(12); }
      ev('pointerup', cx, cy + cell * 3);
      out.hard = e.stats.pieces - pcs;
      return out;
    });
    assert(res.dx === 2, '드래그 2칸 → ' + res.dx);
    assert(res.rot === 1, '탭 회전 → ' + res.rot);
    assert(res.hard === 1, '튕기기 즉시 낙하 → ' + res.hard);
    return JSON.stringify(res);
  });

  await test('모바일 가로 화면 (844×390) 배치', async () => {
    await mp.setViewportSize({ width: 844, height: 390 });
    await sleep(400);
    const r = await mp.evaluate(() => { const b = document.getElementById('board').getBoundingClientRect(); return { bottom: b.bottom, ih: innerHeight, cls: document.getElementById('screen-game').className }; });
    await mp.screenshot({ path: path.join(SHOTS, '23-mobile-landscape.png') });
    assert(r.bottom <= r.ih + 1, JSON.stringify(r));
    return r.cls;
  });
  assert(mp._errors.length === 0, mp._errors.join('\n'));
  await mctx.close();

  // ---------------- 태블릿 ----------------
  const tctx = await browser.newContext({ viewport: { width: 820, height: 1180 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const { page: tp } = await newPage(browser, { ctx: tctx });
  await test('태블릿 세로 (820×1180) 게임 화면', async () => {
    await startMode(tp, 'A');
    await sleep(300);
    await tp.screenshot({ path: path.join(SHOTS, '24-tablet.png') });
    const r = await tp.evaluate(() => { const b = document.getElementById('board').getBoundingClientRect(); return { bottom: b.bottom, ih: innerHeight, cell: IT.app.session.renderer.cell }; });
    assert(r.bottom <= r.ih + 1 && r.cell >= 24, JSON.stringify(r));
    return 'cell ' + r.cell + 'px';
  });
  await tctx.close();

  await browser.close();
  const failed = results.filter((r) => !r.ok);
  console.log(`\n결과: ${results.length - failed.length} 통과, ${failed.length} 실패`);
  fs.writeFileSync(path.join(__dirname, 'e2e-results.json'), JSON.stringify(results, null, 2));
  process.exit(failed.length ? 1 : 0);
})();
