import { api } from "../api.js";
import { el, esc, icons, fmtDuration, toast } from "../ui.js";
import { appHeader, bottomNav } from "../chrome.js";
import { navigate } from "../router.js";

export async function render(container) {
  const view = el(`
    <div class="screen has-bottom-nav">
      <div id="header-slot"></div>
      <div class="content">
        <div id="active"></div>
        <div id="calendar-wrap"></div>
        <div class="section-title" style="margin-top:20px;">Sesiones</div>
        <div id="list"><div class="muted text-center" style="padding:20px;">Cargando...</div></div>
      </div>
    </div>
  `);

  view.querySelector("#header-slot").appendChild(appHeader({ title: "Historial" }));
  view.appendChild(bottomNav());
  container.replaceChildren(view);

  try {
    const sessions = await api.listSessions({ limit: 100 });
    const active = sessions.find(s => !s.finished_at);
    const finished = sessions.filter(s => s.finished_at);

    // sesion activa destacada
    const activeEl = view.querySelector("#active");
    if (active) {
      const activeDetail = await api.getSession(active.id);
      const isEmpty = !activeDetail.exercises || activeDetail.exercises.length === 0;

      const card = el(`
        <a href="${isEmpty ? '#' : '#/workout/' + active.id}" class="list-item" style="background:var(--accent-bg);border:1px solid var(--accent);margin-bottom:12px;">
          <div class="ex-icon" style="background:var(--accent);color:#fff;">${isEmpty ? '⚠️' : icons.play}</div>
          <div class="body">
            <div class="title" style="color:var(--accent);">${esc(active.title)}</div>
            <div class="meta">${isEmpty ? 'Entrenamiento vacio - toca para descartar' : 'En curso · iniciado ' + fmtRelativeLocal(active.started_at)}</div>
          </div>
          <div class="arrow">${icons.chevronRight}</div>
        </a>
      `);

      if (isEmpty) {
        card.addEventListener("click", async (e) => {
          e.preventDefault();
          if (await confirm("Este entrenamiento esta vacio. ¿Descartarlo?")) {
            try {
              await api.discardSession(active.id);
              toast("Descartado", "success");
              await render(container);
            } catch { toast("Error", "error"); }
          }
        });
      }

      activeEl.appendChild(card);
    }

    // calendario
    renderCalendar(view.querySelector("#calendar-wrap"), finished);

    // lista
    const listEl = view.querySelector("#list");
    listEl.innerHTML = "";
    if (!finished.length) {
      listEl.innerHTML = `<div class="empty-state"><div class="em-title">Sin entrenamientos</div><div>Inicia una rutina para empezar</div></div>`;
      return;
    }
    finished.forEach(s => {
      const dur = fmtDuration(s.started_at, s.finished_at);
      listEl.appendChild(el(`
        <div class="list-item">
          <div class="body">
            <div class="title">${esc(s.title)}</div>
            <div class="meta">${fmtDateLocal(s.started_at)} · ${dur}</div>
          </div>
        </div>
      `));
    });

  } catch (e) {
    toast(e.detail || "Error", "error");
  }
}

