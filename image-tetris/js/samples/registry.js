/* IMAGE TETRIS – 샘플 이미지 레지스트리
 *
 * 새 샘플 테마/이미지 추가 방법:
 *   IT.Samples.register({ key: 'my-theme', name: '내 테마', icon: '⭐' }, [
 *     { key: 'my-image', name: '이미지 이름', svg: '<svg ...>...</svg>' },   // 코드로 그린 SVG
 *     { key: 'my-photo', name: '사진', src: 'assets/samples/photo.jpg' },     // 파일 (웹 서버로 실행할 때)
 *   ]);
 * 이미지 id 는 'sample:<key>' 가 됩니다. key 는 전체 샘플에서 고유해야 합니다.
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});

  const themes = [];
  const byId = new Map();

  function register(theme, items) {
    let t = themes.find((x) => x.key === theme.key);
    if (!t) { t = Object.assign({ items: [] }, theme); themes.push(t); }
    for (const it of items) {
      const id = 'sample:' + it.key;
      if (byId.has(id)) { console.warn('[Samples] 중복 key 무시:', it.key); continue; }
      const rec = Object.assign({ id, kind: 'sample', theme: t.key, themeName: t.name }, it);
      if (rec.svg) rec.url = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(rec.svg);
      else rec.url = rec.src;
      t.items.push(rec);
      byId.set(id, rec);
    }
  }

  IT.Samples = {
    register,
    themes,
    get(id) { return byId.get(id) || null; },
    all() { return themes.flatMap((t) => t.items); },
    DEFAULT_ID: 'sample:mountain-lake',
  };
})();
