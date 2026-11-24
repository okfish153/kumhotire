/* IMAGE TETRIS – IndexedDB 래퍼
 * stores: images(사용자 등록 이미지), collection(완성한 이미지)
 * IndexedDB 를 쓸 수 없는 환경(일부 사생활 보호 모드)에서는 메모리 저장소로 대체합니다.
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const DB_NAME = 'image-tetris';
  const DB_VERSION = 1;
  const STORES = ['images', 'collection'];

  class MemoryStore {
    constructor() { this.maps = {}; STORES.forEach((s) => (this.maps[s] = new Map())); this.persistent = false; }
    async getAll(store) { return Array.from(this.maps[store].values()); }
    async get(store, id) { return this.maps[store].get(id) || null; }
    async put(store, value) { this.maps[store].set(value.id, value); return value.id; }
    async delete(store, id) { this.maps[store].delete(id); }
    async clear(store) { this.maps[store].clear(); }
  }

  class IDBStore {
    constructor(db) { this.db = db; this.persistent = true; }
    _tx(store, mode, fn) {
      return new Promise((resolve, reject) => {
        let result;
        const tx = this.db.transaction(store, mode);
        const os = tx.objectStore(store);
        const req = fn(os);
        if (req) req.onsuccess = () => { result = req.result; };
        tx.oncomplete = () => resolve(result);
        tx.onerror = () => reject(tx.error || (req && req.error));
        tx.onabort = () => reject(tx.error || new Error('트랜잭션 중단'));
      });
    }
    getAll(store) { return this._tx(store, 'readonly', (os) => os.getAll()).then((r) => r || []); }
    get(store, id) { return this._tx(store, 'readonly', (os) => os.get(id)).then((r) => r || null); }
    put(store, value) { return this._tx(store, 'readwrite', (os) => os.put(value)); }
    delete(store, id) { return this._tx(store, 'readwrite', (os) => os.delete(id)); }
    clear(store) { return this._tx(store, 'readwrite', (os) => os.clear()); }
  }

  function open() {
    return new Promise((resolve) => {
      if (!globalThis.indexedDB) { resolve(new MemoryStore()); return; }
      let done = false;
      const fallback = () => { if (!done) { done = true; resolve(new MemoryStore()); } };
      const timer = setTimeout(fallback, 4000);
      try {
        const req = indexedDB.open(DB_NAME, DB_VERSION);
        req.onupgradeneeded = () => {
          const db = req.result;
          STORES.forEach((s) => { if (!db.objectStoreNames.contains(s)) db.createObjectStore(s, { keyPath: 'id' }); });
        };
        req.onsuccess = () => { if (done) return; done = true; clearTimeout(timer); resolve(new IDBStore(req.result)); };
        req.onerror = () => { clearTimeout(timer); fallback(); };
        req.onblocked = () => { clearTimeout(timer); fallback(); };
      } catch (e) { clearTimeout(timer); fallback(); }
    });
  }

  IT.DB = { open, MemoryStore };
})();
