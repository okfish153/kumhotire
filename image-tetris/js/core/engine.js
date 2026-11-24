/* IMAGE TETRIS – 테트리스 게임 엔진 (순수 로직, DOM/이미지와 무관)
 *
 * - 10×20 보드 (+ 위쪽 숨김 2줄)
 * - 7-bag 무작위 생성, SRS 회전 + 월킥, 홀드, 고스트
 * - 락 딜레이(0.5초, 이동 리셋 최대 15회)
 * - 점수: 가이드라인 기준 라인/T-Spin/Back-to-Back/콤보/퍼펙트 클리어
 *
 * 이벤트: spawn, move, rotate, harddrop, lock, clear, levelup, hold, gameover
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const { TYPES, PIECES, kicksFor } = IT.Pieces;

  const MAX_LEVEL = 20;
  const LINE_POINTS = {
    none: [0, 100, 300, 500, 800],
    mini: [100, 200, 400, 400, 400],
    full: [400, 800, 1200, 1600, 1600],
  };
  const PERFECT_POINTS = [0, 800, 1200, 1800, 2000];

  class Engine extends IT.Emitter {
    constructor(opts = {}) {
      super();
      this.cols = 10;
      this.visibleRows = 20;
      this.hidden = 2;
      this.rows = this.visibleRows + this.hidden;
      this.rng = opts.rng || Math.random;
      this.startLevel = IT.util.clamp(opts.startLevel || 1, 1, MAX_LEVEL);
      this.lockDelay = opts.lockDelay != null ? opts.lockDelay : 500;
      this.maxLockResets = 15;
      this.softDropMs = opts.softDropMs || 30;
      this.skinFor = opts.skinFor || (() => null);
      this._sequence = opts.sequence ? opts.sequence.slice() : null;
      this.reset();
    }

    reset() {
      this.board = [];
      for (let y = 0; y < this.rows; y++) this.board.push(this._emptyRow());
      this.bag = [];
      this.queue = [];
      this.holdType = null;
      this.canHold = true;
      this.piece = null;
      this.score = 0;
      this.lines = 0;
      this.level = this.startLevel;
      this.combo = -1;
      this.maxCombo = 0;
      this.b2b = false;
      this.started = false;
      this.over = false;
      this.paused = false;
      this.elapsed = 0;
      this.gravityAcc = 0;
      this.lockTimer = 0;
      this.lockResets = 0;
      this.lowestY = 0;
      this.softDropping = false;
      this.lastRotate = false;
      this.lastKick = -1;
      this.stats = { pieces: 0, singles: 0, doubles: 0, triples: 0, tetrises: 0, tspins: 0, perfect: 0 };
    }

    _emptyRow() { return new Array(this.cols).fill(null); }

    start() {
      const seq = this._sequence;
      this.reset();
      this._sequence = seq;
      this.started = true;
      this._spawnNext();
    }

    /* ---------- 상태 조회 ---------- */
    active() { return this.started && !this.over && !this.paused && !!this.piece; }
    peek(n = 3) { this._fillQueue(); return this.queue.slice(0, n); }
    gravityMs(level = this.level) {
      return Math.pow(0.8 - (level - 1) * 0.007, level - 1) * 1000;
    }
    cellsOf(p = this.piece, x = p.x, y = p.y, r = p.r) {
      return PIECES[p.type].states[r].map((c) => ({ x: x + c.x, y: y + c.y, u: c.u, v: c.v }));
    }
    collides(p, x, y, r) {
      const st = PIECES[p.type].states[r];
      for (let i = 0; i < st.length; i++) {
        const bx = x + st[i].x, by = y + st[i].y;
        if (bx < 0 || bx >= this.cols || by >= this.rows) return true;
        if (by >= 0 && this.board[by][bx]) return true;
      }
      return false;
    }
    isOccupied(x, y) {
      if (x < 0 || x >= this.cols || y >= this.rows) return true;
      if (y < 0) return false;
      return !!this.board[y][x];
    }
    ghostY() {
      const p = this.piece;
      if (!p) return 0;
      let y = p.y;
      while (!this.collides(p, p.x, y + 1, p.r)) y++;
      return y;
    }
    grounded() { const p = this.piece; return !!p && this.collides(p, p.x, p.y + 1, p.r); }

    /* ---------- 블록 생성 ---------- */
    _fillQueue() {
      while (this.queue.length < 7) {
        if (this._sequence && this._sequence.length) { this.queue.push(this._sequence.shift()); continue; }
        if (!this.bag.length) this.bag = IT.util.shuffle(TYPES.slice(), this.rng);
        this.queue.push(this.bag.pop());
      }
    }
    _spawnNext() {
      this._fillQueue();
      const t = this.queue.shift();
      this._fillQueue();
      return this._spawn(t);
    }
    _spawn(type) {
      const p = { type, r: 0, x: type === 'O' ? 4 : 3, y: 0, skin: this.skinFor(type) };
      this.piece = p;
      this.gravityAcc = 0;
      this.lockTimer = 0;
      this.lockResets = 0;
      this.lastRotate = false;
      this.lastKick = -1;
      if (this.collides(p, p.x, p.y, p.r)) { this._gameOver('blockout'); return false; }
      if (!this.collides(p, p.x, p.y + 1, p.r)) p.y++;
      this.lowestY = p.y;
      this.emit('spawn', { type });
      return true;
    }

    /* ---------- 조작 ---------- */
    move(dx) {
      if (!this.active()) return false;
      const p = this.piece;
      if (this.collides(p, p.x + dx, p.y, p.r)) return false;
      p.x += dx;
      this.lastRotate = false;
      this._afterMove();
      this.emit('move', { dx });
      return true;
    }
    rotate(dir) {
      if (!this.active()) return false;
      const p = this.piece;
      const from = p.r, to = (p.r + dir + 4) % 4;
      const kicks = kicksFor(p.type, from, to);
      for (let i = 0; i < kicks.length; i++) {
        const [kx, ky] = kicks[i];
        if (!this.collides(p, p.x + kx, p.y + ky, to)) {
          p.x += kx; p.y += ky; p.r = to;
          this.lastRotate = true;
          this.lastKick = i;
          this._afterMove();
          this.emit('rotate', { dir, kick: i });
          return true;
        }
      }
      return false;
    }
    rotateCW() { return this.rotate(1); }
    rotateCCW() { return this.rotate(-1); }
    setSoftDrop(on) { this.softDropping = !!on; if (on) this.gravityAcc = Math.max(this.gravityAcc, this.softDropMs); }
    /** 한 칸 수동 하강 (터치 드래그용) */
    softDropStep() {
      if (!this.active()) return false;
      const p = this.piece;
      if (this.collides(p, p.x, p.y + 1, p.r)) return false;
      p.y++;
      this.score += 1;
      this.lastRotate = false;
      this._onFall();
      return true;
    }
    hardDrop() {
      if (!this.active()) return false;
      const p = this.piece;
      const fromY = p.y;
      while (!this.collides(p, p.x, p.y + 1, p.r)) p.y++;
      const dist = p.y - fromY;
      this.score += dist * 2;
      if (dist > 0) this.lastRotate = false;
      this.emit('harddrop', { distance: dist, fromY, type: p.type, cells: this.cellsOf(p) });
      this._lock();
      return true;
    }
    hold() {
      if (!this.active() || !this.canHold) return false;
      const cur = this.piece.type;
      this.canHold = false;
      const prev = this.holdType;
      this.holdType = cur;
      this.emit('hold', { type: cur });
      if (prev) this._spawn(prev);
      else this._spawnNext();
      return true;
    }
    setPaused(on) { if (this.started && !this.over) this.paused = !!on; }

    _afterMove() {
      const p = this.piece;
      if (p.y > this.lowestY) { this.lowestY = p.y; this.lockResets = 0; }
      if (this.lockResets < this.maxLockResets) {
        this.lockTimer = 0;
        if (this.grounded()) this.lockResets++;
      }
    }
    _onFall() {
      const p = this.piece;
      this.lockTimer = 0;
      if (p.y > this.lowestY) { this.lowestY = p.y; this.lockResets = 0; }
    }

    /* ---------- 시간 진행 ---------- */
    update(dt) {
      if (!this.active()) return;
      this.elapsed += dt;
      const p = this.piece;
      const g = this.gravityMs();
      const interval = this.softDropping ? Math.min(g, this.softDropMs) : g;
      this.gravityAcc += dt;
      let guard = 0;
      while (this.gravityAcc >= interval && guard++ < 50) {
        this.gravityAcc -= interval;
        if (!this.collides(p, p.x, p.y + 1, p.r)) {
          p.y++;
          this.lastRotate = false;
          if (this.softDropping) this.score += 1;
          this._onFall();
        } else { this.gravityAcc = 0; break; }
      }
      if (this.piece === p && this.grounded()) {
        this.lockTimer += dt;
        if (this.lockTimer >= this.lockDelay) this._lock();
      }
    }

    /* ---------- 고정 / 줄 제거 / 점수 ---------- */
    _detectTSpin() {
      const p = this.piece;
      if (!p || p.type !== 'T' || !this.lastRotate) return 'none';
      const cx = p.x + 1, cy = p.y + 1;
      const C = [
        this.isOccupied(cx - 1, cy - 1), // TL
        this.isOccupied(cx + 1, cy - 1), // TR
        this.isOccupied(cx + 1, cy + 1), // BR
        this.isOccupied(cx - 1, cy + 1), // BL
      ];
      const count = C.filter(Boolean).length;
      if (count < 3) return 'none';
      const FRONT = [[0, 1], [1, 2], [2, 3], [3, 0]][p.r];
      const front = C[FRONT[0]] && C[FRONT[1]];
      return front || this.lastKick === 4 ? 'full' : 'mini';
    }

    _lock() {
      const p = this.piece;
      if (!p) return;
      const tspin = this._detectTSpin();
      const cells = this.cellsOf(p);
      let allHidden = true;
      for (const c of cells) {
        if (c.y >= 0) this.board[c.y][c.x] = { t: p.type, u: c.u, v: c.v, r: p.r, skin: p.skin };
        if (c.y >= this.hidden) allHidden = false;
      }
      this.piece = null;
      this.stats.pieces++;
      this.emit('lock', { type: p.type, cells, tspin, r: p.r, skin: p.skin });

      const full = [];
      for (let y = 0; y < this.rows; y++) if (this.board[y].every(Boolean)) full.push(y);
      const n = full.length;
      const clearedRows = full.map((y) => ({ y: y - this.hidden, cells: this.board[y].slice() }));
      if (n) {
        const keep = this.board.filter((_, i) => full.indexOf(i) < 0);
        while (keep.length < this.rows) keep.unshift(this._emptyRow());
        this.board = keep;
      }
      const result = this._applyScore(n, tspin);
      if (n) {
        this.emit('clear', Object.assign({ lines: n, rows: clearedRows, tspin }, result));
      } else if (tspin !== 'none') {
        this.emit('clear', Object.assign({ lines: 0, rows: [], tspin }, result));
      }

      if (allHidden && n === 0) { this._gameOver('lockout'); return; }
      this.canHold = true;
      this._spawnNext();
    }

    _applyScore(n, tspin) {
      const lv = this.level;
      let base = LINE_POINTS[tspin][n] || 0;
      const difficult = n > 0 && (n === 4 || tspin !== 'none');
      let b2bApplied = false;
      if (n > 0) {
        if (difficult && this.b2b) { base *= 1.5; b2bApplied = true; }
        this.b2b = difficult;
        this.combo++;
        this.maxCombo = Math.max(this.maxCombo, this.combo);
      } else {
        this.combo = -1;
      }
      let points = base * lv;
      const comboPoints = n > 0 && this.combo > 0 ? 50 * this.combo * lv : 0;
      let perfect = false, perfectPoints = 0;
      if (n > 0 && this.board.every((row) => row.every((c) => !c))) {
        perfect = true;
        perfectPoints = PERFECT_POINTS[n] * lv;
        this.stats.perfect++;
      }
      const total = Math.floor(points + comboPoints + perfectPoints);
      this.score += total;

      if (n === 1) this.stats.singles++;
      else if (n === 2) this.stats.doubles++;
      else if (n === 3) this.stats.triples++;
      else if (n === 4) this.stats.tetrises++;
      if (tspin !== 'none') this.stats.tspins++;

      const prevLevel = this.level;
      this.lines += n;
      this.level = Math.min(MAX_LEVEL, this.startLevel + Math.floor(this.lines / 10));
      if (this.level > prevLevel) this.emit('levelup', { level: this.level });
      return { points: total, combo: this.combo, b2b: b2bApplied, perfect, level: this.level };
    }

    _gameOver(reason) {
      this.over = true;
      this.emit('gameover', { reason });
    }

    /** 새 스테이지: 보드만 비우고 점수/레벨은 유지 */
    clearBoard() {
      for (let y = 0; y < this.rows; y++) this.board[y] = this._emptyRow();
      if (this.piece && this.collides(this.piece, this.piece.x, this.piece.y, this.piece.r)) this.piece.y = 0;
    }

    /** 테스트용: 아래쪽부터 문자열 배열로 보드 구성 ('#' 또는 문자 = 채움, '.' = 빈칸) */
    setBoardFromStrings(lines) {
      for (let y = 0; y < this.rows; y++) this.board[y] = this._emptyRow();
      const off = this.rows - lines.length;
      lines.forEach((ln, i) => {
        for (let x = 0; x < this.cols; x++) {
          const ch = ln[x];
          if (ch && ch !== '.' && ch !== ' ') this.board[off + i][x] = { t: ch === '#' ? 'Z' : ch, u: 0, v: 0, r: 0, skin: null };
        }
      });
    }
  }

  Engine.MAX_LEVEL = MAX_LEVEL;
  Engine.LINE_POINTS = LINE_POINTS;
  IT.Engine = Engine;
})();
