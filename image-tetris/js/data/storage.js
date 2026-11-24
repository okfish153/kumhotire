/* IMAGE TETRIS – LocalStorage 기반 설정 / 기록 / 게임 구성 저장 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const PREFIX = 'imageTetris.';

  const ls = {
    get(key, def) {
      try {
        const v = localStorage.getItem(PREFIX + key);
        return v == null ? def : JSON.parse(v);
      } catch (e) { return def; }
    },
    set(key, val) {
      try { localStorage.setItem(PREFIX + key, JSON.stringify(val)); return true; } catch (e) { return false; }
    },
    remove(key) { try { localStorage.removeItem(PREFIX + key); } catch (e) { /* 무시 */ } },
  };

  const DEFAULT_SETTINGS = {
    bgmOn: true, sfxOn: true, bgmVolume: 0.45, sfxVolume: 0.7,
    das: 160, arr: 40, softDropSpeed: 30,
    ghost: true, grid: true, effects: 'full', // full | reduced
    smoothMove: true, autoNext: true, vibration: true,
    pieceColors: 'theme', // theme | classic
    touchControls: 'auto', // auto | on | off
  };

  const DEFAULT_CONFIG = {
    mode: 'C',
    difficulty: 'easy',
    custom: { target: 15, startLevel: 1 },
    mainImage: 'sample:mountain-lake', // 대표 이미지 (완성 모드, 테마)
    bgImage: null, // null = 대표 이미지 사용
    blockMode: 'slice', // slice(한 장 분할) | perPiece(7종 개별)
    blockImage: null, // slice 모드 원본 (null = 대표 이미지)
    pieceImages: {}, // { I: id, ... }
    bgOpacity: 0.55, // 배경 이미지 투명도 (0~1)
    bgDim: 0.35, // 배경 어둡게 (0~1)
    blockBg: true, // 이미지 블록 모드에서 배경 이미지도 표시
    challengePool: 'all', // all | user | samples
  };

  const Storage = {
    loadSettings() { return Object.assign({}, DEFAULT_SETTINGS, ls.get('settings', {})); },
    saveSettings(s) { ls.set('settings', s); },
    loadConfig() {
      const c = Object.assign({}, DEFAULT_CONFIG, ls.get('config', {}));
      c.custom = Object.assign({}, DEFAULT_CONFIG.custom, c.custom || {});
      c.pieceImages = Object.assign({}, c.pieceImages || {});
      return c;
    },
    saveConfig(c) { ls.set('config', c); },
    defaultConfig() { return JSON.parse(JSON.stringify(DEFAULT_CONFIG)); },

    /* 샘플 이미지 편집값 / 이미지별 테마 색 수정값 */
    loadSampleAdjust() { return ls.get('sampleAdjust', {}); },
    saveSampleAdjust(m) { ls.set('sampleAdjust', m); },
    loadThemeOverrides() { return ls.get('themeOverrides', {}); },
    saveThemeOverrides(m) { ls.set('themeOverrides', m); },

    /* 기록 */
    loadRecords() {
      const r = ls.get('records', null) || {};
      return {
        best: r.best || {}, // mode → [{score, lines, level, time, date, difficulty}]
        plays: r.plays || 0,
        lines: r.lines || 0,
        time: r.time || 0,
        completed: r.completed || 0,
        modePlays: r.modePlays || {},
      };
    },
    saveRecords(r) { ls.set('records', r); },
    /** 게임 결과 반영 → 최고 점수 갱신 여부 반환 */
    addResult(res) {
      const r = Storage.loadRecords();
      r.plays++;
      r.lines += res.lines;
      r.time += res.time;
      r.completed += res.completed || 0;
      r.modePlays[res.mode] = (r.modePlays[res.mode] || 0) + 1;
      const list = (r.best[res.mode] = r.best[res.mode] || []);
      const prevBest = list.length ? list[0].score : 0;
      const entry = { score: res.score, lines: res.lines, level: res.level, time: res.time, date: Date.now(), difficulty: res.difficulty };
      list.push(entry);
      list.sort((a, b) => b.score - a.score);
      list.length = Math.min(list.length, 10);
      Storage.saveRecords(r);
      return { newBest: res.score > 0 && res.score > prevBest, prevBest, rank: list.indexOf(entry) + 1 };
    },
    bestScore(mode) { const l = Storage.loadRecords().best[mode]; return l && l.length ? l[0].score : 0; },
    resetRecords() { ls.remove('records'); },
    resetAll() {
      ['settings', 'config', 'records', 'sampleAdjust', 'themeOverrides'].forEach((k) => ls.remove(k));
    },
  };

  IT.Storage = Storage;
  IT.DEFAULT_SETTINGS = DEFAULT_SETTINGS;
})();
