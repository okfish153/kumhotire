/* IMAGE TETRIS – 게임 세션 컨트롤러
 * 엔진(순수 로직) + 이미지/테마 + 렌더러 + 입력 + 사운드 + 모드 규칙을 연결합니다.
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const U = IT.util;
  const { TYPES } = IT.Pieces;
  const { MODES, resolveDifficulty, RevealProgress, ImagePicker } = IT.Modes;

  const CLEAR_NAMES = ['', '', 'DOUBLE', 'TRIPLE', 'TETRIS!'];
  const TSPIN_SUFFIX = ['', ' SINGLE', ' DOUBLE', ' TRIPLE'];

  class GameSession {
    constructor(app, opts) {
      this.app = app;
      this.mode = opts.mode;
      this.modeInfo = MODES[this.mode];
      this.diff = resolveDifficulty(opts.difficulty, opts.custom);
      this.settings = app.settings;
      this.cfg = app.config;
      this.lib = app.library;
      this.els = app.gameEls;
      this.sound = app.sound;
      this.state = 'loading'; // loading | countdown | playing | paused | stage | over | destroyed
      this.stageNo = 1;
      this.completed = []; // {id, name, thumb}
      this.raf = 0;
      this.last = 0;
      this._timers = [];
      this._hud = {};
      this._displayScore = 0;
      this._previewSig = '';
      this._revealDirty = true;
    }

    /* ============ 준비 ============ */
    async prepare() {
      const s = this.settings;
      this.textures = new IT.TextureManager();
      this.painter = new IT.Render.BlockPainter(this.textures);
      this.fx = new IT.Effects();
      this.fx.reduced = s.effects === 'reduced';
      this.renderer = new IT.Render.BoardRenderer(this.els.board, this.painter, this.fx);
      this.revealView = new IT.RevealView(this.els.revealCanvas);

      if (this.mode === 'E') {
        const pool = this._challengePool();
        this.picker = new ImagePicker(pool);
        this.currentId = this.picker.next();
      } else {
        this.currentId = this.lib.resolve(this.cfg.mainImage);
      }

      this.engine = new IT.Engine({
        startLevel: this.diff.startLevel,
        softDropMs: s.softDropSpeed,
        skinFor: (t) => (this.skin ? this.skin : null),
      });
      this._wireEngine();
      this.app.layoutGame(this);
      await this._loadStage(this.currentId);
      this._setupInput();
      this._updateHud(true);
    }

    _challengePool() {
      const pool = this.cfg.challengePool;
      const user = this.lib.user.map((u) => u.id);
      const samples = IT.Samples.all().map((x) => x.id);
      if (pool === 'user' && user.length) return user;
      if (pool === 'samples') return samples;
      return [...user, ...samples];
    }

    /** 스테이지(이미지) 불러오기: 테마, 배경, 블록 스킨, 공개 진행 */
    async _loadStage(id) {
      const lib = this.lib, cfg = this.cfg, s = this.settings;
      this.currentId = id;
      const rec = lib.get(id);
      this.currentName = rec ? rec.name : '이미지';
      const theme = await lib.getTheme(id);
      this.theme = theme;
      this.app.applyTheme(theme);
      const colors = s.pieceColors === 'classic' && this.mode !== 'D' ? IT.Pieces.CLASSIC_COLORS : theme.pieces;
      this.painter.setColors(colors);

      let bgImage = null, opacity = cfg.bgOpacity, dim = cfg.bgDim;
      this.skin = null;
      const bgId = lib.resolve(cfg.bgImage || id);
      if (this.mode === 'A') {
        bgImage = await lib.getAdjusted(bgId, 1400);
        opacity = cfg.bgOpacity * (lib.getAdjust(bgId).opacity / 100);
      } else if (this.mode === 'B') {
        if (cfg.blockMode === 'perPiece') {
          const imgs = {};
          for (const t of TYPES) imgs[t] = await lib.getAdjusted(lib.resolve(cfg.pieceImages[t] || cfg.blockImage || id), 600);
          this.skin = this.textures.buildPerPiece(imgs);
        } else {
          this.skin = this.textures.buildSlice(await lib.getAdjusted(lib.resolve(cfg.blockImage || id), 1200));
        }
        if (cfg.blockBg) {
          bgImage = await lib.getAdjusted(bgId, 1400);
          opacity = Math.min(cfg.bgOpacity, 0.45) * (lib.getAdjust(bgId).opacity / 100);
          dim = Math.max(cfg.bgDim, 0.5);
        }
      }
      // 현재 블록도 새 스킨 반영
      if (this.engine.piece) this.engine.piece.skin = this.skin;
      this.renderer.setBackground({ image: bgImage, opacity, dim, theme, grid: s.grid, pattern: this.mode === 'D' });

      // 오른쪽 이미지 영역
      const panelImg = await lib.getAdjusted(id, 900);
      this.stageImage = panelImg;
      this.revealView.setTheme(theme);
      if (this.mode === 'C' || this.mode === 'E') {
        this.progress = new RevealProgress(this.diff.target, panelImg.width / panelImg.height);
        this.revealView.set(panelImg, this.progress, 'reveal');
      } else {
        this.progress = null;
        this.revealView.set(panelImg, null, 'preview');
      }
      this._revealDirty = true;
      this._previewSig = '';
      this.app.updateGamePanels(this);
    }

    _wireEngine() {
      const e = this.engine, fx = this.fx, snd = this.sound;
      const hidden = e.hidden;
      const vis = (cells) => cells.map((c) => ({ x: c.x, y: c.y - hidden }));
      const colorOf = (cell) => (cell ? this.painter.color(cell.t) : '#fff');
      let lastHard = 0;
      e.on('move', () => snd.play('move'));
      e.on('rotate', () => snd.play('rotate'));
      e.on('hold', () => snd.play('hold'));
      e.on('harddrop', (d) => {
        lastHard = performance.now();
        snd.play('harddrop');
        fx.hardDrop(vis(d.cells), d.fromY - hidden, this.painter.color(d.type));
        this.app.vibrate(12);
      });
      e.on('lock', (d) => {
        if (performance.now() - lastHard > 30) snd.play('lock');
        fx.land(vis(d.cells), this.painter.color(d.type));
      });
      e.on('clear', (d) => this._onClear(d, colorOf));
      e.on('levelup', (d) => {
        snd.play('levelup');
        snd.setTempoForLevel(d.level);
        fx.text('LEVEL UP', 'Lv.' + d.level, '#7fffd4', true);
        this._flashHud('level');
      });
      e.on('gameover', () => this._onGameOver());
    }

    _onClear(d, colorOf) {
      const fx = this.fx, snd = this.sound;
      if (d.lines > 0) fx.lineClear(d.rows, colorOf, 10);
      // 문구
      let main = '', color = '#ffffff';
      if (d.tspin !== 'none') {
        main = 'T-SPIN' + (d.tspin === 'mini' ? ' MINI' : '') + TSPIN_SUFFIX[d.lines];
        color = '#d7a6ff';
        snd.play('tspin');
      } else if (d.lines === 4) { main = CLEAR_NAMES[4]; color = '#7fe7ff'; snd.play('tetris'); }
      else if (d.lines > 1) { main = CLEAR_NAMES[d.lines]; color = '#ffe27a'; }
      if (d.lines > 0 && d.tspin === 'none' && d.lines < 4) snd.play('clear', d.lines);
      const sub = (d.b2b ? 'BACK-TO-BACK  ' : '') + (d.points > 0 ? '+' + U.formatNum(d.points) : '');
      if (main) fx.text(main, sub, color, d.lines >= 4 || d.tspin === 'full');
      if (d.combo > 0) { fx.text(d.combo + ' COMBO', main ? '' : sub, '#ff9ecf'); snd.play('combo', d.combo); }
      if (d.perfect) { fx.text('PERFECT CLEAR!', '', '#ffd700', true); fx.confetti(10, 20, Object.values(this.painter.colors), 80); }
      if (d.lines > 0) this.app.vibrate(d.lines >= 4 ? [20, 30, 20] : 15);

      if (this.progress && d.lines > 0 && !this.progress.complete) {
        const fresh = this.progress.addLines(d.lines);
        if (fresh.length) { this.revealView.revealTiles(fresh); snd.play('reveal'); }
        this._revealDirty = true;
        if (this.progress.complete) this._stageComplete();
      }
      this._flashHud('lines');
    }

    _setupInput() {
      const e = this.engine;
      this.input = new IT.InputController({
        move: (d) => e.move(d),
        cw: () => e.rotateCW(),
        ccw: () => e.rotateCCW(),
        soft: (on) => e.setSoftDrop(on),
        softStep: () => { if (e.softDropStep()) this.sound.play('softdrop'); },
        hard: () => e.hardDrop(),
        hold: () => e.hold(),
        pause: () => this.togglePause(),
      }, this.settings);
      this.input.onAction = (act, src) => { if (src && src.startsWith('btn')) this.app.vibrate(6); };
      this.input.attachKeyboard(window);
      this.input.attachButtons(this.els.touch);
      this.input.attachSwipe(this.els.boardWrap, () => this.renderer.cell);
    }

    /* ============ 진행 ============ */
    start() {
      this.state = 'countdown';
      this.sound.setTempoForLevel(this.diff.startLevel);
      this._loop();
      this._countdown(() => {
        this.engine.start();
        this.state = 'playing';
        this.input.setEnabled(true);
        if (this.settings.bgmOn) this.sound.startBgm();
      });
    }

    _countdown(done) {
      const ov = this.els.overlay;
      const seq = ['3', '2', '1', 'GO!'];
      let i = 0;
      const step = () => {
        if (this.state === 'destroyed') return;
        if (i >= seq.length) { ov.innerHTML = ''; done(); return; }
        ov.innerHTML = `<div class="countdown ${seq[i] === 'GO!' ? 'go' : ''}">${seq[i]}</div>`;
        this.sound.play(seq[i] === 'GO!' ? 'go' : 'count');
        i++;
        this._later(step, i === seq.length ? 450 : 620);
      };
      step();
    }

    _later(fn, ms) { const t = setTimeout(fn, ms); this._timers.push(t); return t; }

    _loop() {
      this.last = performance.now();
      const frame = (ts) => {
        if (this.state === 'destroyed') return;
        let dt = ts - this.last;
        this.last = ts;
        if (dt < 0) dt = 0;
        let rem = Math.min(dt, 250);
        while (rem > 0) {
          const step = Math.min(rem, 16.7);
          if (this.state === 'playing') { this.input.update(step); this.engine.update(step); }
          rem -= step;
        }
        const fdt = Math.min(dt, 100);
        this.fx.update(fdt);
        // 일시정지·종료 후 화면 변화가 없으면 다시 그리지 않음 (배터리/성능)
        const fxIdle = !this.fx.particles.length && !this.fx.texts.length && !this.fx.strips.length && !this.fx.flashes.length;
        const idle = fxIdle && !this._needsDraw && (this.state === 'paused' || (this.state === 'over' && this.renderer.overT > 900));
        if (!idle) this.renderer.render(this.engine, fdt, { ghost: this.settings.ghost, smooth: this.settings.smoothMove });
        this._needsDraw = false;
        this._updatePreviews();
        if (this._revealDirty || this.revealView.animating) { this.revealView.render(fdt); this._revealDirty = false; }
        this._updateHud(false, fdt);
        this.raf = requestAnimationFrame(frame);
      };
      this.raf = requestAnimationFrame(frame);
    }

    _updatePreviews() {
      const e = this.engine;
      const next = e.started ? e.peek(3) : [];
      const sig = (e.holdType || '-') + (e.canHold ? 1 : 0) + next.join('') + '|' + this.renderer.cell + '|' + (this.skin || '');
      if (sig === this._previewSig) return;
      this._previewSig = sig;
      const skinFor = () => this.skin;
      IT.Render.drawPiecePreview(this.els.holdCanvas, e.holdType ? [e.holdType] : [], this.painter, skinFor, { dim: !e.canHold, maxCell: 26 });
      IT.Render.drawPiecePreview(this.els.nextCanvas, next, this.painter, skinFor, { maxCell: 24, shrink: true });
    }

    _updateHud(force, dt = 16) {
      const e = this.engine, h = this.els.hud;
      this._displayScore += (e.score - this._displayScore) * Math.min(1, dt / 90);
      if (Math.abs(e.score - this._displayScore) < 1) this._displayScore = e.score;
      const vals = {
        score: U.formatNum(this._displayScore),
        level: e.level,
        lines: e.lines,
        combo: e.combo > 0 ? e.combo : 0,
        time: U.formatTime(e.elapsed),
        best: U.formatNum(Math.max(this.app.bestScore(this.mode), e.score)),
      };
      for (const k in vals) {
        if (force || this._hud[k] !== vals[k]) { this._hud[k] = vals[k]; if (h[k]) h[k].textContent = vals[k]; }
      }
      if (this.progress) {
        const pct = Math.round(this.progress.percent);
        const key = pct + '|' + this.progress.lines;
        if (force || this._hud.reveal !== key) {
          this._hud.reveal = key;
          this.els.revealBar.style.width = this.progress.percent + '%';
          this.els.revealPct.textContent = pct + '%';
          this.els.revealLines.textContent = `${this.progress.lines} / ${this.progress.target}줄`;
        }
      }
    }

    _flashHud(key) {
      const el = this.els.hud[key];
      if (!el) return;
      const box = el.closest('.stat') || el;
      box.classList.remove('flash');
      void box.offsetWidth;
      box.classList.add('flash');
    }

    /* ============ 일시정지 ============ */
    togglePause() {
      if (this.state === 'playing') this.pause();
      else if (this.state === 'paused') this.resume();
    }
    pause(silent) {
      if (this.state !== 'playing') return;
      this.state = 'paused';
      this.engine.setPaused(true);
      this.input.releaseAll();
      this.sound.stopBgm();
      if (!silent) this.sound.play('pause');
      this.app.showPause(this);
    }
    resume() {
      if (this.state !== 'paused') return;
      this.state = 'countdown';
      this.app.closeModal();
      this._countdownShort(() => {
        if (this.state !== 'countdown') return;
        this.state = 'playing';
        this.engine.setPaused(false);
        this.input.setEnabled(true);
        if (this.settings.bgmOn) this.sound.startBgm();
      });
    }
    _countdownShort(done) {
      const ov = this.els.overlay;
      ov.innerHTML = '<div class="countdown small">READY</div>';
      this._later(() => { ov.innerHTML = ''; done(); }, 500);
    }

    /* ============ 이미지 완성 ============ */
    async _stageComplete() {
      this.state = 'stage';
      this.engine.setPaused(true);
      this.input.setEnabled(false);
      this.sound.stopBgm();
      this._later(() => this.sound.play('complete'), 250);
      this.revealView.celebrate();
      this.fx.confetti(10, 20, [...Object.values(this.painter.colors), '#ffffff'], 180);
      this.fx.text('이미지 완성!', this.currentName, '#ffe27a', true);
      const entry = { id: this.currentId, name: this.currentName, thumb: null };
      this.completed.push(entry);
      try {
        const rec = await this.app.collection.add({
          imageId: this.currentId, name: this.currentName, canvas: this.stageImage,
          mode: this.mode, score: this.engine.score, lines: this.engine.lines, difficulty: this.diff.name,
        });
        entry.thumb = rec.thumb;
        entry.colId = rec.id;
      } catch (err) {
        console.warn('컬렉션 저장 실패', err);
        entry.thumb = this.stageImage ? IT.ImageProc.thumbDataURL(this.stageImage, 200) : null;
      }
      this._later(() => { if (this.state === 'stage') this.app.showStageComplete(this, entry); }, 1500);
    }

    nextImageId() {
      if (this.mode === 'E') return this.picker.next();
      return this.app.nextImageId(this.currentId);
    }

    async nextStage() {
      if (this.state !== 'stage') return;
      this.app.closeModal();
      const id = this.nextImageId();
      this.state = 'loading';
      try { await this._loadStage(id); } catch (e) {
        this.app.toast('다음 이미지를 불러오지 못해 기본 이미지로 진행합니다: ' + e.message, 'error');
        try { await this._loadStage(IT.Samples.DEFAULT_ID); } catch (e2) { console.error(e2); }
      }
      if (this.state === 'destroyed') return;
      this.stageNo++;
      this.fx.clear();
      this.engine.clearBoard();
      if (this.engine.piece) { const t = this.engine.piece.type; this.engine._spawn(t); }
      this.engine.canHold = true;
      this.renderer.resetVisual();
      this._previewSig = '';
      this.state = 'countdown';
      this.els.overlay.innerHTML = `<div class="countdown small">STAGE ${this.stageNo}</div>`;
      this._later(() => {
        this.els.overlay.innerHTML = '';
        if (this.state !== 'countdown') return;
        this.state = 'playing';
        this.engine.setPaused(false);
        this.input.setEnabled(true);
        if (this.settings.bgmOn) this.sound.startBgm();
      }, 1100);
    }

    /* ============ 종료 ============ */
    _onGameOver() {
      this.state = 'over';
      this.input.setEnabled(false);
      this.sound.stopBgm();
      this.sound.play('gameover');
      this.renderer.startGameOver();
      this.app.vibrate([40, 60, 40]);
      this._later(() => this.finish(), 1300);
    }

    /** 결과 집계 후 결과 화면 */
    finish() {
      if (this._finished) return;
      this._finished = true;
      const e = this.engine;
      const result = {
        mode: this.mode,
        modeName: this.modeInfo.title,
        score: e.score,
        lines: e.lines,
        level: e.level,
        maxCombo: Math.max(0, e.maxCombo),
        time: e.elapsed,
        difficulty: this.diff.name,
        completed: this.completed.length,
        images: this.completed.slice(),
        stats: Object.assign({}, e.stats),
      };
      const rec = IT.Storage.addResult(result);
      result.newBest = rec.newBest;
      result.prevBest = rec.prevBest;
      result.rank = rec.rank;
      this.state = 'over';
      this.app.showResults(this, result);
    }

    /** 게임 도중 그만두기 (기록은 남김) */
    quit() {
      if (this.engine.started && !this._finished && (this.engine.score > 0 || this.engine.lines > 0)) {
        const e = this.engine;
        IT.Storage.addResult({ mode: this.mode, score: e.score, lines: e.lines, level: e.level, time: e.elapsed, difficulty: this.diff.name, completed: this.completed.length });
        this._finished = true;
      }
      this.destroy();
    }

    destroy() {
      this.state = 'destroyed';
      cancelAnimationFrame(this.raf);
      this._timers.forEach(clearTimeout);
      if (this.input) this.input.destroy();
      this.sound.stopBgm();
      if (this.els.overlay) this.els.overlay.innerHTML = '';
    }

    relayout() {
      this.app.layoutGame(this);
      this._previewSig = '';
      this._revealDirty = true;
      this._needsDraw = true;
      this.renderer.vis = null;
    }
  }

  IT.GameSession = GameSession;
})();
