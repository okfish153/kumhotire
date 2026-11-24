/* IMAGE TETRIS – 화면 구성 (메인, 이미지 설정, 컬렉션, 기록, 설정, 일시정지/완성/결과 창)
 * App.prototype 에 화면별 메서드를 추가합니다.
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const { $, $$, h } = IT.UI;
  const U = IT.util;
  const { MODES, MODE_ORDER, DIFFICULTIES } = IT.Modes;
  const TYPES = IT.Pieces.TYPES;
  const proto = {};

  /* =========================================================
   * 초기 바인딩 (한 번만)
   * ========================================================= */
  proto.initScreens = function () {
    // 메인
    $('#btn-start').addEventListener('click', () => this.startGame());
    $('#custom-target').addEventListener('change', (e) => { this.config.custom.target = U.clamp(Number(e.target.value) || 15, 1, 200); e.target.value = this.config.custom.target; this.saveConfig(); this._renderDiffHint(); });
    $('#custom-level').addEventListener('change', (e) => { this.config.custom.startLevel = U.clamp(Number(e.target.value) || 1, 1, 20); e.target.value = this.config.custom.startLevel; this.saveConfig(); this._renderDiffHint(); });

    // 이미지 설정
    $$('[data-libtab]').forEach((b) => b.addEventListener('click', () => { this.libTab = b.dataset.libtab; this.renderLibrary(); }));
    const input = $('#file-input');
    input.addEventListener('change', () => { if (input.files && input.files.length) this.uploadFiles(input.files); input.value = ''; });
    const dz = $('#dropzone');
    dz.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); } });
    ['dragenter', 'dragover'].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add('over'); }));
    ['dragleave', 'drop'].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove('over'); }));
    dz.addEventListener('drop', (e) => { const f = e.dataTransfer && e.dataTransfer.files; if (f && f.length) this.uploadFiles(f); });
    // 화면 어디에 떨어뜨려도 등록 (이미지 설정 화면)
    document.addEventListener('dragover', (e) => { if (this.screen === 'library') e.preventDefault(); });
    document.addEventListener('drop', (e) => {
      if (this.screen !== 'library' || e.defaultPrevented) return;
      e.preventDefault();
      const f = e.dataTransfer && e.dataTransfer.files;
      if (f && f.length) this.uploadFiles(f);
    });

    $('#btn-edit').addEventListener('click', () => this.libSel && IT.Editor.open(this, this.libSel));
    $('#btn-rename').addEventListener('click', async () => {
      const r = this.library.get(this.libSel);
      if (!r || r.kind !== 'user') return;
      const name = await IT.UI.prompt('새 이름을 입력하세요.', r.name, { title: '이름 변경' });
      if (name) { await this.library.rename(this.libSel, name); this.onLibraryChanged(); }
    });
    $('#btn-delete').addEventListener('click', () => this.deleteImage(this.libSel));
    $$('.target').forEach((b) => b.addEventListener('click', () => this.assignTarget(b.dataset.target)));
    $$('[data-blockmode]').forEach((b) => b.addEventListener('click', () => {
      this.config.blockMode = b.dataset.blockmode; this.saveConfig(); this.renderLibrary();
    }));
    const pm = $('#preview-mode');
    MODE_ORDER.forEach((k) => pm.appendChild(h('option', { value: k }, `${MODES[k].icon} ${MODES[k].name}`)));
    pm.addEventListener('change', () => { this.previewMode = pm.value; this.drawLibraryPreview(); });
    const bindRange = (id, key, fmt) => {
      const el = $('#' + id), out = $('#' + id + '-out');
      el.addEventListener('input', () => { this.config[key] = Number(el.value); out.textContent = fmt(el.value); this.drawLibraryPreview(); });
      el.addEventListener('change', () => this.saveConfig());
    };
    bindRange('bg-opacity', 'bgOpacity', (v) => Math.round(v * 100) + '%');
    bindRange('bg-dim', 'bgDim', (v) => Math.round(v * 100) + '%');
    $('#block-bg').addEventListener('change', (e) => { this.config.blockBg = e.target.checked; this.saveConfig(); this.drawLibraryPreview(); });
    $('#btn-theme-reset').addEventListener('click', () => {
      this.library.setThemeOverride(this.config.mainImage, null);
      this.toast('자동 생성 색상으로 되돌렸습니다.');
      this.onLibraryChanged();
    });
    $('#btn-reset-default').addEventListener('click', () => this.resetToDefaultImages());
    $('#btn-save-start').addEventListener('click', () => { this.saveConfig(); this.toast('저장했습니다.', 'success', 1200); this.startGame(); });

    // 게임 화면 하단
    $('#btn-pause').addEventListener('click', () => this.session && this.session.togglePause());
    $('#btn-bgm').addEventListener('click', () => this.toggleSound('bgm'));
    $('#btn-sfx').addEventListener('click', () => this.toggleSound('sfx'));
    this._syncSoundButtons();

    // 컬렉션 / 기록
    $('#btn-col-clear').addEventListener('click', async () => {
      if (!this.collection.count()) return;
      if (await IT.UI.confirm('완성한 이미지 컬렉션을 모두 삭제할까요?', { title: '컬렉션 삭제', ok: '모두 삭제', danger: true })) {
        await this.collection.clear(); this.renderCollection(); this.toast('컬렉션을 비웠습니다.');
      }
    });
    $('#btn-rec-reset').addEventListener('click', async () => {
      if (await IT.UI.confirm('모든 최고 기록과 누적 통계를 초기화할까요?', { title: '기록 초기화', ok: '초기화', danger: true })) {
        IT.Storage.resetRecords(); this.invalidateBest(); this.renderRecords(); this.toast('기록을 초기화했습니다.');
      }
    });
    this.library.on('change', () => { this.invalidateBest(); });
  };

  /* =========================================================
   * 메인 화면
   * ========================================================= */
  proto.renderMenu = function () {
    const cfg = this.config, lib = this.library;
    const rec = lib.get(cfg.mainImage);
    $('#menu-thumb').src = rec ? rec.thumb : '';
    $('#menu-image-name').textContent = rec ? rec.name : '-';
    this.applyThemeFor(cfg.mainImage).then(() => {
      const pal = $('#menu-palette');
      pal.innerHTML = '';
      Object.values(this.currentTheme.pieces).forEach((c) => pal.appendChild(h('i', { style: { background: c } })));
    });
    const list = $('#mode-list');
    list.innerHTML = '';
    for (const k of MODE_ORDER) {
      const m = MODES[k];
      const best = this.bestScore(k);
      const b = h('button', { class: 'mode-btn' + (cfg.mode === k ? ' active' : ''), role: 'radio', 'aria-checked': cfg.mode === k ? 'true' : 'false', type: 'button' },
        h('span', { class: 'mode-icon' }, m.icon),
        h('span', { class: 'mode-text' }, h('b', null, `${k}. ${m.name}`), h('small', null, m.desc)),
        best ? h('span', { class: 'mode-best' }, 'BEST ' + U.formatNum(best)) : null);
      b.addEventListener('click', () => { cfg.mode = k; this.saveConfig(); this.sound.play('click'); this.renderMenu(); });
      list.appendChild(b);
    }
    const dl = $('#difficulty-list');
    dl.innerHTML = '';
    for (const k of ['easy', 'normal', 'hard', 'custom']) {
      const d = DIFFICULTIES[k];
      const b = h('button', { class: cfg.difficulty === k ? 'active' : '', role: 'radio', 'aria-checked': cfg.difficulty === k ? 'true' : 'false', type: 'button' }, d.name);
      b.addEventListener('click', () => { cfg.difficulty = k; this.saveConfig(); this.sound.play('click'); this.renderMenu(); });
      dl.appendChild(b);
    }
    $('#custom-diff').classList.toggle('hidden', cfg.difficulty !== 'custom');
    $('#custom-target').value = cfg.custom.target;
    $('#custom-level').value = cfg.custom.startLevel;
    this._renderDiffHint();
    const cc = this.collection.count();
    $('#col-count').textContent = cc ? cc : '';
  };
  proto._renderDiffHint = function () {
    const d = IT.Modes.resolveDifficulty(this.config.difficulty, this.config.custom);
    const m = this.config.mode;
    const goal = m === 'C' ? `${d.target}줄을 지우면 이미지 완성` : m === 'E' ? `${d.target}줄마다 새 미스터리 이미지` : `목표 ${d.target}줄 (이미지 완성·챌린지 모드에 적용)`;
    $('#difficulty-hint').textContent = `${goal} · 시작 레벨 ${d.startLevel}`;
  };

  /* =========================================================
   * 이미지 설정 화면
   * ========================================================= */
  proto.renderLibrary = function () {
    const lib = this.library, cfg = this.config;
    if (!this.libSel || !lib.exists(this.libSel)) this.libSel = cfg.mainImage;
    if (!this.previewMode) this.previewMode = cfg.mode;
    $('#preview-mode').value = this.previewMode;
    $$('[data-libtab]').forEach((b) => b.classList.toggle('active', b.dataset.libtab === this.libTab));
    $('#lib-user').classList.toggle('hidden', this.libTab !== 'user');
    $('#lib-samples').classList.toggle('hidden', this.libTab !== 'samples');
    $('#user-count').textContent = lib.user.length || '';

    // 내 이미지
    const ug = $('#user-grid');
    ug.innerHTML = '';
    lib.userList().forEach((r) => ug.appendChild(this._thumbCard(r)));
    $('#user-empty').classList.toggle('hidden', lib.user.length > 0);

    // 샘플
    const tabs = $('#sample-theme-tabs');
    tabs.innerHTML = '';
    IT.Samples.themes.forEach((t) => {
      const b = h('button', { class: 'chip' + (t.key === this.sampleTheme ? ' active' : ''), type: 'button' }, `${t.icon} ${t.name}`);
      b.addEventListener('click', () => { this.sampleTheme = t.key; this.renderLibrary(); });
      tabs.appendChild(b);
    });
    const sg = $('#sample-grid');
    sg.innerHTML = '';
    const theme = IT.Samples.themes.find((t) => t.key === this.sampleTheme) || IT.Samples.themes[0];
    theme.items.forEach((s) => sg.appendChild(this._thumbCard(lib.get(s.id))));

    // 선택 정보
    const sel = lib.get(this.libSel);
    $('#sel-thumb').src = sel.thumb;
    $('#sel-name').textContent = sel.name;
    const adj = lib.getAdjust(sel.id);
    const edited = adj.rot || adj.flip || adj.crop || adj.brightness !== 100 || adj.opacity !== 100;
    $('#sel-meta').textContent = (sel.kind === 'sample' ? `샘플 · ${sel.theme}` : `내 이미지 · ${sel.width}×${sel.height}`) + (edited ? ' · 편집됨' : '');
    $('#btn-rename').classList.toggle('hidden', sel.kind !== 'user');
    $('#btn-delete').classList.toggle('hidden', sel.kind !== 'user');

    // 적용 대상 표시
    const assigned = {
      main: cfg.mainImage,
      bg: cfg.bgImage || cfg.mainImage,
      block: cfg.blockImage || cfg.mainImage,
    };
    $$('.target').forEach((b) => {
      const id = assigned[b.dataset.target];
      const on = id === this.libSel;
      b.classList.toggle('on', on);
      const r = lib.get(id);
      b.querySelector('.assigned').textContent = on ? '✓ 이 이미지 적용 중' : r ? '현재: ' + r.name : '';
    });
    $$('[data-blockmode]').forEach((b) => b.classList.toggle('active', b.dataset.blockmode === cfg.blockMode));
    $('#piece-slot-wrap').classList.toggle('hidden', cfg.blockMode !== 'perPiece');
    this._renderPieceSlots();

    $('#bg-opacity').value = cfg.bgOpacity; $('#bg-opacity-out').textContent = Math.round(cfg.bgOpacity * 100) + '%';
    $('#bg-dim').value = cfg.bgDim; $('#bg-dim-out').textContent = Math.round(cfg.bgDim * 100) + '%';
    $('#block-bg').checked = !!cfg.blockBg;
    this._renderThemeSwatches();
    this.drawLibraryPreview();
  };

  proto._thumbCard = function (r) {
    const cfg = this.config;
    const tags = [];
    if (cfg.mainImage === r.id) tags.push('⭐');
    if ((cfg.bgImage || cfg.mainImage) === r.id) tags.push('🖼️');
    if ((cfg.blockImage || cfg.mainImage) === r.id && cfg.blockMode === 'slice') tags.push('🧩');
    if (cfg.blockMode === 'perPiece' && Object.values(cfg.pieceImages).includes(r.id)) tags.push('🧩');
    if (this.collection.has(r.id)) tags.push('🏆');
    const card = h('button', { class: 'thumb' + (this.libSel === r.id ? ' selected' : ''), type: 'button', title: r.name },
      h('img', { src: r.thumb, alt: r.name, loading: 'lazy', draggable: 'false' }),
      h('span', { class: 'thumb-name' }, r.name),
      tags.length ? h('span', { class: 'thumb-tags' }, tags.join('')) : null);
    card.addEventListener('click', () => { this.libSel = r.id; this.sound.play('click'); this.renderLibrary(); });
    card.addEventListener('dblclick', () => { this.libSel = r.id; this.assignTarget('main'); });
    return card;
  };

  proto._renderPieceSlots = function () {
    const wrap = $('#piece-slots'), cfg = this.config, lib = this.library;
    wrap.innerHTML = '';
    const painter = new IT.Render.BlockPainter(new IT.TextureManager());
    if (this.currentTheme) painter.setColors(this.currentTheme.pieces);
    for (const t of TYPES) {
      const id = cfg.pieceImages[t];
      const r = id ? lib.get(id) : null;
      const cv = h('canvas', { class: 'slot-piece' });
      const slot = h('div', { class: 'slot' + (r ? ' has' : '') },
        h('button', { class: 'slot-main', type: 'button', title: `${t} 블록에 선택한 이미지 지정` },
          r ? h('img', { src: r.thumb, alt: '' }) : h('span', { class: 'slot-empty' }, '대표'),
          cv, h('b', null, t)),
        r ? h('button', { class: 'slot-x', type: 'button', 'aria-label': t + ' 지정 해제' }, '✕') : null);
      slot.querySelector('.slot-main').addEventListener('click', () => {
        cfg.pieceImages[t] = this.libSel; this.saveConfig(); this.sound.play('click'); this.renderLibrary();
      });
      const x = slot.querySelector('.slot-x');
      if (x) x.addEventListener('click', () => { delete cfg.pieceImages[t]; this.saveConfig(); this.renderLibrary(); });
      wrap.appendChild(slot);
      requestAnimationFrame(() => IT.Render.drawPiecePreview(cv, [t], painter, null, { maxCell: 9 }));
    }
  };

  proto._renderThemeSwatches = async function () {
    const wrap = $('#theme-swatches'), id = this.config.mainImage;
    const theme = await this.library.getTheme(id);
    wrap.innerHTML = '';
    const ov = this.library.themeOverrides[id] || {};
    const items = [...TYPES.map((t) => ({ key: t, label: t + ' 블록', color: theme.pieces[t], kind: 'pieces' })),
      { key: 'accent', label: '강조색', color: theme.accent, kind: 'ui' }, { key: 'bg', label: '배경', color: theme.bg, kind: 'ui' }];
    for (const it of items) {
      const inp = h('input', { type: 'color', value: it.color, 'aria-label': it.label });
      const sw = h('label', { class: 'swatch' }, inp, h('i', { style: { background: it.color } }), h('span', null, it.label));
      inp.addEventListener('input', () => { sw.querySelector('i').style.background = inp.value; });
      inp.addEventListener('change', () => {
        const o = { pieces: Object.assign({}, ov.pieces), ui: Object.assign({}, ov.ui) };
        if (it.kind === 'pieces') o.pieces[it.key] = inp.value;
        else if (it.key === 'bg') {
          const c = U.hexToHsl(inp.value);
          Object.assign(o.ui, { bg: inp.value, bg2: U.hslToHex(c.h, c.s, Math.min(0.3, c.l + 0.06)), panel: U.hslToHex(c.h, c.s, Math.min(0.32, c.l + 0.08)), board: U.shade(inp.value, -0.25) });
        } else {
          Object.assign(o.ui, { accent: inp.value, border: U.shade(inp.value, -0.45) });
        }
        // 비슷한 블록 색 자동 보정 안내
        if (it.kind === 'pieces') {
          const all = Object.assign({}, theme.pieces, o.pieces);
          const near = TYPES.filter((t) => t !== it.key && U.deltaE(all[t], inp.value) < 12);
          if (near.length) this.toast(`${near.join(', ')} 블록과 색이 매우 비슷합니다. 구분이 어려울 수 있어요.`, 'warn');
        }
        this.library.setThemeOverride(id, o);
        this.onLibraryChanged();
      });
      wrap.appendChild(sw);
    }
  };

  proto.assignTarget = function (target) {
    const id = this.libSel, cfg = this.config;
    if (!id) return;
    if (target === 'main') cfg.mainImage = id;
    else if (target === 'bg') cfg.bgImage = id === cfg.mainImage ? null : id;
    else if (target === 'block') { cfg.blockImage = id === cfg.mainImage ? null : id; cfg.blockMode = 'slice'; }
    this.saveConfig();
    this.sound.play('click');
    const names = { main: '대표 이미지', bg: '배경 이미지', block: '블록 이미지' };
    this.toast(`‘${this.library.get(id).name}’을(를) ${names[target]}로 지정했습니다.`, 'success', 1800);
    if (target === 'main') this.applyThemeFor(id);
    this.renderLibrary();
  };

  proto.uploadFiles = async function (files) {
    const prog = $('#upload-progress');
    prog.classList.remove('hidden');
    const bar = prog.querySelector('i'), label = prog.querySelector('span');
    const res = await this.library.addFiles(files, (i, n, name) => {
      bar.style.width = (n ? (i / n) * 100 : 100) + '%';
      label.textContent = i < n ? `처리 중 ${i + 1}/${n} · ${name}` : '완료';
    });
    setTimeout(() => prog.classList.add('hidden'), 600);
    if (res.added.length) {
      this.sound.play('upload');
      this.libSel = res.added[res.added.length - 1];
      this.libTab = 'user';
      // 처음 등록한 경우 대표 이미지로 자동 지정
      if (this.library.isSample(this.config.mainImage) && this.library.user.length === res.added.length) {
        this.config.mainImage = res.added[0];
        this.saveConfig();
        this.applyThemeFor(this.config.mainImage);
        this.toast(`${res.added.length}장 등록 완료! 첫 이미지를 대표 이미지로 지정했어요.`, 'success');
      } else {
        this.toast(`${res.added.length}장을 등록했습니다.`, 'success');
      }
    }
    if (res.errors.length) {
      this.sound.play('error');
      IT.UI.modal({
        title: '일부 파일을 등록하지 못했습니다',
        body: h('ul', { class: 'error-list' }, res.errors.map((e) => h('li', null, h('b', null, e.name), ' – ', e.message))),
        actions: [{ label: '확인', cls: 'btn-primary' }],
      });
    }
    this.renderLibrary();
  };

  proto.deleteImage = async function (id) {
    const r = this.library.get(id);
    if (!r || r.kind !== 'user') return;
    if (!(await IT.UI.confirm(`‘${r.name}’ 이미지를 삭제할까요? (완성 컬렉션에 저장된 사본은 유지됩니다)`, { title: '이미지 삭제', ok: '삭제', danger: true }))) return;
    await this.library.remove(id);
    const cfg = this.config;
    if (cfg.mainImage === id) cfg.mainImage = this.library.user[0] ? this.library.user[0].id : IT.Samples.DEFAULT_ID;
    if (cfg.bgImage === id) cfg.bgImage = null;
    if (cfg.blockImage === id) cfg.blockImage = null;
    for (const t in cfg.pieceImages) if (cfg.pieceImages[t] === id) delete cfg.pieceImages[t];
    this.saveConfig();
    this.libSel = cfg.mainImage;
    this.applyThemeFor(cfg.mainImage);
    this.toast('삭제했습니다.');
    this.renderLibrary();
  };

  proto.resetToDefaultImages = async function () {
    if (!(await IT.UI.confirm('대표·배경·블록 이미지 지정과 샘플 편집값, 테마 색상 수정을 기본값으로 되돌릴까요? (등록한 이미지는 삭제되지 않습니다)', { title: '기본 이미지로 초기화', ok: '초기화' }))) return;
    const d = IT.Storage.defaultConfig();
    Object.assign(this.config, { mainImage: d.mainImage, bgImage: null, blockImage: null, pieceImages: {}, blockMode: d.blockMode, bgOpacity: d.bgOpacity, bgDim: d.bgDim, blockBg: d.blockBg });
    this.saveConfig();
    await this.library.resetAllSampleAdjust();
    this.library.themeOverrides = {};
    IT.Storage.saveThemeOverrides({});
    this.libSel = this.config.mainImage;
    this.applyThemeFor(this.config.mainImage);
    this.toast('기본 이미지로 초기화했습니다.', 'success');
    this.renderLibrary();
  };

  proto.onLibraryChanged = function () {
    if (this.screen === 'library') this.renderLibrary();
    if (this.screen === 'menu') this.renderMenu();
    this.applyThemeFor(this.config.mainImage);
  };

  /** 이미지 설정 화면의 적용 결과 미리보기 (실제 렌더러 사용) */
  proto.drawLibraryPreview = async function () {
    if (this.screen !== 'library') return;
    const token = (this._pvToken = (this._pvToken || 0) + 1);
    const cfg = this.config, lib = this.library, mode = this.previewMode || cfg.mode;
    const canvas = $('#preview-canvas');
    const side = $('#preview-side');
    try {
      const mainId = cfg.mainImage;
      const theme = await lib.getTheme(mainId);
      const textures = new IT.TextureManager();
      const painter = new IT.Render.BlockPainter(textures);
      painter.setColors(this.settings.pieceColors === 'classic' && mode !== 'D' ? IT.Pieces.CLASSIC_COLORS : theme.pieces);
      let skin = null, bgImage = null, opacity = cfg.bgOpacity, dim = cfg.bgDim;
      const bgId = lib.resolve(cfg.bgImage || mainId);
      if (mode === 'A') { bgImage = await lib.getAdjusted(bgId, 900); opacity *= lib.getAdjust(bgId).opacity / 100; }
      if (mode === 'B') {
        if (cfg.blockMode === 'perPiece') {
          const imgs = {};
          for (const t of TYPES) imgs[t] = await lib.getAdjusted(lib.resolve(cfg.pieceImages[t] || cfg.blockImage || mainId), 400);
          skin = textures.buildPerPiece(imgs);
        } else skin = textures.buildSlice(await lib.getAdjusted(lib.resolve(cfg.blockImage || mainId), 900));
        if (cfg.blockBg) { bgImage = await lib.getAdjusted(bgId, 900); opacity = Math.min(cfg.bgOpacity, 0.45) * lib.getAdjust(bgId).opacity / 100; dim = Math.max(cfg.bgDim, 0.5); }
      }
      if (token !== this._pvToken) return;
      // 미리보기용 보드 구성
      const e = new IT.Engine({ rng: U.seededRandom(3), skinFor: () => skin });
      e.start();
      const place = [['I', 0, 0], ['O', 4, 0], ['L', 6, 0], ['T', 0, 2], ['Z', 2, 0], ['J', 7, 1], ['S', 4, 0], ['O', 8, 0]];
      for (const [t, x, r] of place) {
        e.piece = { type: t, x, y: 0, r, skin };
        if (e.collides(e.piece, x, 0, r)) continue;
        e.piece.y = e.ghostY();
        e._lock();
      }
      e.piece = { type: 'T', x: 4, y: 7, r: 1, skin };
      const fx = new IT.Effects();
      const rr = new IT.Render.BoardRenderer(canvas, painter, fx);
      const narrow = window.innerWidth < 520;
      const cell = narrow ? U.clamp(Math.floor((window.innerWidth - 80) / 2 / 10), 9, 18) : 18;
      rr.layout(cell * 10, cell * 20);
      rr.setBackground({ image: bgImage, opacity, dim, theme, grid: this.settings.grid, pattern: mode === 'D' });
      rr.render(e, 0, { ghost: true, smooth: false });
      // 오른쪽 이미지 패널
      const img = await lib.getAdjusted(mainId, 600);
      if (token !== this._pvToken) return;
      side.style.width = Math.round(cell * 6.5) + 'px';
      side.style.height = Math.round(cell * 8.6) + 'px';
      const rv = new IT.RevealView(side);
      rv.setTheme(theme);
      if (mode === 'C') { const p = new IT.Modes.RevealProgress(IT.Modes.resolveDifficulty(cfg.difficulty, cfg.custom).target, img.width / img.height, U.seededRandom(5)); p.addLines(Math.ceil(p.target * 0.45)); rv.set(img, p, 'reveal'); }
      else if (mode === 'E') rv.set(null, null, 'mystery');
      else rv.set(img, null, 'preview');
      rv.render(0);
      this.applyTheme(theme);
    } catch (err) {
      console.warn('미리보기 실패', err);
    }
  };

  /* =========================================================
   * 컬렉션
   * ========================================================= */
  proto.renderCollection = function () {
    const items = this.collection.list();
    const grid = $('#collection-grid');
    grid.innerHTML = '';
    $('#col-empty').classList.toggle('hidden', items.length > 0);
    $('#btn-col-clear').classList.toggle('hidden', !items.length);
    const unique = new Set(items.map((x) => x.imageId)).size;
    $('#col-summary').textContent = items.length ? `완성한 이미지 ${items.length}장 (서로 다른 이미지 ${unique}종)` : '';
    for (const it of items) {
      const card = h('button', { class: 'thumb col-card', type: 'button' },
        h('img', { src: it.thumb, alt: it.name, loading: 'lazy' }),
        h('span', { class: 'thumb-name' }, it.name),
        h('span', { class: 'thumb-sub' }, `${U.formatDate(it.completedAt)} · ${MODES[it.mode] ? MODES[it.mode].name : ''}`));
      card.addEventListener('click', () => this.openViewer(it));
      grid.appendChild(card);
    }
  };

  proto.openViewer = function (it) {
    const url = URL.createObjectURL(it.blob);
    const canReplay = this.library.exists(it.imageId);
    IT.UI.modal({
      title: '🏆 ' + it.name,
      className: 'viewer-modal',
      body: h('div', { class: 'viewer' },
        h('img', { src: url, alt: it.name }),
        h('p', { class: 'hint' }, `${U.formatDate(it.completedAt)} 완성 · ${MODES[it.mode] ? MODES[it.mode].title : ''} · ${it.difficulty || ''} · ${U.formatNum(it.score || 0)}점 · ${it.lines || 0}줄`)),
      onClose: () => setTimeout(() => URL.revokeObjectURL(url), 500),
      actions: [
        { label: '🗑 삭제', cls: 'btn-danger', onClick: async () => {
          if (!(await IT.UI.confirm('이 컬렉션 항목을 삭제할까요?', { danger: true, ok: '삭제' }))) return false;
          await this.collection.remove(it.id); this.renderCollection(); return true;
        } },
        { label: '⬇ 저장', onClick: () => {
          const a = h('a', { href: url, download: `${it.name}.jpg` });
          document.body.appendChild(a); a.click(); a.remove();
          return false;
        } },
        canReplay ? { label: '▶ 다시 도전', cls: 'btn-primary', onClick: () => { this.config.mainImage = it.imageId; this.config.mode = 'C'; this.saveConfig(); setTimeout(() => this.startGame(), 50); } } : null,
      ].filter(Boolean),
    });
  };

  /* =========================================================
   * 기록
   * ========================================================= */
  proto.renderRecords = function () {
    const r = IT.Storage.loadRecords();
    const tile = (label, value) => h('div', { class: 'sum-tile' }, h('span', null, label), h('b', null, value));
    const sum = $('#records-summary');
    sum.innerHTML = '';
    sum.append(
      tile('전체 플레이', U.formatNum(r.plays) + '회'),
      tile('누적 제거 줄', U.formatNum(r.lines) + '줄'),
      tile('누적 플레이 시간', U.formatDuration(r.time)),
      tile('완성한 이미지', U.formatNum(r.completed) + '장'),
    );
    const wrap = $('#records-modes');
    wrap.innerHTML = '';
    for (const k of MODE_ORDER) {
      const list = r.best[k] || [];
      const m = MODES[k];
      const table = list.length
        ? h('div', { class: 'table-scroll' }, h('table', { class: 'rec-table' },
          h('thead', null, h('tr', null, ['순위', '점수', '줄', '레벨', '시간', '난이도', '날짜'].map((x) => h('th', null, x)))),
          h('tbody', null, list.slice(0, 5).map((e, i) => h('tr', { class: i === 0 ? 'top' : '' },
            h('td', null, i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : String(i + 1)),
            h('td', null, U.formatNum(e.score)), h('td', null, e.lines), h('td', null, e.level),
            h('td', null, U.formatTime(e.time)), h('td', null, e.difficulty || '-'), h('td', null, U.formatDate(e.date)))))))
        : h('p', { class: 'empty small' }, '아직 기록이 없습니다.');
      wrap.appendChild(h('div', { class: 'card rec-card' },
        h('h3', { class: 'card-title' }, `${m.icon} ${m.title}`, h('small', null, ` · ${r.modePlays[k] || 0}회 플레이`)), table));
    }
  };

  /* =========================================================
   * 설정
   * ========================================================= */
  proto.renderSettings = async function () {
    const s = this.settings, cfg = this.config;
    const body = $('#settings-body');
    body.innerHTML = '';
    const save = () => { this.saveSettings(); this._syncSoundButtons(); };
    const toggle = (label, key, desc, obj = s, onChange) => {
      const inp = h('input', { type: 'checkbox' });
      inp.checked = !!obj[key];
      inp.addEventListener('change', () => { obj[key] = inp.checked; obj === s ? save() : this.saveConfig(); if (onChange) onChange(); });
      return h('label', { class: 'set-row' }, h('span', null, label, desc ? h('small', null, desc) : null), h('span', { class: 'switch' }, inp, h('i')));
    };
    const range = (label, key, min, max, step, fmt, onChange) => {
      const out = h('output', null, fmt(s[key]));
      const inp = h('input', { type: 'range', min, max, step, value: s[key] });
      inp.addEventListener('input', () => { s[key] = Number(inp.value); out.textContent = fmt(s[key]); if (onChange) onChange(); });
      inp.addEventListener('change', save);
      return h('label', { class: 'set-row col' }, h('span', null, label, ' ', out), inp);
    };
    const select = (label, key, options, obj = s) => {
      const sel = h('select', null, options.map(([v, l]) => h('option', { value: v }, l)));
      sel.value = obj[key];
      sel.addEventListener('change', () => { obj[key] = sel.value; obj === s ? save() : this.saveConfig(); });
      return h('label', { class: 'set-row' }, h('span', null, label), sel);
    };
    const section = (title, ...rows) => h('div', { class: 'card set-card' }, h('h3', { class: 'card-title' }, title), ...rows);
    const pct = (v) => Math.round(v * 100) + '%';

    body.append(
      section('🔊 사운드',
        toggle('배경음', 'bgmOn', '게임 중 자체 합성 배경음'),
        range('배경음 음량', 'bgmVolume', 0, 1, 0.05, pct, () => this.sound.applySettings()),
        toggle('효과음', 'sfxOn', '이동·회전·줄 제거 등'),
        range('효과음 음량', 'sfxVolume', 0, 1, 0.05, pct, () => this.sound.applySettings()),
        h('div', { class: 'btn-row' }, h('button', { class: 'btn btn-sm', type: 'button', onclick: () => { this.sound.unlock(); this.sound.play('tetris'); } }, '▶ 효과음 들어보기'))),
      section('🎮 조작',
        range('좌우 자동 반복 시작 (DAS)', 'das', 60, 300, 10, (v) => v + 'ms'),
        range('좌우 반복 간격 (ARR)', 'arr', 0, 100, 5, (v) => (v === 0 ? '즉시' : v + 'ms')),
        range('빠른 낙하 속도', 'softDropSpeed', 10, 100, 5, (v) => `한 칸 ${v}ms`),
        select('터치 버튼', 'touchControls', [['auto', '자동 (터치 기기에서 표시)'], ['on', '항상 표시'], ['off', '숨김']]),
        toggle('진동 피드백', 'vibration', '지원 기기에서 줄 제거·즉시 낙하 시')),
      section('🖥️ 화면',
        toggle('착지 위치 미리보기 (고스트)', 'ghost'),
        toggle('게임판 격자', 'grid'),
        toggle('부드러운 블록 이동', 'smoothMove'),
        select('시각 효과', 'effects', [['full', '풍부하게'], ['reduced', '간단하게 (저사양 기기)']]),
        select('블록 색상', 'pieceColors', [['theme', '이미지 테마 색상'], ['classic', '클래식 색상']])),
      section('🧩 게임',
        toggle('이미지 완성 후 다음 이미지로 자동 진행', 'autoNext'),
        select('랜덤 챌린지 이미지 범위', 'challengePool', [['all', '내 이미지 + 샘플 전체'], ['user', '내 이미지만'], ['samples', '샘플만']], cfg)),
    );

    // 데이터 관리
    let usage = '';
    try {
      if (navigator.storage && navigator.storage.estimate) {
        const est = await navigator.storage.estimate();
        usage = ` · 사용량 약 ${(est.usage / 1024 / 1024).toFixed(1)}MB`;
      }
    } catch (e) { /* 무시 */ }
    const danger = (label, fn) => h('button', { class: 'btn btn-sm btn-danger', type: 'button', onclick: fn }, label);
    body.append(section('💾 데이터 관리',
      h('p', { class: 'hint' }, `등록 이미지 ${this.library.user.length}장 · 컬렉션 ${this.collection.count()}장${usage}. 모든 데이터는 이 브라우저(IndexedDB/LocalStorage)에만 저장됩니다.`),
      h('div', { class: 'btn-row wrap' },
        danger('등록 이미지 전체 삭제', async () => {
          if (!this.library.user.length) return this.toast('등록한 이미지가 없습니다.');
          if (!(await IT.UI.confirm('등록한 모든 이미지를 삭제할까요?', { danger: true, ok: '모두 삭제' }))) return;
          await this.library.removeAllUser(); this._validateConfig(); this.toast('등록 이미지를 모두 삭제했습니다.'); this.renderSettings();
        }),
        danger('컬렉션 전체 삭제', async () => {
          if (!(await IT.UI.confirm('완성 이미지 컬렉션을 모두 삭제할까요?', { danger: true, ok: '모두 삭제' }))) return;
          await this.collection.clear(); this.toast('컬렉션을 비웠습니다.'); this.renderSettings();
        }),
        danger('게임 기록 초기화', async () => {
          if (!(await IT.UI.confirm('최고 점수와 누적 통계를 초기화할까요?', { danger: true, ok: '초기화' }))) return;
          IT.Storage.resetRecords(); this.invalidateBest(); this.toast('기록을 초기화했습니다.');
        }),
        danger('모든 데이터 초기화', async () => {
          if (!(await IT.UI.confirm('등록 이미지, 컬렉션, 기록, 설정을 모두 지우고 처음 상태로 되돌릴까요?', { danger: true, ok: '모두 초기화' }))) return;
          await this.library.removeAllUser(); await this.collection.clear(); IT.Storage.resetAll();
          location.reload();
        }))),
      section('ℹ️ 정보',
        h('p', { class: 'hint' }, 'IMAGE TETRIS v1.0 · 서버 없이 브라우저에서 동작합니다. 이미지·효과음·배경음은 모두 기기 안에서 처리·합성되며 외부로 전송되지 않습니다.')));
  };

  proto.toggleSound = function (kind) {
    const s = this.settings;
    if (kind === 'bgm') {
      s.bgmOn = !s.bgmOn;
      if (this.session && this.session.state === 'playing') { if (s.bgmOn) this.sound.startBgm(); else this.sound.stopBgm(); }
    } else s.sfxOn = !s.sfxOn;
    this.saveSettings();
    this._syncSoundButtons();
  };
  proto._syncSoundButtons = function () {
    const b = $('#btn-bgm'), f = $('#btn-sfx');
    b.classList.toggle('off', !this.settings.bgmOn); b.setAttribute('aria-pressed', String(this.settings.bgmOn));
    f.classList.toggle('off', !this.settings.sfxOn); f.setAttribute('aria-pressed', String(this.settings.sfxOn));
    f.textContent = this.settings.sfxOn ? '🔊' : '🔇';
  };

  /* =========================================================
   * 게임 중 창 (일시정지 / 이미지 완성 / 결과)
   * ========================================================= */
  proto.showPause = function (session) {
    const e = session.engine;
    let resumeOnClose = true;
    const sndRow = h('div', { class: 'btn-row center' },
      h('button', { class: 'btn btn-sm', type: 'button', onclick: (ev) => { this.toggleSound('bgm'); ev.target.textContent = this.settings.bgmOn ? '🎵 배경음 켬' : '🎵 배경음 끔'; } }, this.settings.bgmOn ? '🎵 배경음 켬' : '🎵 배경음 끔'),
      h('button', { class: 'btn btn-sm', type: 'button', onclick: (ev) => { this.toggleSound('sfx'); ev.target.textContent = this.settings.sfxOn ? '🔊 효과음 켬' : '🔇 효과음 끔'; } }, this.settings.sfxOn ? '🔊 효과음 켬' : '🔇 효과음 끔'));
    IT.UI.modal({
      title: 'Ⅱ 일시정지',
      className: 'pause-modal',
      body: h('div', null,
        h('div', { class: 'mini-stats' },
          h('div', null, h('span', null, '점수'), h('b', null, U.formatNum(e.score))),
          h('div', null, h('span', null, '줄'), h('b', null, e.lines)),
          h('div', null, h('span', null, '레벨'), h('b', null, e.level)),
          h('div', null, h('span', null, '시간'), h('b', null, U.formatTime(e.elapsed)))),
        sndRow),
      onClose: () => { if (resumeOnClose && session.state === 'paused') session.resume(); },
      actions: [
        { label: '메인으로', onClick: () => { resumeOnClose = false; setTimeout(() => this.go('menu'), 0); } },
        { label: '다시 시작', onClick: () => { resumeOnClose = false; setTimeout(() => this.startGame(), 0); } },
        { label: '▶ 계속하기', cls: 'btn-primary', close: false, onClick: () => { session.resume(); } },
      ],
    });
  };

  proto.showStageComplete = function (session, entry) {
    const img = session.stageImage;
    const cv = h('canvas', { class: 'stage-img' });
    const W = Math.min(420, window.innerWidth - 80), H = Math.min(380, window.innerHeight * 0.45);
    const r = U.containRect(img.width, img.height, W, H);
    const dpr = Math.min(2, devicePixelRatio || 1);
    cv.width = r.w * dpr; cv.height = r.h * dpr; cv.style.width = r.w + 'px'; cv.style.height = r.h + 'px';
    cv.getContext('2d').drawImage(img, 0, 0, cv.width, cv.height);
    const auto = this.settings.autoNext;
    const countEl = h('p', { class: 'hint center' }, auto ? '5초 후 다음 이미지로 자동 진행합니다.' : '');
    let timer = null, left = 5;
    const m = IT.UI.modal({
      title: '🎉 이미지 완성!',
      className: 'stage-modal',
      dismissible: false,
      body: h('div', { class: 'stage-body' }, cv,
        h('p', { class: 'stage-name' }, entry.name),
        h('p', { class: 'hint center' }, `STAGE ${session.stageNo} 클리어 · ${U.formatNum(session.engine.score)}점 · ${session.engine.lines}줄 · 컬렉션에 저장됨`),
        countEl),
      onClose: () => clearInterval(timer),
      actions: [
        { label: '결과 보기', onClick: () => { clearInterval(timer); setTimeout(() => session.finish(), 0); } },
        { label: '다음 이미지로 계속 ▶', cls: 'btn-primary', close: false, onClick: () => { clearInterval(timer); session.nextStage(); } },
      ],
    });
    if (auto) {
      timer = setInterval(() => {
        left--;
        countEl.textContent = `${left}초 후 다음 이미지로 자동 진행합니다.`;
        if (left <= 0) { clearInterval(timer); if (session.state === 'stage') session.nextStage(); }
      }, 1000);
    }
    return m;
  };

  proto.showResults = function (session, res) {
    this.invalidateBest();
    const imgs = res.images.length
      ? h('div', { class: 'result-images' }, res.images.map((x) => h('figure', null, x.thumb ? h('img', { src: x.thumb, alt: x.name }) : null, h('figcaption', null, x.name))))
      : h('p', { class: 'hint center' }, session.mode === 'C' || session.mode === 'E' ? '이번 판에는 완성한 이미지가 없어요.' : '');
    const row = (label, value) => h('div', { class: 'res-row' }, h('span', null, label), h('b', null, value));
    const canNext = session.mode === 'C' || session.mode === 'E';
    IT.UI.modal({
      title: res.newBest ? '🏆 최고 점수 갱신!' : '게임 종료',
      className: 'result-modal' + (res.newBest ? ' best' : ''),
      dismissible: false,
      body: h('div', null,
        h('div', { class: 'res-score' }, h('span', null, '최종 점수'), h('b', null, U.formatNum(res.score)),
          res.newBest ? h('em', { class: 'new-best' }, 'NEW BEST') : h('small', null, `최고 기록 ${U.formatNum(Math.max(res.prevBest, res.score))}`)),
        h('div', { class: 'res-grid' },
          row('모드', res.modeName), row('난이도', res.difficulty),
          row('제거한 줄', res.lines + '줄'), row('최고 콤보', res.maxCombo + '콤보'),
          row('도달 레벨', 'Lv.' + res.level), row('플레이 시간', U.formatTime(res.time)),
          row('테트리스', res.stats.tetrises + '회'), row('T-Spin', res.stats.tspins + '회')),
        h('h4', { class: 'sub-title' }, `완성한 이미지 ${res.images.length}장`), imgs),
      actions: [
        { label: '메인으로', onClick: () => setTimeout(() => this.go('menu'), 0) },
        canNext ? { label: '다음 이미지 도전', onClick: () => {
          if (session.mode === 'C') { this.config.mainImage = this.nextImageId(session.currentId); this.saveConfig(); }
          setTimeout(() => this.startGame(), 0);
        } } : null,
        { label: '↻ 다시 시작', cls: 'btn-primary', onClick: () => setTimeout(() => this.startGame(), 0) },
      ].filter(Boolean),
    });
  };

  // main.js 의 App 클래스에 합쳐집니다.
  IT._screenProto = proto;
})();
