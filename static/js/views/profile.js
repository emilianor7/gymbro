import { auth } from "../api.js";
import { el, esc, icons, toast } from "../ui.js";
import { appHeader, bottomNav } from "../chrome.js";
import { navigate } from "../router.js";

export async function render(container) {
  const u = auth.user || {};
  const view = el(`
    <div class="screen has-bottom-nav">
      <div id="header-slot"></div>
      <div class="content">
        <div style="display:flex;align-items:center;gap:16px;padding:8px 0 20px;">
          <div style="width:64px;height:64px;border-radius:50%;background:var(--bg-elev-2);display:flex;align-items:center;justify-content:center;flex-shrink:0;color:var(--accent);">
            ${icons.user}
          </div>
          <div>
            <div style="font-size:20px;font-weight:700;letter-spacing:-0.02em;">${esc(u.username || '')}</div>
            <div style="font-size:13px;color:var(--text-muted);">${esc(u.email || '')}</div>
          </div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:20px;" id="quick-stats">
          <div class="stat-box"><div class="sb-val" id="s-sessions">—</div><div class="sb-label">Sesiones</div></div>
          <div class="stat-box"><div class="sb-val" id="s-streak">—</div><div class="sb-label">Racha</div></div>
          <div class="stat-box"><div class="sb-val" id="s-week">—</div><div class="sb-label">Esta semana</div></div>
        </div>

        <div class="section-title">Duracion / Sesiones</div>
        <div style="background:var(--bg-elev-1);border-radius:var(--radius-lg);padding:16px 12px 10px;margin-bottom:20px;">
          <div style="display:flex;gap:8px;margin-bottom:14px;">
            <button class="btn btn-sm chart-tab active" data-tab="duration">Duracion</button>
            <button class="btn btn-sm chart-tab" data-tab="sessions">Sesiones</button>
          </div>
          <div id="chart" style="height:100px;display:flex;align-items:flex-end;gap:4px;"></div>
          <div id="chart-labels" style="display:flex;gap:4px;margin-top:6px;"></div>
        </div>

        <div class="section-title">Records personales</div>
        <div id="prs" style="margin-bottom:20px;"><div class="muted" style="font-size:13px;">Cargando...</div></div>

        <div class="section-title">Sesiones recientes</div>
        <div id="recent" style="margin-bottom:20px;"><div class="muted" style="font-size:13px;">Cargando...</div></div>

        <button class="btn btn-block" id="logout" style="color:var(--danger);margin-top:8px;">Cerrar sesion</button>
      </div>
    </div>
  `);

  const style = document.createElement("style");
  style.textContent = `
    .stat-box{background:var(--bg-elev-1);border-radius:var(--radius);padding:12px 8px;text-align:center;}
    .sb-val{font-family:var(--font-mono);font-size:20px;font-weight:700;color:var(--accent);}
    .sb-label{font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.05em;margin-top:2px;}
    .chart-tab{background:var(--bg-elev-2);color:var(--text-muted);}
    .chart-tab.active{background:var(--accent);color:#fff;}
  `;
  document.head.appendChild(style);

  view.querySelector("#header-slot").appendChild(appHeader({ title: "Perfil" }));
  view.appendChild(bottomNav());
  container.replaceChildren(view);

  view.querySelector("#logout").addEventListener("click", () => { auth.clear(); navigate("/login"); });

  // cargar stats
  let data = null;
  try {
    const token = localStorage.getItem("gymbro_token");
    const r = await fetch("/stats/profile", { headers: { "Authorization": `Bearer ${token}` } });
    if (!r.ok) throw new Error();
    data = await r.json();
  } catch {
    toast("Error cargando estadisticas", "error");
    return;
  }

  // quick stats
  const fmtMin = (m) => { const h = Math.floor(m/60); return h ? `${h}h ${m%60}m` : `${m}m`; };
  view.querySelector("#s-sessions").textContent = data.total_sessions;
  view.querySelector("#s-streak").textContent = `${data.streak_days}d`;
  view.querySelector("#s-week").textContent = fmtMin(data.this_week_duration_min) || "0m";

  // grafico
  let currentTab = "duration";
  const renderChart = (tab) => {
    const values = data.weeks.map(w => tab === "duration" ? w.duration_min : w.sessions);
    const maxVal = Math.max(...values, 1);
    const chartEl = view.querySelector("#chart");
    const labelsEl = view.querySelector("#chart-labels");
    chartEl.innerHTML = "";
    labelsEl.innerHTML = "";
    data.weeks.forEach((w, i) => {
      const val = values[i];
      const pct = Math.max((val / maxVal) * 100, val > 0 ? 4 : 0);
      chartEl.appendChild(el(`
        <div style="flex:1;display:flex;flex-direction:column;align-items:center;">
          <div style="width:100%;border-radius:3px 3px 0 0;background:${val > 0 ? 'var(--accent)' : 'var(--bg-elev-2)'};height:${pct}%;min-height:${val>0?'3px':'0'};"></div>
        </div>
      `));
      labelsEl.appendChild(el(`<div style="flex:1;font-size:9px;color:var(--text-faint);text-align:center;">${w.week_label}</div>`));
    });
  };
  renderChart(currentTab);

  view.querySelectorAll(".chart-tab").forEach(btn => {
    btn.addEventListener("click", () => {
      view.querySelectorAll(".chart-tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentTab = btn.dataset.tab;
      renderChart(currentTab);
    });
  });

  // PRs
  const prsEl = view.querySelector("#prs");
  prsEl.innerHTML = "";
  if (!data.prs.length) {
    prsEl.innerHTML = `<div class="empty-state" style="padding:20px 0;">Completa entrenamientos para ver tus records</div>`;
  } else {
    data.prs.forEach(pr => prsEl.appendChild(el(`
      <div class="list-item" style="padding:10px 14px;">
        <div class="body">
          <div class="title" style="font-size:14px;">${esc(pr.exercise_name)}</div>
          <div class="meta">${pr.date}</div>
        </div>
        <div style="font-family:var(--font-mono);font-weight:700;font-size:15px;color:var(--accent);">${pr.kg}kg x ${pr.reps}</div>
      </div>
    `)));
  }

  // recientes
  const recentEl = view.querySelector("#recent");
  recentEl.innerHTML = "";
  if (!data.recent_sessions.length) {
    recentEl.innerHTML = `<div class="empty-state" style="padding:20px 0;">Sin sesiones todavia</div>`;
  } else {
    data.recent_sessions.forEach(s => recentEl.appendChild(el(`
      <div class="list-item" style="padding:10px 14px;">
        <div class="body">
          <div class="title" style="font-size:14px;">${esc(s.title)}</div>
          <div class="meta">${esc(s.date)}</div>
        </div>
        <div style="font-size:13px;color:var(--text-muted);">${fmtMin(s.duration_min)}</div>
      </div>
    `)));
  }
}
