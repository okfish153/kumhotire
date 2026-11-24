/* IMAGE TETRIS – 입력 처리
 * - 키보드 (DAS/ARR 자동 반복)
 * - 터치 버튼 (멀티터치, 누르고 있으면 반복)
 * - 게임판 스와이프 (좌우 드래그=이동, 아래 드래그=빠른 낙하, 아래로 튕기기=즉시 낙하, 위로 튕기기=홀드, 탭=회전)
 * 터치 버튼과 스와이프는 서로 다른 요소에서만 동작하고, Pointer Events 만 사용하므로 중복 입력이 없습니다.
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});

  const KEYMAP = {
    ArrowLeft: 'left', ArrowRight: 'right', ArrowDown: 'soft',
    ArrowUp: 'cw', KeyX: 'cw', KeyZ: 'ccw', ControlLeft: 'ccw', ControlRight: 'ccw',
    Space: 'hard', KeyC: 'hold', ShiftLeft: 'hold', ShiftRight: 'hold',
    KeyP: 'pause', Escape: 'pause', F1: 'pause',
  };

  class InputController {
    /** actions: { move(dir)→bool, cw(), ccw(), soft(on), softStep(), hard(), hold(), pause() } */
    constructor(actions, settings) {
      this.a = actions;
      this.settings = settings;
      this.enabled = false;
      this.dirStack = [];
      this.dasT = 0; this.arrT = 0;
      this.softKeys = new Set();
      this._detach = [];
      this.onAction = null; // 진동 등 부가 피드백용
    }

    get das() { return this.settings.das; }
    get arr() { return this.settings.arr; }

    setEnabled(on) { this.enabled = on; if (!on) this.releaseAll(); }

    releaseAll() {
      this.dirStack = [];
      if (this.softKeys.size) { this.softKeys.clear(); this.a.soft(false); }
    }

    _press(act, src) {
      if (!this.enabled && act !== 'pause') return;
      if (this.onAction) this.onAction(act, src);
      switch (act) {
        case 'left': case 'right': {
          const d = act === 'left' ? -1 : 1;
          this.dirStack = this.dirStack.filter((x) => x.src !== src || x.d !== d);
          this.dirStack.push({ d, src });
          this.dasT = 0; this.arrT = 0;
          this.a.move(d);
          break;
        }
        case 'soft': this.softKeys.add(src); this.a.soft(true); break;
        case 'cw': this.a.cw(); break;
        case 'ccw': this.a.ccw(); break;
        case 'hard': this.a.hard(); break;
        case 'hold': this.a.hold(); break;
        case 'pause': this.a.pause(); break;
        default: break;
      }
    }
    _release(act, src) {
      if (act === 'left' || act === 'right') {
        const d = act === 'left' ? -1 : 1;
        const top = this.dirStack[this.dirStack.length - 1];
        this.dirStack = this.dirStack.filter((x) => !(x.src === src && x.d === d));
        const nt = this.dirStack[this.dirStack.length - 1];
        if (top && (!nt || nt.d !== top.d)) { this.dasT = 0; this.arrT = 0; }
      } else if (act === 'soft') {
        this.softKeys.delete(src);
        if (!this.softKeys.size) this.a.soft(false);
      }
    }

    /** 매 프레임 호출: DAS/ARR 반복 이동 */
    update(dt) {
      if (!this.enabled || !this.dirStack.length) return;
      const d = this.dirStack[this.dirStack.length - 1].d;
      this.dasT += dt;
      if (this.dasT < this.das) return;
      if (this.arr <= 0) { let g = 0; while (this.a.move(d) && g++ < 10); return; }
      this.arrT += dt;
      let g = 0;
      while (this.arrT >= this.arr && g++ < 10) { this.arrT -= this.arr; if (!this.a.move(d)) { this.arrT = 0; break; } }
    }

    /* ---------- 키보드 ---------- */
    attachKeyboard(target = window) {
      const down = (e) => {
        const act = KEYMAP[e.code];
        if (!act) return;
        const t = e.target;
        if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT')) return;
        e.preventDefault();
        if (e.repeat) return; // 자동 반복은 직접 처리
        this._press(act, 'key:' + e.code);
      };
      const up = (e) => {
        const act = KEYMAP[e.code];
        if (!act) return;
        this._release(act, 'key:' + e.code);
      };
      const blur = () => this.releaseAll();
      target.addEventListener('keydown', down);
      target.addEventListener('keyup', up);
      window.addEventListener('blur', blur);
      this._detach.push(() => { target.removeEventListener('keydown', down); target.removeEventListener('keyup', up); window.removeEventListener('blur', blur); });
    }

    /* ---------- 터치 버튼 ---------- */
    attachButtons(container) {
      const btns = container.querySelectorAll('[data-act]');
      btns.forEach((btn) => {
        const act = btn.dataset.act;
        const down = (e) => {
          e.preventDefault();
          e.stopPropagation();
          try { btn.setPointerCapture(e.pointerId); } catch (_) { /* 무시 */ }
          btn.classList.add('pressed');
          this._press(act, 'btn:' + e.pointerId + ':' + act);
        };
        const up = (e) => {
          btn.classList.remove('pressed');
          this._release(act, 'btn:' + e.pointerId + ':' + act);
        };
        btn.addEventListener('pointerdown', down);
        btn.addEventListener('pointerup', up);
        btn.addEventListener('pointercancel', up);
        btn.addEventListener('lostpointercapture', up);
        btn.addEventListener('contextmenu', (e) => e.preventDefault());
        this._detach.push(() => {
          btn.removeEventListener('pointerdown', down); btn.removeEventListener('pointerup', up);
          btn.removeEventListener('pointercancel', up); btn.removeEventListener('lostpointercapture', up);
        });
      });
    }

    /* ---------- 스와이프 ---------- */
    attachSwipe(el, getCell) {
      let g = null;
      const down = (e) => {
        if (e.pointerType === 'mouse' || g) return;
        e.preventDefault();
        try { el.setPointerCapture(e.pointerId); } catch (_) { /* 무시 */ }
        g = { id: e.pointerId, x0: e.clientX, y0: e.clientY, lx: e.clientX, ly: e.clientY, t0: performance.now(), mode: null, accX: 0, accY: 0, hist: [] };
      };
      const move = (e) => {
        if (!g || e.pointerId !== g.id || !this.enabled) return;
        e.preventDefault();
        const cell = getCell();
        const now = performance.now();
        const dx = e.clientX - g.lx, dy = e.clientY - g.ly;
        g.lx = e.clientX; g.ly = e.clientY;
        g.hist.push({ t: now, y: e.clientY });
        while (g.hist.length && now - g.hist[0].t > 90) g.hist.shift();
        const tx = e.clientX - g.x0, ty = e.clientY - g.y0;
        if (!g.mode) {
          if (Math.abs(tx) > cell * 0.45 && Math.abs(tx) > Math.abs(ty)) g.mode = 'h';
          else if (ty > cell * 0.6 && ty > Math.abs(tx)) g.mode = 'v';
          else if (ty < -cell * 1.2 && -ty > Math.abs(tx)) g.mode = 'up';
          if (g.mode === 'h') g.accX = tx;
          if (g.mode === 'v') g.accY = 0;
        } else if (g.mode === 'h') g.accX += dx;
        else if (g.mode === 'v') g.accY += dy;
        if (g.mode === 'h') {
          const step = cell * 0.85;
          while (g.accX >= step) { g.accX -= step; this.a.move(1); }
          while (g.accX <= -step) { g.accX += step; this.a.move(-1); }
        } else if (g.mode === 'v') {
          const step = cell * 0.75;
          while (g.accY >= step) { g.accY -= step; this.a.softStep(); }
        }
      };
      const up = (e) => {
        if (!g || e.pointerId !== g.id) return;
        const now = performance.now();
        const dt = now - g.t0;
        const tx = e.clientX - g.x0, ty = e.clientY - g.y0;
        const cell = getCell();
        if (this.enabled && e.type === 'pointerup') {
          if (!g.mode && Math.hypot(tx, ty) < Math.max(10, cell * 0.4) && dt < 350) {
            if (this.onAction) this.onAction('cw', 'tap');
            this.a.cw();
          } else if (g.mode === 'v' || (!g.mode && ty > cell)) {
            const h = g.hist;
            const v = h.length > 1 ? (h[h.length - 1].y - h[0].y) / Math.max(1, h[h.length - 1].t - h[0].t) : ty / Math.max(1, dt);
            if (v > 0.9 && ty > cell * 1.5) { if (this.onAction) this.onAction('hard', 'swipe'); this.a.hard(); }
          } else if (g.mode === 'up') {
            if (this.onAction) this.onAction('hold', 'swipe');
            this.a.hold();
          }
        }
        g = null;
      };
      el.addEventListener('pointerdown', down);
      el.addEventListener('pointermove', move);
      el.addEventListener('pointerup', up);
      el.addEventListener('pointercancel', up);
      this._detach.push(() => {
        el.removeEventListener('pointerdown', down); el.removeEventListener('pointermove', move);
        el.removeEventListener('pointerup', up); el.removeEventListener('pointercancel', up);
      });
    }

    destroy() { this._detach.forEach((f) => f()); this._detach = []; this.releaseAll(); }
  }

  IT.InputController = InputController;
  IT.KEYMAP = KEYMAP;
})();
