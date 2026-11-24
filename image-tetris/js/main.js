/* IMAGE TETRIS – 앱 진입점 / 화면 전환 / 공통 상태 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const { $, $$ } = IT.UI;
  const U = IT.util;

  class App {
    async init() {
      this.settings = IT.Storage.loadSettings();
      this.config = IT.Storage.loadConfig();
      this.db = await IT.DB.open();
      this.library = new IT.ImageLibrary(this.db);
      this.collection = new IT.Collection(this.db);
      await Promise.all([this.library.init(), this.collection.init()]);
      this.sound = new IT.Sound(this.settings);
      this.session = null;
      this.screen = 'menu';
      this.libSel = null;
      this.libTab = 'user';
      this.sampleTheme = IT.Samples.themes[0].key;
      this._validateConfig();

      this.gameEls = {
        screen: $('#screen-game'), layout: $('#game-layout'), board: $('#board'), boardWrap: $('#board-wrap'), boardFrame: $('#board-frame'),
        overlay: $('#board-overlay'), holdCanvas: $('#hold-canvas'), nextCanvas: $('#next-canvas'), revealCanvas: $('#reveal-canvas'),
        revealBar: $('#reveal-bar'), revealPct: $('#reveal-pct'), revealLines: $('#reveal-lines'), revealProgress: $('#reveal-progress'),
        revealTitle: $('#reveal-title'), nextImage: $('#next-image'), palette: $('#game-palette'), mode: $('#hud-mode'),
        touch: $('#touch-controls'), footer: $('.game-footer'), stats: $('.p-stats'),
        hud: { score: $('#hud-score'), best: $('#hud-best'), level: $('#hud-level'), lines: $('#hud-lines'), combo: $('#hud-combo'), time: $('#hud-time') },
      };

      this._bindGlobal();
      this.initScreens();
      this.go('menu');
      if (!this.db.persistent) {
        this.toast('이 브라우저 환경에서는 저장소를 쓸 수 없어, 등록한 이미지는 창을 닫으면 사라집니다.', 'warn', 5000);
      }
      document.body.classList.add('ready');
    }

    _validateConfig() {
      const c = this.config, lib = this.library;
      c.mainImage = lib.resolve(c.mainImage);
      if (c.bgImage && !lib.exists(c.bgImage)) c.bgImage = null;
      if (c.blockImage && !lib.exists(c.blockImage)) c.blockImage = null;
      for (const t in c.pieceImages) if (!lib.exists(c.pieceImages[t])) delete c.pieceImages[t];
      if (!IT.Modes.MODES[c.mode]) c.mode = 'C';
      if (!IT.Modes.DIFFICULTIES[c.difficulty]) c.difficulty = 'easy';
      this.saveConfig();
    }
    saveConfig() { IT.Storage.saveConfig(this.config); }
    saveSettings() { IT.Storage.saveSettings(this.settings); this.sound.applySettings(); }

    _bindGlobal() {
      document.addEventListener('click', (e) => {
        const nav = e.target.closest('[data-nav]');
        if (nav) {
          e.preventDefault();
          this.sound.unlock();
          this.sound.play('click');
          this.go(nav.dataset.nav, { tab: nav.dataset.tab });
        }
      });
      const unlock = () => { this.sound.unlock(); };
      window.addEventListener('pointerdown', unlock, { passive: true });
      // 실제 터치가 감지되면 (자동 모드) 터치 버튼을 표시
      window.addEventListener('pointerdown', (e) => {
        if (e.pointerType === 'touch' && !this._sawTouch) {
          this._sawTouch = true;
          if (this.screen === 'game' && this.session) this.session.relayout();
        }
      }, { passive: true });
      window.addEventListener('keydown', unlock);
      const onResize = U.debounce(() => {
        if (this.screen === 'game' && this.session) this.session.relayout();
        if (this.screen === 'library') this.drawLibraryPreview();
      }, 120);
      window.addEventListener('resize', onResize);
      if (window.visualViewport) window.visualViewport.addEventListener('resize', onResize);
      window.addEventListener('orientationchange', onResize);
      document.addEventListener('visibilitychange', () => {
        if (document.hidden && this.session && this.session.state === 'playing') this.session.pause(true);
      });
      window.addEventListener('keydown', (e) => {
        if (this.screen === 'menu' && e.key === 'Enter' && !IT.UI.hasModal() && !/INPUT|SELECT|TEXTAREA|BUTTON/.test(e.target.tagName)) this.startGame();
      });
      // 더블탭 확대 방지 (게임 화면)
      let lastTouch = 0;
      document.addEventListener('touchend', (e) => {
        if (this.screen !== 'game' || (e.target.closest && e.target.closest('.modal'))) return;
        const now = Date.now();
        if (now - lastTouch < 350) e.preventDefault();
        lastTouch = now;
      }, { passive: false });
    }

    go(name, opts = {}) {
      if (this.screen === 'game' && name !== 'game' && this.session) {
        this.session.quit();
        this.session = null;
        IT.UI.closeAll();
        this.applyThemeFor(this.config.mainImage);
      }
      this.screen = name;
      $$('.screen').forEach((s) => s.classList.toggle('active', s.id === 'screen-' + name));
      document.body.dataset.screen = name;
      window.scrollTo(0, 0);
      if (name === 'menu') this.renderMenu();
      else if (name === 'library') { if (opts.tab) this.libTab = opts.tab; this.renderLibrary(); }
      else if (name === 'collection') this.renderCollection();
      else if (name === 'records') this.renderRecords();
      else if (name === 'settings') this.renderSettings();
    }

    /* ---------- 테마 ---------- */
    applyTheme(t) {
      const r = document.documentElement.style;
      r.setProperty('--bg', t.bg);
      r.setProperty('--bg2', t.bg2);
      r.setProperty('--panel', t.panel);
      r.setProperty('--board', t.board);
      r.setProperty('--accent', t.accent);
      r.setProperty('--accent2', t.accent2);
      r.setProperty('--border', t.border);
      r.setProperty('--accent-rgb', Object.values(U.hexToRgb(t.accent)).join(','));
      r.setProperty('--accent-ink', U.luminance(t.accent) > 0.45 ? '#14142a' : '#ffffff');
      const meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.setAttribute('content', t.bg);
      this.currentTheme = t;
    }
    async applyThemeFor(id) {
      try { this.applyTheme(await this.library.getTheme(this.library.resolve(id))); }
      catch (e) { this.applyTheme(IT.Palette.DEFAULT_THEME); }
    }

    /* ---------- 공통 ---------- */
    nextImageId(id) {
      const order = this.library.allIds();
      const i = order.indexOf(id);
      return order[(i + 1) % order.length];
    }
    bestScore(mode) {
      if (!this._bestCache || this._bestCacheT !== this._bestVersion) {
        this._bestCache = {};
        const r = IT.Storage.loadRecords();
        for (const m in r.best) this._bestCache[m] = r.best[m].length ? r.best[m][0].score : 0;
        this._bestCacheT = this._bestVersion;
      }
      return this._bestCache[mode] || 0;
    }
    invalidateBest() { this._bestVersion = (this._bestVersion || 0) + 1; }
    vibrate(p) { if (this.settings.vibration && navigator.vibrate) { try { navigator.vibrate(p); } catch (e) { /* 무시 */ } } }
    toast(msg, type, ms) { IT.UI.toast(msg, type, ms); }
    closeModal() { IT.UI.closeTop(); }

    /* ---------- 게임 시작 ---------- */
    async startGame() {
      if (this._starting) return;
      this._starting = true;
      this.sound.unlock();
      if (this.session) { this.session.destroy(); this.session = null; }
      IT.UI.closeAll();
      this.invalidateBest();
      this.go('game');
      const overlay = this.gameEls.overlay;
      overlay.innerHTML = '<div class="loading"><i></i>이미지 준비 중…</div>';
      const s = new IT.GameSession(this, { mode: this.config.mode, difficulty: this.config.difficulty, custom: this.config.custom });
      this.session = s;
      try {
        await s.prepare();
      } catch (e) {
        console.error(e);
        this.toast('게임을 준비하지 못했습니다: ' + (e && e.message), 'error', 4000);
        this._starting = false;
        this.session = null;
        this.go('menu');
        return;
      }
      this._starting = false;
      if (this.session !== s) return;
      overlay.innerHTML = '';
      s.start();
    }

    /** 화면 크기에 맞춰 게임판 칸 크기 계산 */
    layoutGame(session) {
      const els = this.gameEls, scr = els.screen;
      const vw = window.innerWidth, vh = (window.visualViewport && window.visualViewport.height) || window.innerHeight;
      const coarse = window.matchMedia('(pointer: coarse)').matches;
      const tc = this.settings.touchControls;
      const touch = tc === 'on' || (tc === 'auto' && (coarse || this._sawTouch));
      const landscape = vw > vh * 1.15;
      const portraitSmall = (!landscape && vw < 1000) || vw < 520;
      const landscapeTouch = touch && landscape && !portraitSmall;
      scr.classList.toggle('touch', touch);
      scr.classList.toggle('compact', portraitSmall);
      scr.classList.toggle('landscape-touch', landscapeTouch);
      const footerH = els.footer.offsetHeight;
      const touchH = touch && !landscapeTouch ? els.touch.offsetHeight : 0;
      let availW, availH;
      if (portraitSmall) {
        const statsH = els.stats.offsetHeight + 8;
        const sideW = vw < 400 ? 70 : 84;
        scr.style.setProperty('--side-w', sideW + 'px');
        availW = vw - sideW - 8 - 16 - 8;
        availH = vh - statsH - touchH - footerH - 16 - 8;
      } else {
        const roomy = vh >= 600;
        const tiny = vw < 760;
        const sl = landscapeTouch ? (roomy ? 160 : tiny ? 96 : 112) : vw < 1100 ? 170 : 200;
        const sr = landscapeTouch ? (roomy ? 190 : tiny ? 104 : 122) : vw < 1100 ? 190 : 240;
        scr.style.setProperty('--side-l', sl + 'px');
        scr.style.setProperty('--side-r', sr + 'px');
        if (landscapeTouch) {
          const tcw = U.clamp(Math.floor((vw - sl - sr - 200) / 2 - 20), tiny ? 110 : 130, 220);
          scr.style.setProperty('--tc-w', tcw + 'px');
          availW = vw - sl - sr - 2 * (tcw + 14) - 16 - 12;
          availH = vh - 12 - 12;
        } else {
          availW = vw - sl - sr - 32 - 24 - 8;
          availH = vh - footerH - touchH - 24 - 8;
        }
      }
      const cell = U.clamp(Math.floor(Math.min(availW / 10, availH / 20)), 10, 46);
      scr.style.setProperty('--cell', cell + 'px');
      scr.style.setProperty('--board-w', cell * 10 + 'px');
      scr.style.setProperty('--board-h', cell * 20 + 'px');
      if (session && session.renderer) session.renderer.layout(cell * 10, cell * 20);
    }

    /** 게임 화면 오른쪽 패널(모드별) 구성 */
    updateGamePanels(session) {
      const els = this.gameEls, mode = session.mode;
      const titles = { A: '배경 이미지', B: '블록 이미지', C: '이미지 완성', D: '테마 이미지', E: '미스터리 이미지' };
      els.revealTitle.textContent = titles[mode];
      els.revealProgress.classList.toggle('hidden', !(mode === 'C' || mode === 'E'));
      els.nextImage.classList.toggle('hidden', mode !== 'E');
      els.palette.innerHTML = '';
      if (mode === 'D' || mode === 'A' || mode === 'B') {
        const th = session.theme;
        Object.values(th.pieces).forEach((c) => { const i = document.createElement('i'); i.style.background = c; els.palette.appendChild(i); });
      }
      const info = IT.Modes.MODES[mode];
      const extra = mode === 'C' || mode === 'E' ? ` · 목표 ${session.diff.target}줄` : '';
      els.mode.innerHTML = `<span class="mode-icon">${info.icon}</span><div><b>${info.name}</b><small>${U.escapeHtml(session.diff.name)}${extra}</small><small class="img-name">${U.escapeHtml(session.currentName || '')}${session.stageNo > 1 ? ' · STAGE ' + session.stageNo : ''}</small></div>`;
    }
  }

  Object.assign(App.prototype, IT._screenProto || {});
  IT.App = App;

  window.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    IT.app = app;
    app.init().catch((e) => {
      console.error(e);
      document.body.insertAdjacentHTML('beforeend', `<div class="fatal">게임을 시작하지 못했습니다.<br><small>${U.escapeHtml(e && e.message || String(e))}</small></div>`);
    });
  });
})();