function renderCalendar(container, sessions) {
  // mapear fecha -> array de sesiones
  const byDate = {};
  sessions.forEach(s => {
    const d = toLocal(s.started_at);
    const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
    if (!byDate[key]) byDate[key] = [];
    byDate[key].push(s);
  });

  const now = new Date();
  let viewYear = now.getFullYear();
  let viewMonth = now.getMonth();

  const wrap = el(`
    <div style="background:var(--bg-elev-1);border-radius:var(--radius-lg);padding:14px;margin-bottom:4px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
        <button class="icon-btn" id="cal-prev">${icons.arrowLeft}</button>
        <div id="cal-title" style="font-weight:600;font-size:15px;"></div>
        <button class="icon-btn" id="cal-next">${icons.chevronRight}</button>
      </div>
      <div id="cal-grid"></div>
      <div id="cal-detail" style="margin-top:10px;"></div>
    </div>
  `);

  container.appendChild(wrap);

  const drawMonth = () => {
    const title = wrap.querySelector("#cal-title");
    const grid = wrap.querySelector("#cal-grid");
    const detail = wrap.querySelector("#cal-detail");

    const monthNames = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];
    title.textContent = `${monthNames[viewMonth]} ${viewYear}`;

    // header dias semana
    const days = ["Lun","Mar","Mie","Jue","Vie","Sab","Dom"];
    let html = `<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:3px;margin-bottom:4px;">`;
    days.forEach(d => {
      html += `<div style="text-align:center;font-size:10px;color:var(--text-faint);padding:2px 0;">${d}</div>`;
    });
    html += `</div><div style="display:grid;grid-template-columns:repeat(7,1fr);gap:3px;">`;

    const firstDay = new Date(viewYear, viewMonth, 1);
    // lunes = 0 en nuestro calendario
    let startPad = (firstDay.getDay() + 6) % 7;
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
    const today = new Date();

    for (let i = 0; i < startPad; i++) {
      html += `<div></div>`;
    }

    for (let d = 1; d <= daysInMonth; d++) {
      const key = `${viewYear}-${viewMonth}-${d}`;
      const hasSessions = byDate[key];
      const isToday = today.getFullYear() === viewYear && today.getMonth() === viewMonth && today.getDate() === d;

      const bg = hasSessions ? "var(--accent)" : "transparent";
      const color = hasSessions ? "#fff" : isToday ? "var(--accent)" : "var(--text)";
      const border = isToday && !hasSessions ? "1px solid var(--accent)" : "none";
      const label = hasSessions && hasSessions.length > 0 ? hasSessions[0].title.split(" ").slice(0,2).join(" ") : "";

      html += `
        <div data-key="${key}" style="text-align:center;cursor:${hasSessions ? 'pointer' : 'default'};">
          <div style="width:30px;height:30px;border-radius:50%;background:${bg};color:${color};border:${border};display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:${hasSessions ? '600' : '400'};margin:0 auto;">${d}</div>
          ${label ? `<div style="font-size:8px;color:var(--accent);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;margin-top:1px;">${esc(label)}</div>` : ''}
        </div>
      `;
    }

    html += `</div>`;
    grid.innerHTML = html;
    detail.innerHTML = "";

    // click en dia con sesion
    grid.querySelectorAll("[data-key]").forEach(cell => {
      cell.addEventListener("click", () => {
        const key = cell.dataset.key;
        const ss = byDate[key];
        if (!ss) return;
        detail.innerHTML = "";
        ss.forEach(s => {
          const dur = fmtDuration(s.started_at, s.finished_at);
          detail.appendChild(el(`
            <div style="background:var(--bg-elev-2);border-radius:var(--radius);padding:10px 14px;margin-top:8px;">
              <div style="font-weight:600;font-size:14px;">${esc(s.title)}</div>
              <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">${fmtDateLocal(s.started_at)} · ${dur}</div>
            </div>
          `));
        });
      });
    });
  };

  wrap.querySelector("#cal-prev").addEventListener("click", () => {
    viewMonth--;
    if (viewMonth < 0) { viewMonth = 11; viewYear--; }
    drawMonth();
  });
  wrap.querySelector("#cal-next").addEventListener("click", () => {
    viewMonth++;
    if (viewMonth > 11) { viewMonth = 0; viewYear++; }
    drawMonth();
  });

  drawMonth();
}

function toLocal(iso) {
  if (!iso) return new Date();
  const s = iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z";
  return new Date(s);
}

function fmtDateLocal(iso) {
  const d = toLocal(iso);
  return d.toLocaleDateString("es-AR", { weekday: "short", day: "numeric", month: "short" });
}

function fmtRelativeLocal(iso) {
  const d = toLocal(iso);
  const now = new Date();
  const diff = (now - d) / 1000;
  if (diff < 60) return "hace un momento";
  if (diff < 3600) return `hace ${Math.floor(diff / 60)} min`;
  return `hace ${Math.floor(diff / 3600)} h`;
}
