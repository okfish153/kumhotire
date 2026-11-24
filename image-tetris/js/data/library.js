/* IMAGE TETRIS – 이미지 라이브러리 (샘플 + 사용자 이미지 통합 관리)
 * - 사용자 이미지는 IndexedDB 에 Blob 으로 저장 (외부 전송 없음)
 * - 편집값(adjust)은 원본을 바꾸지 않는 비파괴 방식
 * - 디코딩된 이미지는 메모리 캐시로 재사용
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const P = IT.ImageProc;

  class ImageLibrary extends IT.Emitter {
    constructor(db) {
      super();
      this.db = db;
      this.user = []; // {id, name, blob, thumb, width, height, adjust, createdAt}
      this.sampleAdjust = IT.Storage.loadSampleAdjust();
      this.themeOverrides = IT.Storage.loadThemeOverrides();
      this._base = new Map(); // id → Promise<canvas>
      this._adjusted = new Map(); // key → canvas
      this._themes = new Map(); // id|adjust → theme
    }

    async init() {
      try {
        const recs = await this.db.getAll('images');
        this.user = recs.sort((a, b) => a.createdAt - b.createdAt);
      } catch (e) {
        console.warn('이미지 목록을 불러오지 못했습니다', e);
        this.user = [];
      }
    }

    /* ---------- 조회 ---------- */
    isSample(id) { return typeof id === 'string' && id.startsWith('sample:'); }
    get(id) {
      if (!id) return null;
      if (this.isSample(id)) {
        const s = IT.Samples.get(id);
        return s ? { id, name: s.name, kind: 'sample', theme: s.themeName, thumb: s.url, adjust: this.sampleAdjust[id] || null } : null;
      }
      const u = this.user.find((x) => x.id === id);
      return u ? { id, name: u.name, kind: 'user', thumb: u.thumb, adjust: u.adjust || null, width: u.width, height: u.height } : null;
    }
    exists(id) { return !!this.get(id); }
    userList() { return this.user.map((u) => this.get(u.id)); }
    allIds() { return [...this.user.map((u) => u.id), ...IT.Samples.all().map((s) => s.id)]; }
    resolve(id) { return this.exists(id) ? id : IT.Samples.DEFAULT_ID; }

    /* ---------- 추가 / 삭제 ---------- */
    async addFiles(files, onProgress) {
      const added = [], errors = [];
      const list = Array.from(files || []);
      for (let i = 0; i < list.length; i++) {
        const f = list[i];
        if (onProgress) onProgress(i, list.length, f.name);
        try {
          const r = await P.processFile(f);
          const rec = {
            id: IT.util.uid('img_'),
            name: (f.name || '이미지').replace(/\.[^.]+$/, '').slice(0, 40) || '이미지',
            blob: r.blob,
            thumb: r.thumb,
            width: r.width,
            height: r.height,
            originalWidth: r.originalWidth,
            originalHeight: r.originalHeight,
            adjust: null,
            createdAt: Date.now() + i,
          };
          await this.db.put('images', rec);
          this.user.push(rec);
          added.push(rec.id);
        } catch (e) {
          errors.push({ name: f.name || '(이름 없음)', message: e && e.message ? e.message : String(e) });
        }
      }
      if (onProgress) onProgress(list.length, list.length, '');
      if (added.length) this.emit('change', { added });
      return { added, errors };
    }

    async remove(id) {
      if (this.isSample(id)) return false;
      await this.db.delete('images', id);
      this.user = this.user.filter((u) => u.id !== id);
      this._invalidate(id);
      this._base.delete(id);
      delete this.themeOverrides[id];
      IT.Storage.saveThemeOverrides(this.themeOverrides);
      this.emit('change', { removed: [id] });
      return true;
    }

    async removeAllUser() {
      await this.db.clear('images');
      this.user.forEach((u) => { this._invalidate(u.id); this._base.delete(u.id); });
      this.user = [];
      this.emit('change', { cleared: true });
    }

    async rename(id, name) {
      const u = this.user.find((x) => x.id === id);
      if (!u) return;
      u.name = String(name).slice(0, 40) || u.name;
      await this.db.put('images', u);
      this.emit('change', { renamed: id });
    }

    /* ---------- 편집값 ---------- */
    getAdjust(id) { const r = this.get(id); return P.normalizeAdjust(r && r.adjust); }
    async setAdjust(id, adjust) {
      const a = P.normalizeAdjust(adjust);
      const isDefault = a.rot === 0 && !a.flip && !a.crop && a.brightness === 100 && a.opacity === 100;
      this._invalidate(id);
      if (this.isSample(id)) {
        if (isDefault) delete this.sampleAdjust[id]; else this.sampleAdjust[id] = a;
        IT.Storage.saveSampleAdjust(this.sampleAdjust);
      } else {
        const u = this.user.find((x) => x.id === id);
        if (!u) return;
        u.adjust = isDefault ? null : a;
        try {
          const canvas = await this.getAdjusted(id, 480);
          u.thumb = P.thumbDataURL(canvas, 240, false);
        } catch (e) { /* 썸네일 갱신 실패는 무시 */ }
        await this.db.put('images', u);
      }
      this.emit('change', { adjusted: id });
    }
    async resetAllSampleAdjust() {
      Object.keys(this.sampleAdjust).forEach((id) => this._invalidate(id));
      this.sampleAdjust = {};
      IT.Storage.saveSampleAdjust({});
      this.emit('change', {});
    }

    _invalidate(id) {
      for (const k of Array.from(this._adjusted.keys())) if (k.startsWith(id + '|')) this._adjusted.delete(k);
      for (const k of Array.from(this._themes.keys())) if (k.startsWith(id + '|')) this._themes.delete(k);
    }

    /* ---------- 디코딩 / 렌더링 ---------- */
    getBase(id) {
      if (this._base.has(id)) return this._base.get(id);
      const p = this._loadBase(id).catch((e) => { this._base.delete(id); throw e; });
      this._base.set(id, p);
      // 메모리 관리: 최근 16개만 유지
      if (this._base.size > 16) { const first = this._base.keys().next().value; if (first !== id) this._base.delete(first); }
      return p;
    }
    async _loadBase(id) {
      if (this.isSample(id)) {
        const s = IT.Samples.get(id);
        if (!s) throw new Error('샘플 이미지를 찾을 수 없습니다.');
        const img = await P.loadImage(s.url);
        // SVG 는 1.5배 해상도로 래스터화
        const scale = s.svg ? 1.5 : 1;
        const w = (img.naturalWidth || 600) * scale, h = (img.naturalHeight || 800) * scale;
        const c = IT.util.createCanvas(w, h);
        c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        return c;
      }
      const u = this.user.find((x) => x.id === id);
      if (!u) {
        // DB 에 남아 있을 수 있으므로 재시도
        const rec = await this.db.get('images', id);
        if (!rec) throw new Error('이미지를 찾을 수 없습니다.');
        this.user.push(rec);
        return this._loadBase(id);
      }
      const img = await P.loadImage(u.blob);
      return P.downscale(img, P.MAX_SIDE);
    }

    /** 편집값이 적용된 캔버스 (maxSide 이하) */
    async getAdjusted(id, maxSide = 1200) {
      const adj = this.getAdjust(id);
      const key = id + '|' + maxSide + '|' + JSON.stringify(adj);
      if (this._adjusted.has(key)) return this._adjusted.get(key);
      const base = await this.getBase(id);
      const c = P.applyAdjust(base, adj, maxSide);
      this._adjusted.set(key, c);
      if (this._adjusted.size > 40) this._adjusted.delete(this._adjusted.keys().next().value);
      return c;
    }

    /* ---------- 테마 ---------- */
    async getTheme(id) {
      const adj = this.getAdjust(id);
      const key = id + '|' + JSON.stringify(adj);
      let theme = this._themes.get(key);
      if (!theme) {
        const c = await this.getAdjusted(id, 400);
        const pal = IT.Palette.extractPalette(c, 7).map((p) => p.hex);
        theme = IT.Palette.buildTheme(pal);
        this._themes.set(key, theme);
      }
      const ov = this.themeOverrides[id];
      if (ov) {
        theme = Object.assign({}, theme, ov.ui || {}, { pieces: Object.assign({}, theme.pieces, ov.pieces || {}) });
      }
      return theme;
    }
    async getAutoTheme(id) {
      const saved = this.themeOverrides[id];
      delete this.themeOverrides[id];
      const t = await this.getTheme(id);
      if (saved) this.themeOverrides[id] = saved;
      return t;
    }
    setThemeOverride(id, ov) {
      if (!ov) delete this.themeOverrides[id];
      else this.themeOverrides[id] = ov;
      IT.Storage.saveThemeOverrides(this.themeOverrides);
      this.emit('change', { theme: id });
    }
  }

  IT.ImageLibrary = ImageLibrary;
})();
