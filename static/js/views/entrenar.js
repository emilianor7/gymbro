import { api } from "../api.js";
import { el, esc, icons, toast, fmtRelative } from "../ui.js";
import { appHeader, bottomNav } from "../chrome.js";
import { navigate } from "../router.js";

export async function render(container) {
  const view = el(`
    <div class="screen has-bottom-nav">
      <div id="header-slot"></div>
      <div class="content">
        <div id="body">
          <div class="muted text-center" style="padding:40px;">Cargando...</div>
        </div>
      </div>
    </div>
  `);

  view.querySelector("#header-slot").appendChild(appHeader({ title: "Entrenar" }));
  view.appendChild(bottomNav());
  container.replaceChildren(view);

  const body = view.querySelector("#body");

  try {
    const sessions = await api.listSessions({ limit: 5 });
    const active = sessions.find(s => !s.finished_at);

    if (active) {
      navigate(`/workout/${active.id}`);
      return;
    }

    const routines = await api.listRoutines();
    body.innerHTML = "";

    if (routines.length === 0) {
      body.innerHTML = `
        <div class="empty-state">
          <div class="em-title">Sin rutinas todavía</div>
          <div>Creá una rutina primero</div>
        </div>
        <button class="btn btn-primary btn-block mt-4" id="go">Ir a Rutinas</button>
      `;
      body.querySelector("#go").addEventListener("click", () => navigate("/routines"));
      return;
    }

    body.appendChild(el(`<div class="section-title">Iniciar entrenamiento</div>`));

    for (const r of routines) {
      const item = el(`
        <div class="list-item">
          <div class="body">
            <div class="title">${esc(r.title)}</div>
            <div class="meta">Editado ${fmtRelative(r.updated_at)}</div>
          </div>
          <button class="btn btn-primary btn-sm" data-start>${icons.play}</button>
        </div>
      `);
      item.querySelector("[data-start]").addEventListener("click", async () => {
        try {
          // verificar si ya hay sesion activa de esta rutina
          const activeSessions = await api.listSessions({ limit: 5 });
          const activeOfThisRoutine = activeSessions.find(
            s => !s.finished_at && s.routine_id === r.id
          );

          if (activeOfThisRoutine) {
            const continuar = await confirm(
              `Ya tenes un entrenamiento de "${r.title}" en curso. ¿Continuar ese entrenamiento?`
            );
            if (continuar) {
              navigate(`/workout/${activeOfThisRoutine.id}`);
            } else {
              // descartar el activo y crear uno nuevo
              await api.discardSession(activeOfThisRoutine.id);
              const session = await api.startSession({ routine_id: r.id });
              navigate(`/workout/${session.id}`);
            }
            return;
          }

          const session = await api.startSession({ routine_id: r.id });
          navigate(`/workout/${session.id}`);
        } catch (e) {
          toast(e.detail || "No se pudo iniciar", "error");
        }
      });
      body.appendChild(item);
    }
  } catch (e) {
    body.innerHTML = `<div class="empty-state">Error cargando</div>`;
    toast(e.detail || "Error", "error");
  }
}
