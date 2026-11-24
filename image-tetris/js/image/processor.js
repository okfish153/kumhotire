/* IMAGE TETRIS – 이미지 처리 (브라우저 내부에서만 처리, 외부 전송 없음)
 * - 파일 검증 / 디코딩 / 고해상도 최적화(축소) / 썸네일
 * - 비파괴 편집값(회전·반전·자르기·밝기) 적용
 */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});
  const U = IT.util;

  const ACCEPT_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/pjpeg'];
  const ACCEPT_EXT = /\.(jpe?g|png|webp)$/i;
  const MAX_BYTES = 50 * 1024 * 1024;
  const MAX_SIDE = 2048; // 저장 최대 해상도 (긴 변)
  const THUMB = 240;

  const DEFAULT_ADJUST = { rot: 0, flip: false, crop: null, brightness: 100, opacity: 100 };

  function normalizeAdjust(a) {
    const o = Object.assign({}, DEFAULT_ADJUST, a || {});
    o.rot = ((Math.round(o.rot) % 4) + 4) % 4;
    o.brightness = U.clamp(Number(o.brightness) || 100, 20, 200);
    o.opacity = U.clamp(Number(o.opacity) || 100, 5, 100);
    if (o.crop) {
      const c = o.crop;
      const w = U.clamp(c.w, 0.02, 1), h = U.clamp(c.h, 0.02, 1);
      o.crop = { x: U.clamp(c.x, 0, 1 - w), y: U.clamp(c.y, 0, 1 - h), w, h };
      if (o.crop.x === 0 && o.crop.y === 0 && w === 1 && h === 1) o.crop = null;
    }
    return o;
  }

  function validateFile(file) {
    if (!file) return '파일이 없습니다.';
    const typeOk = ACCEPT_TYPES.includes((file.type || '').toLowerCase());
    const extOk = ACCEPT_EXT.test(file.name || '');
    if (!typeOk && !extOk) return '지원하지 않는 형식입니다 (JPG, JPEG, PNG, WebP만 가능).';
    if (file.type && !typeOk && !/^image\//.test(file.type)) return '이미지 파일이 아닙니다.';
    if (file.size === 0) return '빈 파일입니다.';
    if (file.size > MAX_BYTES) return `파일이 너무 큽니다 (최대 ${MAX_BYTES / 1024 / 1024}MB).`;
    return null;
  }

  /** Blob/URL → HTMLImageElement (EXIF 방향은 브라우저가 자동 적용) */
  function loadImage(src, timeoutMs = 20000) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      let url = null;
      if (src instanceof Blob) { url = URL.createObjectURL(src); src = url; }
      const timer = setTimeout(() => { cleanup(); reject(new Error('이미지 로딩 시간 초과')); }, timeoutMs);
      const cleanup = () => { clearTimeout(timer); if (url) setTimeout(() => URL.revokeObjectURL(url), 0); };
      img.onload = () => {
        if (!img.naturalWidth || !img.naturalHeight) { cleanup(); reject(new Error('이미지 크기를 읽을 수 없습니다.')); return; }
        const done = () => { cleanup(); resolve(img); };
        if (img.decode) img.decode().then(done, done); else done();
      };
      img.onerror = () => { cleanup(); reject(new Error('손상되었거나 읽을 수 없는 이미지입니다.')); };
      img.decoding = 'async';
      img.src = src;
    });
  }

  /** 품질을 유지하며 단계적으로 축소 */
  function downscale(src, maxSide) {
    const sw = src.naturalWidth || src.width, sh = src.naturalHeight || src.height;
    const scale = Math.min(1, maxSide / Math.max(sw, sh));
    const tw = Math.max(1, Math.round(sw * scale)), th = Math.max(1, Math.round(sh * scale));
    let cur = src, cw = sw, ch = sh;
    while (cw / 2 >= tw * 1.01 && ch / 2 >= th * 1.01) {
      cw = Math.round(cw / 2); ch = Math.round(ch / 2);
      const c = U.createCanvas(cw, ch);
      const x = c.getContext('2d');
      x.imageSmoothingQuality = 'high';
      x.drawImage(cur, 0, 0, cw, ch);
      cur = c;
    }
    const out = U.createCanvas(tw, th);
    const ctx = out.getContext('2d');
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(cur, 0, 0, tw, th);
    return out;
  }

  function hasAlpha(canvas) {
    const s = 48;
    const c = U.createCanvas(s, s);
    const ctx = c.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(canvas, 0, 0, s, s);
    const d = ctx.getImageData(0, 0, s, s).data;
    for (let i = 3; i < d.length; i += 4) if (d[i] < 250) return true;
    return false;
  }

  function canvasToBlob(canvas, type, quality) {
    return new Promise((resolve, reject) => {
      if (canvas.toBlob) {
        canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('이미지 인코딩 실패'))), type, quality);
      } else {
        try {
          const url = canvas.toDataURL(type, quality);
          fetch(url).then((r) => r.blob()).then(resolve, reject);
        } catch (e) { reject(e); }
      }
    });
  }

  function thumbDataURL(canvas, size = THUMB, alpha = false) {
    const s = Math.min(1, size / Math.max(canvas.width, canvas.height));
    const c = downscale(canvas, Math.max(canvas.width, canvas.height) * s);
    return alpha ? c.toDataURL('image/png') : c.toDataURL('image/jpeg', 0.82);
  }

  /** 업로드 파일 → 저장용 데이터 */
  async function processFile(file) {
    const err = validateFile(file);
    if (err) throw new Error(err);
    const img = await loadImage(file);
    const big = Math.max(img.naturalWidth, img.naturalHeight) > MAX_SIDE;
    const canvas = downscale(img, MAX_SIDE);
    const alpha = /png|webp/i.test(file.type || file.name) && hasAlpha(canvas);
    let blob;
    if (!big && file.size < 3 * 1024 * 1024 && /jpe?g|png|webp/i.test(file.type)) {
      blob = file; // 원본 그대로 보존 (작은 이미지)
    } else {
      blob = await canvasToBlob(canvas, alpha ? 'image/png' : 'image/jpeg', 0.92);
    }
    return {
      blob,
      width: canvas.width,
      height: canvas.height,
      originalWidth: img.naturalWidth,
      originalHeight: img.naturalHeight,
      alpha,
      thumb: thumbDataURL(canvas, THUMB, alpha),
      optimized: blob !== file,
    };
  }

  /** 편집값 적용: 반전 → 회전 → 자르기 → 밝기 (투명도는 그릴 때 적용) */
  function applyAdjust(base, adjust, maxSide = 1600) {
    const a = normalizeAdjust(adjust);
    const W = base.width, H = base.height;
    const odd = a.rot % 2 === 1;
    const rw = odd ? H : W, rh = odd ? W : H;
    const c = a.crop || { x: 0, y: 0, w: 1, h: 1 };
    const cw = c.w * rw, ch = c.h * rh;
    const scale = Math.min(1, maxSide / Math.max(cw, ch));
    const out = U.createCanvas(cw * scale, ch * scale);
    const ctx = out.getContext('2d', { willReadFrequently: a.brightness !== 100 });
    ctx.imageSmoothingQuality = 'high';
    ctx.scale(out.width / cw, out.height / ch);
    ctx.translate(-c.x * rw, -c.y * rh);
    ctx.translate(rw / 2, rh / 2);
    if (a.flip) ctx.scale(-1, 1);
    ctx.rotate((a.rot * Math.PI) / 2);
    ctx.drawImage(base, -W / 2, -H / 2);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    if (a.brightness !== 100) {
      const k = a.brightness / 100;
      const id = ctx.getImageData(0, 0, out.width, out.height);
      const d = id.data;
      for (let i = 0; i < d.length; i += 4) {
        d[i] = Math.min(255, d[i] * k);
        d[i + 1] = Math.min(255, d[i + 1] * k);
        d[i + 2] = Math.min(255, d[i + 2] * k);
      }
      ctx.putImageData(id, 0, 0);
    }
    return out;
  }

  /** 편집 화면용: 회전·반전만 적용한 이미지 크기 */
  function rotatedSize(w, h, rot) { return rot % 2 ? { w: h, h: w } : { w, h }; }

  IT.ImageProc = {
    ACCEPT_TYPES, MAX_SIDE, MAX_BYTES, DEFAULT_ADJUST,
    normalizeAdjust, validateFile, loadImage, downscale, hasAlpha, canvasToBlob,
    thumbDataURL, processFile, applyAdjust, rotatedSize,
  };
})();
