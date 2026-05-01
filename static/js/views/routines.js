import { api } from "../api.js";
import { el, esc, icons, fmtRelative, toast } from "../ui.js";
import { bottomNav, appHeader } from "../chrome.js";
import { navigate } from "../router.js";

export async function render(container) {
  const view = el(`
    <div class="screen has-bottom-nav">
      <div id="header-slot"></div>
      <div class="content">
        <div id="list">
          <div class="muted text-center" style="padding:40px;">Cargando...</div>
        </div>
      </div>
      <button class="fab" id="new-routine" aria-label="Nueva rutina">${icons.plus}</button>
    </div>
  `);

  view.querySelector("#header-slot").appendChild(appHeader({ title: "Rutinas" }));
  view.appendChild(bottomNav());
  container.replaceChildren(view);

  view.querySelector("#new-routine").addEventListener("click", () => {
    promptCreateRoutine();
  });

  try {
    const routines = await api.listRoutines();
    const listEl = view.querySelector("#list");
    if (routines.length === 0) {
      listEl.innerHTML = `
        <div class="empty-state">
          <div class="em-title">Sin rutinas</div>
          <div>Tocá el + para crear la primera</div>
        </div>
      `;
      return;
    }
    listEl.innerHTML = "";
    for (const r of routines) {
      const item = el(`
        <a href="#/routines/${r.id}" class="list-item">
          <div class="body">
            <div class="title">${esc(r.title)}</div>
            <div class="meta">Editado ${fmtRelative(r.updated_at)}</div>
          </div>
          <div class="arrow">${icons.chevronRight}</div>
        </a>
      `);
      listEl.appendChild(item);
    }
  } catch (e) {
    toast(e.detail || "Error cargando rutinas", "error");
  }
}

async function promptCreateRoutine() {
  const title = window.prompt("Nombre de la rutina", "Nueva rutina");
  if (!title) return;
  try {
    const r = await api.createRoutine({ title: title.trim() });
    navigate(`/routines/${r.id}`);
  } catch (e) {
    toast(e.detail || "No se pudo crear", "error");
  }
}
