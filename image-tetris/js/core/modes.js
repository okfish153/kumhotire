/* IMAGE TETRIS – 게임 모드 / 난이도 / 이미지 공개 진행 로직 (순수 로직) */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const { shuffle, range, clamp } = IT.util;

  const MODES = {
    A: { key: 'A', name: '이미지 배경', title: '이미지 배경 테트리스', icon: '🖼️',
      desc: '내 이미지를 게임판 배경으로! 밝기와 투명도를 조절해 블록은 선명하게.' },
    B: { key: 'B', name: '이미지 블록', title: '이미지 블록 테트리스', icon: '🧩',
      desc: '블록 표면이 내 이미지로. 회전하면 이미지도 함께 돌아갑니다.' },
    C: { key: 'C', name: '이미지 완성', title: '이미지 완성 테트리스', icon: '✨',
      desc: '줄을 지울 때마다 가려진 이미지 조각이 공개됩니다. 목표 줄 수를 채워 완성하세요!' },
    D: { key: 'D', name: '테마 자동 생성', title: '이미지 테마 테트리스', icon: '🎨',
      desc: '이미지에서 대표 색을 뽑아 블록·버튼·배경을 꾸밉니다. 색상은 직접 수정 가능.' },
    E: { key: 'E', name: '랜덤 챌린지', title: '랜덤 이미지 챌린지', icon: '🎲',
      desc: '무작위 미스터리 이미지! 목표를 달성할 때마다 새 이미지가 등장합니다.' },
  };
  const MODE_ORDER = ['A', 'B', 'C', 'D', 'E'];

  const DIFFICULTIES = {
    easy: { key: 'easy', name: '초급', target: 10, startLevel: 1 },
    normal: { key: 'normal', name: '중급', target: 20, startLevel: 3 },
    hard: { key: 'hard', name: '고급', target: 40, startLevel: 5 },
    custom: { key: 'custom', name: '사용자 설정', target: 15, startLevel: 1 },
  };

  function resolveDifficulty(key, custom) {
    const d = Object.assign({}, DIFFICULTIES[key] || DIFFICULTIES.easy);
    if (d.key === 'custom' && custom) {
      d.target = clamp(Math.round(custom.target || d.target), 1, 200);
      d.startLevel = clamp(Math.round(custom.startLevel || 1), 1, 20);
    }
    return d;
  }

  /** 목표 줄 수와 이미지 비율(가로/세로)에 맞는 조각 격자 계산 */
  function revealGrid(target, aspect) {
    target = Math.max(1, Math.round(target));
    aspect = aspect > 0 ? aspect : 1;
    let best = null;
    const maxTiles = Math.max(target, Math.ceil(target * 1.5));
    for (let rows = 1; rows <= target; rows++) {
      for (let cols = 1; cols <= target; cols++) {
        const n = rows * cols;
        if (n < target || n > maxTiles) continue;
        // 조각 하나의 비율이 정사각형에 가까울수록 좋음
        const tileAspect = aspect / cols * rows;
        const score = Math.abs(Math.log(tileAspect)) + 0.6 * (n - target) / target;
        if (!best || score < best.score) best = { cols, rows, score };
      }
    }
    return { cols: best.cols, rows: best.rows };
  }

  class RevealProgress {
    constructor(target, aspect, rng) {
      this.target = Math.max(1, Math.round(target));
      const g = revealGrid(this.target, aspect);
      this.cols = g.cols;
      this.rows = g.rows;
      this.total = g.cols * g.rows;
      this.order = shuffle(range(this.total), rng);
      this.lines = 0;
      this.revealedCount = 0;
      this._set = new Set();
    }
    get percent() { return Math.min(100, (this.lines / this.target) * 100); }
    get complete() { return this.lines >= this.target; }
    /** 줄 제거 반영 → 새로 공개된 조각 인덱스 목록 반환 */
    addLines(n) {
      if (n <= 0 || this.complete) return [];
      const before = this.revealedCount;
      this.lines = Math.min(this.target, this.lines + n);
      this.revealedCount = this.complete ? this.total : Math.floor((this.lines * this.total) / this.target);
      const fresh = this.order.slice(before, this.revealedCount);
      fresh.forEach((i) => this._set.add(i));
      return fresh;
    }
    isRevealed(i) { return this._set.has(i); }
  }

  /** 같은 이미지가 연속/반복되지 않도록 뽑는 무작위 선택기 */
  class ImagePicker {
    constructor(ids, rng) {
      this.ids = Array.from(new Set(ids));
      this.rng = rng || Math.random;
      this.bag = [];
      this.last = null;
      this.history = [];
    }
    next() {
      if (!this.ids.length) return null;
      if (!this.bag.length) {
        this.bag = shuffle(this.ids.slice(), this.rng);
        // 새 주머니의 첫 이미지가 직전 이미지와 같으면 뒤로 보냄
        if (this.bag.length > 1 && this.bag[this.bag.length - 1] === this.last) {
          const t = this.bag[0]; this.bag[0] = this.bag[this.bag.length - 1]; this.bag[this.bag.length - 1] = t;
        }
      }
      const id = this.bag.pop();
      this.last = id;
      this.history.push(id);
      return id;
    }
  }

  IT.Modes = { MODES, MODE_ORDER, DIFFICULTIES, resolveDifficulty, revealGrid, RevealProgress, ImagePicker };
})();
