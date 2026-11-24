/* IMAGE TETRIS – 완성한 이미지 컬렉션 (IndexedDB 'collection') */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const P = IT.ImageProc;

  class Collection extends IT.Emitter {
    constructor(db) { super(); this.db = db; this.items = []; }
    async init() {
      try { this.items = (await this.db.getAll('collection')).sort((a, b) => b.completedAt - a.completedAt); }
      catch (e) { this.items = []; }
    }
    list() { return this.items.slice(); }
    count() { return this.items.length; }
    has(imageId) { return this.items.some((x) => x.imageId === imageId); }
    /** 완성 이미지 저장 – 원본 이미지가 삭제되어도 보관되도록 사본(최대 1200px)을 저장 */
    async add({ imageId, name, canvas, mode, score, lines, difficulty }) {
      const copy = P.downscale(canvas, 1200);
      const blob = await P.canvasToBlob(copy, 'image/jpeg', 0.9);
      const rec = {
        id: IT.util.uid('col_'),
        imageId, name, blob,
        thumb: P.thumbDataURL(copy, 260),
        width: copy.width, height: copy.height,
        completedAt: Date.now(),
        mode, score, lines, difficulty,
      };
      await this.db.put('collection', rec);
      this.items.unshift(rec);
      this.emit('change');
      return rec;
    }
    async remove(id) {
      await this.db.delete('collection', id);
      this.items = this.items.filter((x) => x.id !== id);
      this.emit('change');
    }
    async clear() {
      await this.db.clear('collection');
      this.items = [];
      this.emit('change');
    }
  }

  IT.Collection = Collection;
})();
