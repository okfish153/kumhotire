/* IMAGE TETRIS – 이미지 편집기 (비파괴 편집)
 * 확대/축소, 자르기(비율 선택), 위치 이동(드래그), 90° 회전, 좌우 반전, 밝기, 투명도, 실시간 미리보기
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const { h } = IT.UI;
  const U = IT.util;
  const P = IT.ImageProc;

  const ASPECTS = [
    { key: 'free', label: '자유', v: null },
    { key: 'orig', label: '원본', v: 'orig' },
    { key: '1:2', label: '게임판 1:2', v: 0.5 },
    { key: '3:4', label: '3:4', v: 3 / 4 },
    { key: '1:1', label: '1:1', v: 1 },
    { key: '4:3', label: '4:3', v: 4 / 3 },
    { key: '16:9', label: '16:9', v: 16 / 9 },
    { key: '9:16', label: '9:16', v: 9 / 16 },
  ];

  async function openEditor(app, id) {
    const lib = app.library;
    const rec = lib.get(id);
    if (!rec) return;
    let base;
    try { base = await lib.getBase(id); } catch (e) { IT.UI.toast('이미지를 열 수 없습니다: ' + e.message, 'error'); return; }
    const init = lib.getAdjust(id);
    const st = {
      rot: init.rot, flip: init.flip, brightness: init.brightness, opacity: init.opacity,
      crop: init.crop ? Object.assign({}, init.crop) : { x: 0, y: 0, w: 1, h: 1 },
      aspect: null,
    };
    let rotated = null; // 회전·반전만 적용한 표시용 이미지
    const rebuildRotated = () => { rotated = P.applyAdjust(base, { rot: st.rot, flip: st.flip }, 1000); };
    rebuildRotated();

    const canvas = h('canvas', { class: 'ed-canvas', 'aria-label': '자르기 영역' });
    const preview = h('canvas', { class: 'ed-preview' });
    const zoom = h('input', { type: 'range', min: '1', max: '5', step: '0.01', value: '1' });
    const bright = h('input', { type: 'range', min: '40', max: '160', step: '1', value: st.brightness });
    const opac = h('input', { type: 'range', min: '10', max: '100', step: '1', value: st.opacity });
    const brightOut = h('output', null, st.brightness + '%');
    const opacOut = h('output', null, st.opacity + '%');
    const sizeOut = h('small', { class: 'ed-size' });
    const aspectBtns = ASPECTS.map((a) => h('button', { class: 'chip' + (a.key === 'free' ? ' active' : ''), type: 'button', 'data-k': a.key }, a.label));

    const body = h('div', { class: 'editor' },
      h('div', { class: 'ed-stage' }, canvas, h('p', { class: 'hint' }, '사각형을 끌어 위치를 옮기고, 모서리를 끌어 크기를 조절하세요. (PC: 마우스 휠로 확대/축소)')),
      h('div', { class: 'ed-side' },
        h('div', { class: 'ed-group' }, h('h5', null, '자르기 비율'), h('div', { class: 'chips' }, aspectBtns)),
        h('div', { class: 'ed-group' }, h('h5', null, '확대 / 축소'), zoom),
        h('div', { class: 'ed-group' }, h('h5', null, '방향'),
          h('div', { class: 'btn-row' },
            h('button', { class: 'btn btn-sm', type: 'button', onclick: () => rotate(-1) }, '⟲ 왼쪽 90°'),
            h('button', { class: 'btn btn-sm', type: 'button', onclick: () => rotate(1) }, '⟳ 오른쪽 90°'),
            h('button', { class: 'btn btn-sm', type: 'button', onclick: () => { st.flip = !st.flip; rebuildRotated(); st.crop = { x: 1 - st.crop.x - st.crop.w, y: st.crop.y, w: st.crop.w, h: st.crop.h }; redraw(); } }, '⇋ 좌우 반전'))),
        h('div', { class: 'ed-group' }, h('h5', null, '밝기 ', brightOut), bright),
        h('div', { class: 'ed-group' }, h('h5', null, '투명도 ', opacOut, h('small', null, ' (배경으로 쓸 때 적용)')), opac),
        h('div', { class: 'ed-group' }, h('h5', null, '미리보기 ', sizeOut), preview),
        h('button', { class: 'btn btn-sm', type: 'button', onclick: resetAll }, '↺ 편집 초기화')));

    let cleanup = null;
    IT.UI.modal({
      title: '이미지 편집 – ' + rec.name,
      onClose: () => { if (cleanup) cleanup(); },
      className: 'editor-modal',
      body,
      dismissible: false,
      actions: [
        { label: '취소' },
        {
          label: '저장', cls: 'btn-primary', onClick: async () => {
            await lib.setAdjust(id, { rot: st.rot, flip: st.flip, crop: st.crop, brightness: st.brightness, opacity: st.opacity });
            IT.UI.toast('편집 내용을 저장했습니다.', 'success');
            app.onLibraryChanged();
          },
        },
      ],
    });

    /* ---------- 좌표 변환 ---------- */
    let disp = null; // 표시 영역
    const rw = () => rotated.width, rh = () => rotated.height;
    function layout() {
      const dpr = Math.min(2, globalThis.devicePixelRatio || 1);
      const cw = canvas.clientWidth || 400, ch = canvas.clientHeight || 400;
      canvas.width = Math.round(cw * dpr); canvas.height = Math.round(ch * dpr);
      const r = U.containRect(rw(), rh(), cw - 24, ch - 24);
      disp = { x: r.x + 12, y: r.y + 12, w: r.w, h: r.h, dpr };
    }
    const toScreen = (c) => ({ x: disp.x + c.x * disp.w, y: disp.y + c.y * disp.h, w: c.w * disp.w, h: c.h * disp.h });

    function aspectValue() {
      if (st.aspect === 'orig') return base.width / base.height;
      return st.aspect;
    }
    /** 주어진 비율(가로/세로, 픽셀 기준)에서 가능한 최대 자르기 크기 (정규화) */
    function maxSize(a) {
      if (!a) return { w: 1, h: 1 };
      const R = rw() / rh();
      return a > R ? { w: 1, h: R / a } : { w: a / R, h: 1 };
    }
    function clampCrop() {
      const c = st.crop;
      c.w = U.clamp(c.w, 0.03, 1); c.h = U.clamp(c.h, 0.03, 1);
      c.x = U.clamp(c.x, 0, 1 - c.w); c.y = U.clamp(c.y, 0, 1 - c.h);
    }
    function applyAspect(keepCenter = true) {
      const a = aspectValue();
      if (!a) { syncZoom(); return; }
      const mx = maxSize(a);
      const z = Number(zoom.value) || 1;
      const cx = st.crop.x + st.crop.w / 2, cy = st.crop.y + st.crop.h / 2;
      st.crop.w = mx.w / z; st.crop.h = mx.h / z;
      if (keepCenter) { st.crop.x = cx - st.crop.w / 2; st.crop.y = cy - st.crop.h / 2; }
      clampCrop();
    }
    function syncZoom() {
      const a = aspectValue() || (st.crop.w * rw()) / (st.crop.h * rh());
      const mx = maxSize(a);
      zoom.value = U.clamp(Math.min(mx.w / st.crop.w, mx.h / st.crop.h), 1, 5);
    }

    /* ---------- 그리기 ---------- */
    let raf = 0;
    function redraw() {
      if (raf) return;
      raf = requestAnimationFrame(() => { raf = 0; draw(); drawPreview(); });
    }
    function draw() {
      if (!disp) layout();
      const ctx = canvas.getContext('2d');
      ctx.setTransform(disp.dpr, 0, 0, disp.dpr, 0, 0);
      const cw = canvas.width / disp.dpr, ch = canvas.height / disp.dpr;
      ctx.clearRect(0, 0, cw, ch);
      ctx.save();
      if ('filter' in ctx) ctx.filter = `brightness(${st.brightness}%)`;
      ctx.drawImage(rotated, disp.x, disp.y, disp.w, disp.h);
      ctx.restore();
      const s = toScreen(st.crop);
      ctx.fillStyle = 'rgba(8,8,20,.62)';
      ctx.beginPath();
      ctx.rect(disp.x, disp.y, disp.w, disp.h);
      ctx.rect(s.x, s.y, s.w, s.h);
      ctx.fill('evenodd');
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 2;
      ctx.strokeRect(s.x, s.y, s.w, s.h);
      ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 1; i < 3; i++) {
        ctx.moveTo(s.x + (s.w * i) / 3, s.y); ctx.lineTo(s.x + (s.w * i) / 3, s.y + s.h);
        ctx.moveTo(s.x, s.y + (s.h * i) / 3); ctx.lineTo(s.x + s.w, s.y + (s.h * i) / 3);
      }
      ctx.stroke();
      ctx.fillStyle = '#fff';
      for (const [hx, hy] of corners(s)) { ctx.beginPath(); ctx.arc(hx, hy, 7, 0, Math.PI * 2); ctx.fill(); }
      sizeOut.textContent = `${Math.round(st.crop.w * (st.rot % 2 ? base.height : base.width))} × ${Math.round(st.crop.h * (st.rot % 2 ? base.width : base.height))}px`;
    }
    function drawPreview() {
      const out = P.applyAdjust(base, { rot: st.rot, flip: st.flip, crop: st.crop, brightness: st.brightness }, 360);
      const W = 240, H = 160;
      const dpr = Math.min(2, globalThis.devicePixelRatio || 1);
      preview.width = W * dpr; preview.height = H * dpr;
      const ctx = preview.getContext('2d');
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      // 투명도 확인용 체크무늬
      for (let y = 0; y < H; y += 10) for (let x = 0; x < W; x += 10) { ctx.fillStyle = ((x + y) / 10) % 2 ? '#2a2a40' : '#1c1c2e'; ctx.fillRect(x, y, 10, 10); }
      const r = U.containRect(out.width, out.height, W, H);
      ctx.globalAlpha = st.opacity / 100;
      ctx.drawImage(out, r.x, r.y, r.w, r.h);
      ctx.globalAlpha = 1;
    }
    const corners = (s) => [[s.x, s.y], [s.x + s.w, s.y], [s.x, s.y + s.h], [s.x + s.w, s.y + s.h]];

    /* ---------- 조작 ---------- */
    function rotate(d) {
      st.rot = (st.rot + d + 4) % 4;
      rebuildRotated();
      layout();
      st.crop = { x: 0, y: 0, w: 1, h: 1 };
      zoom.value = 1;
      applyAspect();
      redraw();
    }
    function resetAll() {
      st.rot = 0; st.flip = false; st.brightness = 100; st.opacity = 100; st.crop = { x: 0, y: 0, w: 1, h: 1 }; st.aspect = null;
      bright.value = 100; opac.value = 100; zoom.value = 1; brightOut.textContent = '100%'; opacOut.textContent = '100%';
      aspectBtns.forEach((b) => b.classList.toggle('active', b.dataset.k === 'free'));
      rebuildRotated(); layout(); redraw();
    }
    aspectBtns.forEach((b) => b.addEventListener('click', () => {
      aspectBtns.forEach((x) => x.classList.toggle('active', x === b));
      st.aspect = ASPECTS.find((a) => a.key === b.dataset.k).v;
      applyAspect();
      redraw();
    }));
    zoom.addEventListener('input', () => {
      const z = Number(zoom.value);
      const a = aspectValue() || (st.crop.w * rw()) / (st.crop.h * rh());
      const mx = maxSize(a);
      const cx = st.crop.x + st.crop.w / 2, cy = st.crop.y + st.crop.h / 2;
      st.crop.w = mx.w / z; st.crop.h = mx.h / z;
      st.crop.x = cx - st.crop.w / 2; st.crop.y = cy - st.crop.h / 2;
      clampCrop();
      redraw();
    });
    bright.addEventListener('input', () => { st.brightness = Number(bright.value); brightOut.textContent = st.brightness + '%'; redraw(); });
    opac.addEventListener('input', () => { st.opacity = Number(opac.value); opacOut.textContent = st.opacity + '%'; redraw(); });

    let drag = null;
    canvas.addEventListener('pointerdown', (e) => {
      if (!disp) return;
      const rect = canvas.getBoundingClientRect();
      const px = e.clientX - rect.left, py = e.clientY - rect.top;
      const s = toScreen(st.crop);
      const hitR = e.pointerType === 'mouse' ? 12 : 22;
      const ci = corners(s).findIndex(([hx, hy]) => Math.hypot(px - hx, py - hy) < hitR);
      if (ci >= 0) drag = { type: 'resize', corner: ci, start: Object.assign({}, st.crop) };
      else if (px >= s.x && px <= s.x + s.w && py >= s.y && py <= s.y + s.h) drag = { type: 'move', sx: px, sy: py, start: Object.assign({}, st.crop) };
      else return;
      e.preventDefault();
      canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener('pointermove', (e) => {
      const rect = canvas.getBoundingClientRect();
      const px = e.clientX - rect.left, py = e.clientY - rect.top;
      if (!drag) {
        if (!disp) return;
        const s = toScreen(st.crop);
        const onCorner = corners(s).some(([hx, hy]) => Math.hypot(px - hx, py - hy) < 12);
        canvas.style.cursor = onCorner ? 'nwse-resize' : px >= s.x && px <= s.x + s.w && py >= s.y && py <= s.y + s.h ? 'move' : 'default';
        return;
      }
      const nx = (px - disp.x) / disp.w, ny = (py - disp.y) / disp.h;
      const c = st.crop, s0 = drag.start;
      if (drag.type === 'move') {
        c.x = s0.x + (px - drag.sx) / disp.w; c.y = s0.y + (py - drag.sy) / disp.h;
        c.w = s0.w; c.h = s0.h;
      } else {
        // 반대쪽 모서리 고정
        const ax = drag.corner % 2 === 0 ? s0.x + s0.w : s0.x;
        const ay = drag.corner < 2 ? s0.y + s0.h : s0.y;
        let w = Math.abs(U.clamp(nx, 0, 1) - ax), hh = Math.abs(U.clamp(ny, 0, 1) - ay);
        const a = aspectValue();
        if (a) {
          const ratio = (a * rh()) / rw(); // 정규화 w/h
          if (w / hh > ratio) w = hh * ratio; else hh = w / ratio;
        }
        w = Math.max(w, 0.04); hh = Math.max(hh, 0.04);
        c.w = w; c.h = hh;
        c.x = drag.corner % 2 === 0 ? ax - w : ax;
        c.y = drag.corner < 2 ? ay - hh : ay;
      }
      clampCrop();
      if (drag.type === 'resize') syncZoom();
      redraw();
    });
    const endDrag = () => { drag = null; };
    canvas.addEventListener('pointerup', endDrag);
    canvas.addEventListener('pointercancel', endDrag);
    canvas.addEventListener('wheel', (e) => {
      e.preventDefault();
      zoom.value = U.clamp(Number(zoom.value) * (e.deltaY < 0 ? 1.08 : 1 / 1.08), 1, 5);
      zoom.dispatchEvent(new Event('input'));
    }, { passive: false });

    const ro = new ResizeObserver(() => { layout(); redraw(); });
    ro.observe(canvas);
    cleanup = () => ro.disconnect();
    requestAnimationFrame(() => { layout(); syncZoom(); redraw(); });
  }

  IT.Editor = { open: openEditor };
})();
