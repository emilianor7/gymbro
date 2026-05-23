import { auth } from "../api.js";
import { el, esc, icons, toast } from "../ui.js";
import { navigate } from "../router.js";

export async function render(container, { token }) {
  const view = el(`
    <div class="screen" style="padding-top:var(--safe-top);">
      <div class="content" style="max-width:420px;margin:0 auto;padding-top:40px;">
        <div id="body">
          <div class="muted text-center" style="padding:40px;">Cargando...</div>
        </div>
      </div>
    </div>
  `);
  container.replaceChildren(view);
  const body = view.querySelector("#body");

  // cargar preview (no requiere auth)
  let preview;
  try {
    const r = await fetch(`/share/preview/${token}`);
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || "Link invalido");
    preview = data;
  } catch (e) {
    body.innerHTML = `
      <div class="empty-state">
        <div style="font-size:48px;margin-bottom:16px;">🔗</div>
        <div class="em-title">Link invalido</div>
        <div class="muted">${esc(e.message)}</div>
        <button class="btn btn-primary mt-4" onclick="location.hash='#/'">Ir al inicio</button>
      </div>
    `;
    return;
  }

  body.innerHTML = `
    <div style="text-align:center;margin-bottom:24px;">
      <div style="font-size:48px;margin-bottom:12px;">💪</div>
      <div style="font-size:22px;font-weight:700;letter-spacing:-0.02em;">${esc(preview.routine_title)}</div>
      <div style="font-size:13px;color:var(--text-muted);margin-top:6px;">
        Compartida por <strong>${esc(preview.owner_username)}</strong> · ${preview.exercises.length} ejercicios · ${preview.total_sets} series
      </div>
    </div>

    <div class="card" style="margin-bottom:20px;">
      ${preview.exercises.map(ex => `
        <div style="display:flex;align-items:center;justify-content:space-between;
          padding:10px 0;border-bottom:1px solid var(--border);">
          <div style="font-size:14px;">${esc(ex.name)}</div>
          <div style="font-size:12px;color:var(--text-muted);font-family:var(--font-mono);">
            ${ex.sets} x ${ex.target_reps ?? '?'}
          </div>
        </div>
      `).join("")}
    </div>

    <div id="action-area"></div>
  `;

  const actionArea = body.querySelector("#action-area");

  if (!auth.isAuthed) {
    // no logueado: invitar a registrarse
    actionArea.innerHTML = `
      <div style="text-align:center;margin-bottom:16px;font-size:13.5px;color:var(--text-muted);line-height:1.6;">
        Para importar esta rutina necesitas una cuenta en GymBro (gratis).
      </div>
      <button class="btn btn-primary btn-block" id="btn-register">Crear cuenta e importar</button>
      <button class="btn btn-block mt-2" id="btn-login">Ya tengo cuenta</button>
    `;
    // guardar el token en sessionStorage para importar despues del login
    sessionStorage.setItem("pending_import_token", token);

    actionArea.querySelector("#btn-register").addEventListener("click", () => {
      navigate("/login?register=1");
    });
    actionArea.querySelector("#btn-login").addEventListener("click", () => {
      navigate("/login");
    });
  } else {
    // logueado: importar directo
    actionArea.innerHTML = `
      <button class="btn btn-primary btn-block" id="btn-import">
        ${icons.plus}<span>Importar a mis rutinas</span>
      </button>
      <button class="btn btn-ghost btn-block mt-2" onclick="location.hash='#/routines'">
        Cancelar
      </button>
    `;

    actionArea.querySelector("#btn-import").addEventListener("click", async () => {
      const btn = actionArea.querySelector("#btn-import");
      btn.disabled = true;
      btn.querySelector("span").textContent = "Importando...";
      try {
        const tkn = localStorage.getItem("gymbro_token");
        const r = await fetch(`/share/import/${token}`, {
          method: "POST",
          headers: { "Authorization": `Bearer ${tkn}` },
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail);
        toast(`"${data.title}" importada!`, "success");
        navigate(`/routines/${data.routine_id}`);
      } catch (e) {
        toast(e.message || "Error importando", "error");
        btn.disabled = false;
        btn.querySelector("span").textContent = "Importar a mis rutinas";
      }
    });
  }
}
