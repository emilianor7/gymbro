// Mini helpers compartidos.

// crear elemento desde HTML string
export function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

// escape HTML para evitar inyeccion en interpolaciones
export function esc(s) {
  if (s === null || s === undefined) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// debounce simple
export function debounce(fn, ms = 300) {
  let t;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

// toasts
export function toast(message, type = "info", duration = 3000) {
  const container = document.getElementById("toast-container");
  const node = el(`<div class="toast ${type}">${esc(message)}</div>`);
  container.appendChild(node);
  setTimeout(() => {
    node.style.animation = "toast-in 0.2s ease reverse";
    setTimeout(() => node.remove(), 200);
  }, duration);
}

// bottom sheet
export function sheet({ title, body, onClose }) {
  const overlay = el(`
    <div class="sheet-overlay">
      <div class="sheet">
        <div class="sheet-header">
          <h2>${esc(title)}</h2>
          <button class="icon-btn" data-close>${icons.close}</button>
        </div>
        <div class="sheet-body"></div>
      </div>
    </div>
  `);
  const bodyEl = overlay.querySelector(".sheet-body");
  if (typeof body === "string") bodyEl.innerHTML = body;
  else if (body) bodyEl.appendChild(body);

  document.body.appendChild(overlay);
  document.body.style.overflow = "hidden";

  const close = () => {
    document.body.style.overflow = "";
    overlay.remove();
    if (onClose) onClose();
  };

  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) close();
  });
  overlay.querySelector("[data-close]").addEventListener("click", close);

  return { close, body: bodyEl };
}

// confirm minimal
export function confirm(message) {
  return new Promise((resolve) => {
    const node = el(`
      <div class="sheet-overlay">
        <div class="sheet" style="padding:20px 18px;">
          <p style="font-size:15px;margin-bottom:18px;">${esc(message)}</p>
          <div style="display:flex;gap:10px;">
            <button class="btn btn-block" data-no>Cancelar</button>
            <button class="btn btn-danger btn-block" data-yes>Confirmar</button>
          </div>
        </div>
      </div>
    `);
    document.body.appendChild(node);
    document.body.style.overflow = "hidden";
    const finish = (v) => {
      document.body.style.overflow = "";
      node.remove();
      resolve(v);
    };
    node.querySelector("[data-yes]").addEventListener("click", () => finish(true));
    node.querySelector("[data-no]").addEventListener("click", () => finish(false));
    node.addEventListener("click", (e) => { if (e.target === node) finish(false); });
  });
}

// formato fechas/duraciones
export function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("es-AR", { day: "numeric", month: "short", year: "numeric" });
}
export function fmtRelative(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const diff = (now - d) / 1000;
  if (diff < 60) return "hace un momento";
  if (diff < 3600) return `hace ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `hace ${Math.floor(diff / 3600)} h`;
  if (diff < 86400 * 7) return `hace ${Math.floor(diff / 86400)} d`;
  return fmtDate(iso);
}
export function fmtDuration(start, end) {
  // agregar Z si no tiene timezone para que se interprete como UTC
  const fixUTC = (iso) => iso && !iso.endsWith("Z") && !iso.includes("+") ? iso + "Z" : iso;
  const s = new Date(fixUTC(start));
  const e = end ? new Date(fixUTC(end)) : new Date();
  let secs = Math.max(0, Math.floor((e - s) / 1000));
  const h = Math.floor(secs / 3600); secs -= h * 3600;
  const m = Math.floor(secs / 60); secs -= m * 60;
  if (h) return `${h}h ${m}m`;
  if (m) return `${m}m ${secs}s`;
  return `${secs}s`;
}

// SVG icons inline (mejor que dep externa)
export const icons = {
  close: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M6 18L18 6"/></svg>`,
  chevronDown: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 9l6 6 6-6"/></svg>`,
  chevronRight: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 6l6 6-6 6"/></svg>`,
  arrowLeft: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>`,
  plus: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg>`,
  check: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5L20 7"/></svg>`,
  trash: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/></svg>`,
  dots: `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/></svg>`,
  timer: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M9 2h6"/></svg>`,
  dumbbell: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4v16M2 8v8M18 4v16M22 8v8M6 12h12"/></svg>`,
  list: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>`,
  history: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 109-9 9.7 9.7 0 00-6.74 2.74L3 8"/><path d="M3 3v5h5M12 7v5l4 2"/></svg>`,
  user: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
  play: `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>`,
  brain: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></svg>`,
};