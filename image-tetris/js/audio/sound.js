/* IMAGE TETRIS – 자체 합성 효과음 + 배경음 (Web Audio API, 외부 음원 파일 없음)
 * 배경음은 이 게임을 위해 만든 오리지널 멜로디입니다.
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});

  const NOTE = (n) => 440 * Math.pow(2, (n - 69) / 12); // MIDI → Hz

  // 오리지널 배경음: 8마디 루프 (C장조, I–V–vi–IV / I–iii–IV–V 진행)
  const CHORDS = [
    [48, 52, 55], [43, 47, 50], [45, 48, 52], [41, 45, 48],
    [48, 52, 55], [40, 43, 47], [41, 45, 48], [43, 47, 50],
  ];
  // 멜로디: 마디당 8분음표 8개 (null = 쉼)
  const MELODY = [
    [72, null, 76, 79, 77, 76, 74, null],
    [71, null, 74, 79, 77, 74, 71, 74],
    [72, null, 69, 72, 76, null, 74, 72],
    [69, 72, 77, null, 76, 74, 72, null],
    [76, null, 79, 84, 83, 79, 76, null],
    [79, 76, 71, null, 72, 74, 76, 79],
    [81, null, 77, 81, 79, 77, 76, 74],
    [74, 76, 77, 79, 74, null, 71, null],
  ];

  class Sound {
    constructor(settings) {
      this.settings = settings;
      this.ctx = null;
      this.master = null;
      this.sfxGain = null;
      this.bgmGain = null;
      this.bgmPlaying = false;
      this.bgmTimer = null;
      this.tempo = 112;
      this._step = 0;
      this._nextTime = 0;
      this._noiseBuf = null;
      this._lastPlay = {};
    }

    /** 사용자 입력 이후 호출 (브라우저 자동재생 정책) */
    unlock() {
      if (!this.ctx) {
        const AC = globalThis.AudioContext || globalThis.webkitAudioContext;
        if (!AC) return false;
        try {
          this.ctx = new AC();
        } catch (e) { return false; }
        const comp = this.ctx.createDynamicsCompressor();
        comp.threshold.value = -14; comp.ratio.value = 4;
        this.master = this.ctx.createGain(); this.master.gain.value = 0.9;
        this.sfxGain = this.ctx.createGain();
        this.bgmGain = this.ctx.createGain();
        this.sfxGain.connect(comp); this.bgmGain.connect(comp); comp.connect(this.master); this.master.connect(this.ctx.destination);
        this.applySettings();
        const len = this.ctx.sampleRate * 0.5;
        this._noiseBuf = this.ctx.createBuffer(1, len, this.ctx.sampleRate);
        const d = this._noiseBuf.getChannelData(0);
        for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
      }
      if (this.ctx.state === 'suspended') this.ctx.resume().catch(() => {});
      return true;
    }

    applySettings() {
      if (!this.ctx) return;
      const s = this.settings;
      const t = this.ctx.currentTime;
      this.sfxGain.gain.setTargetAtTime(s.sfxOn ? s.sfxVolume : 0, t, 0.02);
      this.bgmGain.gain.setTargetAtTime(s.bgmOn ? s.bgmVolume * 0.5 : 0, t, 0.05);
    }

    /* ---------- 합성 도구 ---------- */
    _tone(freq, dur, { type = 'sine', vol = 0.2, attack = 0.005, at = 0, slide = null, dest = null, detune = 0 } = {}) {
      const c = this.ctx;
      const t = c.currentTime + at;
      const o = c.createOscillator();
      const g = c.createGain();
      o.type = type;
      o.frequency.setValueAtTime(freq, t);
      if (detune) o.detune.value = detune;
      if (slide) o.frequency.exponentialRampToValueAtTime(slide, t + dur);
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(vol, t + attack);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(g); g.connect(dest || this.sfxGain);
      o.start(t); o.stop(t + dur + 0.05);
    }
    _noise(dur, { vol = 0.2, at = 0, filter = 2000, type = 'lowpass', dest = null, q = 1 } = {}) {
      const c = this.ctx;
      const t = c.currentTime + at;
      const src = c.createBufferSource();
      src.buffer = this._noiseBuf;
      const f = c.createBiquadFilter(); f.type = type; f.frequency.value = filter; f.Q.value = q;
      const g = c.createGain();
      g.gain.setValueAtTime(vol, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      src.connect(f); f.connect(g); g.connect(dest || this.sfxGain);
      src.start(t); src.stop(t + dur + 0.02);
    }

    /** 효과음 재생 */
    play(name, arg) {
      if (!this.ctx || !this.settings.sfxOn) return;
      const now = performance.now();
      // 같은 소리가 너무 촘촘하면 생략 (성능/청감)
      if (this._lastPlay[name] && now - this._lastPlay[name] < 28) return;
      this._lastPlay[name] = now;
      const T = this._tone.bind(this), N = this._noise.bind(this);
      switch (name) {
        case 'move': T(560, 0.04, { type: 'square', vol: 0.035 }); break;
        case 'rotate': T(720, 0.06, { type: 'triangle', vol: 0.08, slide: 980 }); break;
        case 'softdrop': T(300, 0.03, { type: 'sine', vol: 0.03 }); break;
        case 'harddrop': N(0.16, { vol: 0.3, filter: 900 }); T(170, 0.16, { type: 'sine', vol: 0.32, slide: 55 }); break;
        case 'lock': T(240, 0.07, { type: 'triangle', vol: 0.09, slide: 180 }); break;
        case 'hold': T(520, 0.07, { type: 'triangle', vol: 0.09 }); T(780, 0.09, { type: 'triangle', vol: 0.08, at: 0.06 }); break;
        case 'clear': {
          const n = arg || 1;
          const base = [72, 76, 79, 84, 88];
          for (let i = 0; i <= n; i++) T(NOTE(base[i]), 0.22, { type: 'triangle', vol: 0.12, at: i * 0.05 });
          N(0.25, { vol: 0.08, filter: 5000, type: 'highpass' });
          break;
        }
        case 'tetris': {
          [72, 76, 79, 84, 88, 91].forEach((m, i) => { T(NOTE(m), 0.3, { type: 'square', vol: 0.06, at: i * 0.05 }); T(NOTE(m), 0.35, { type: 'triangle', vol: 0.1, at: i * 0.05 }); });
          N(0.5, { vol: 0.12, filter: 6000, type: 'highpass' });
          break;
        }
        case 'tspin': T(400, 0.25, { type: 'sawtooth', vol: 0.07, slide: 1200 }); T(NOTE(83), 0.3, { type: 'triangle', vol: 0.1, at: 0.12 }); break;
        case 'combo': { const k = Math.min(arg || 1, 12); T(NOTE(72 + k * 2), 0.14, { type: 'square', vol: 0.06 }); T(NOTE(79 + k * 2), 0.16, { type: 'triangle', vol: 0.08, at: 0.05 }); break; }
        case 'levelup': [67, 72, 76, 79, 84].forEach((m, i) => T(NOTE(m), 0.18, { type: 'square', vol: 0.07, at: i * 0.07 })); break;
        case 'reveal': T(NOTE(88), 0.5, { type: 'sine', vol: 0.09 }); T(NOTE(95), 0.6, { type: 'sine', vol: 0.05, at: 0.04 }); break;
        case 'complete': {
          const mel = [[72, 0], [76, 0.12], [79, 0.24], [84, 0.36], [79, 0.52], [84, 0.64]];
          mel.forEach(([m, at]) => { T(NOTE(m), 0.3, { type: 'square', vol: 0.07, at }); T(NOTE(m), 0.32, { type: 'triangle', vol: 0.1, at }); });
          [60, 64, 67, 72].forEach((m) => T(NOTE(m), 1.4, { type: 'triangle', vol: 0.08, at: 0.64, attack: 0.03 }));
          [0.7, 0.8, 0.9, 1.0].forEach((at) => N(0.3, { vol: 0.06, filter: 7000, type: 'highpass', at }));
          break;
        }
        case 'gameover': [67, 63, 60, 55].forEach((m, i) => T(NOTE(m), 0.35, { type: 'triangle', vol: 0.12, at: i * 0.18 })); break;
        case 'count': T(NOTE(76), 0.12, { type: 'square', vol: 0.07 }); break;
        case 'go': T(NOTE(84), 0.3, { type: 'square', vol: 0.08 }); T(NOTE(88), 0.3, { type: 'triangle', vol: 0.08 }); break;
        case 'pause': T(NOTE(69), 0.12, { type: 'sine', vol: 0.08 }); T(NOTE(64), 0.15, { type: 'sine', vol: 0.08, at: 0.08 }); break;
        case 'click': T(900, 0.03, { type: 'triangle', vol: 0.06 }); break;
        case 'error': T(220, 0.15, { type: 'square', vol: 0.06, slide: 160 }); break;
        case 'upload': [76, 81, 88].forEach((m, i) => T(NOTE(m), 0.12, { type: 'triangle', vol: 0.08, at: i * 0.06 })); break;
        default: break;
      }
    }

    /* ---------- 배경음 ---------- */
    startBgm() {
      if (!this.ctx || this.bgmPlaying) return;
      this.bgmPlaying = true;
      this._step = 0;
      this._nextTime = this.ctx.currentTime + 0.1;
      const tick = () => {
        if (!this.bgmPlaying) return;
        const eighth = 60 / this.tempo / 2;
        while (this._nextTime < this.ctx.currentTime + 0.25) {
          this._scheduleStep(this._step, this._nextTime, eighth);
          this._nextTime += eighth;
          this._step = (this._step + 1) % 64;
        }
      };
      tick();
      this.bgmTimer = setInterval(tick, 50);
    }
    stopBgm() {
      this.bgmPlaying = false;
      clearInterval(this.bgmTimer);
      this.bgmTimer = null;
    }
    setTempoForLevel(level) { this.tempo = Math.min(150, 108 + (level - 1) * 2.5); }

    _scheduleStep(step, t, eighth) {
      const bar = Math.floor(step / 8), pos = step % 8;
      const c = this.ctx, dest = this.bgmGain;
      const at = t - c.currentTime;
      if (at < -0.01) return;
      const chord = CHORDS[bar];
      // 베이스 (4분음표)
      if (pos % 2 === 0) this._tone(NOTE(chord[0] - 12 + (pos === 4 ? 7 : 0)), eighth * 1.8, { type: 'triangle', vol: 0.22, at, dest, attack: 0.01 });
      // 아르페지오 (8분음표, 부드러운 사인)
      const arp = chord[[0, 1, 2, 1][pos % 4]] + 12;
      this._tone(NOTE(arp), eighth * 0.9, { type: 'sine', vol: 0.07, at, dest, attack: 0.01 });
      // 패드 (마디 시작)
      if (pos === 0) chord.forEach((m) => this._tone(NOTE(m + 12), eighth * 7.5, { type: 'triangle', vol: 0.035, at, dest, attack: 0.25 }));
      // 멜로디
      const m = MELODY[bar][pos];
      if (m != null) {
        this._tone(NOTE(m), eighth * 0.95, { type: 'square', vol: 0.035, at, dest, attack: 0.01 });
        this._tone(NOTE(m), eighth * 1.1, { type: 'triangle', vol: 0.06, at, dest, attack: 0.01, detune: 6 });
      }
      // 리듬 (하이햇 / 킥)
      this._noise(0.04, { vol: pos % 2 ? 0.03 : 0.05, filter: 8000, type: 'highpass', at, dest });
      if (pos === 0 || pos === 4) this._tone(110, 0.12, { type: 'sine', vol: 0.2, slide: 45, at, dest });
      if (pos === 2 || pos === 6) this._noise(0.1, { vol: 0.06, filter: 1800, type: 'bandpass', at, dest });
    }
  }

  IT.Sound = Sound;
})();
