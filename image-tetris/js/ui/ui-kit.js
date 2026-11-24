/* IMAGE TETRIS – UI 도우미 (모달, 토스트, 확인/입력 창) */
(function () {
  'use strict';
  const IT = (globalThis.IT = globalThis.IT || {});

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  function h(tag, attrs, ...children) {
    const el = document.createElement(tag);
    if (attrs) {
      for (const k in attrs) {
        const v = attrs[k];
        if (v == null || v === false) continue;
        if (k === 'class') el.className = v;
        else if (k === 'html') el.innerHTML = v;
        else if (k === 'text') el.textContent = v;
        else if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
        else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
        else el.setAttribute(k, v === true ? '' : v);
      }
    }
    for (const c of children.flat()) {
      if (c == null || c === false) continue;
      el.appendChild(typeof c === 'string' || typeof c === 'number' ? document.createTextNode(String(c)) : c);
    }
    return el;
  }

  let stack = [];

  /**
   * modal({ title, body: Node|string, actions: [{label, cls, onClick, close=true}], dismissible, className, onClose })
   */
  function modal(opts) {
    const root = $('#modal-root');
    const body = typeof opts.body === 'string' ? h('div', { html: opts.body }) : opts.body;
    const actions = (opts.actions || []).map((a) => {
      const b = h('button', { class: 'btn ' + (a.cls || ''), type: 'button' }, a.label);
      b.addEventListener('click', async () => {
        if (a.onClick) { const r = await a.onClick(b); if (r === false) return; }
        if (a.close !== false) close();
      });
      return b;
    });
    const box = h('div', { class: 'modal ' + (opts.className || ''), role: 'dialog', 'aria-modal': 'true', 'aria-label': opts.title || '' },
      opts.title ? h('h3', { class: 'modal-title' }, opts.title) : null,
      h('div', { class: 'modal-body' }, body),
      actions.length ? h('div', { class: 'modal-actions' }, actions) : null);
    const back = h('div', { class: 'modal-back' }, box);
    let closed = false;
    function close() {
      if (closed) return;
      closed = true;
      back.classList.add('closing');
      stack = stack.filter((m) => m !== api);
      setTimeout(() => back.remove(), 180);
      document.removeEventListener('keydown', onKey, true);
      if (opts.onClose) opts.onClose();
    }
    function onKey(e) {
      if (stack[stack.length - 1] !== api) return;
      if (e.key === 'Escape' && opts.dismissible !== false) { e.preventDefault(); e.stopPropagation(); close(); }
    }
    if (opts.dismissible !== false) back.addEventListener('pointerdown', (e) => { if (e.target === back) close(); });
    document.addEventListener('keydown', onKey, true);
    root.appendChild(back);
    requestAnimationFrame(() => back.classList.add('open'));
    const api = { el: box, back, close, actions };
    stack.push(api);
    const focusEl = actions.find((b) => b.classList.contains('btn-primary')) || actions[0];
    if (focusEl && opts.autoFocus !== false) setTimeout(() => focusEl.focus({ preventScroll: true }), 30);
    return api;
  }
  function closeTop() { const m = stack[stack.length - 1]; if (m) m.close(); }
  function closeAll() { stack.slice().forEach((m) => m.close()); }
  function hasModal() { return stack.length > 0; }

  function confirm(message, { title = '확인', ok = '확인', cancel = '취소', danger = false } = {}) {
    return new Promise((resolve) => {
      let result = false;
      modal({
        title, body: h('p', { class: 'confirm-text' }, message),
        actions: [
          { label: cancel, onClick: () => { result = false; } },
          { label: ok, cls: danger ? 'btn-danger' : 'btn-primary', onClick: () => { result = true; } },
        ],
        onClose: () => resolve(result),
      });
    });
  }

  function prompt(message, value, { title = '입력', ok = '확인', maxLength = 40 } = {}) {
    return new Promise((resolve) => {
      let result = null;
      const input = h('input', { type: 'text', class: 'text-input', value: value || '', maxlength: maxLength });
      const m = modal({
        title,
        body: h('div', null, h('p', null, message), input),
        actions: [{ label: '취소' }, { label: ok, cls: 'btn-primary', onClick: () => { result = input.value.trim(); } }],
        onClose: () => resolve(result),
        autoFocus: false,
      });
      input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { result = input.value.trim(); m.close(); } });
      setTimeout(() => { input.focus(); input.select(); }, 40);
    });
  }

  function toast(msg, type = 'info', ms = 2600) {
    const root = $('#toast-root');
    const t = h('div', { class: 'toast toast-' + type }, msg);
    root.appendChild(t);
    requestAnimationFrame(() => t.classList.add('show'));
    setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 300); }, ms);
  }

  IT.UI = { $, $$, h, modal, closeTop, closeAll, hasModal, confirm, prompt, toast };
})();
