import { api } from "../api.js";
import { el, esc, icons, toast, MUSCLE_LABEL, EQUIPMENT_LABEL } from "../ui.js";
import { appHeader } from "../chrome.js";
import { navigate } from "../router.js";

export async function render(container, { id }) {
  const view = el(`
    <div class="screen">
      <div id="header-slot"></div>
      <div class="content">
        <div id="ex-content">
          <div class="muted" style="text-align:center;padding:40px 0;">Cargando...</div>
        </div>
      </div>
    </div>
  `);

  const back = el(`<button class="icon-btn">${icons.arrowLeft}</button>`);
  back.addEventListener("click", () => history.back());
  view.querySelector("#header-slot").appendChild(appHeader({ title: "Ejercicio", left: back }));
  container.replaceChildren(view);

  let ex;
  try {
    ex = await api.getExercise(id);
  } catch (e) {
    view.querySelector("#ex-content").innerHTML =
      `<div class="empty-state">Ejercicio no encontrado</div>`;
    toast(e.detail || "Error", "error");
    return;
  }

  const muscleEs = MUSCLE_LABEL[ex.primary_muscle] || ex.primary_muscle;
  const equipEs = EQUIPMENT_LABEL[ex.equipment] || ex.equipment;
  const secondary = (ex.secondary_muscles || []).map(m => MUSCLE_LABEL[m] || m);

  const imgBlock = ex.image_path
    ? `<img src="${esc(ex.image_path)}" alt="${esc(ex.name)}"
         style="width:100%;max-width:360px;aspect-ratio:1;border-radius:var(--radius-lg);
                object-fit:cover;background:var(--bg-elev-2);display:block;margin:0 auto;">`
    : `<div style="width:100%;max-width:360px;aspect-ratio:1;border-radius:var(--radius-lg);
                   background:var(--bg-elev-2);display:flex;align-items:center;justify-content:center;
                   color:var(--text-faint);margin:0 auto;">
         <div style="text-align:center;">
           ${icons.dumbbell}
           <div style="font-size:13px;margin-top:8px;">Sin animación</div>
         </div>
       </div>`;

  const secondaryBlock = secondary.length
    ? `<div style="margin-top:6px;">
         <span class="meta" style="font-size:12px;">Secundarios:</span>
         <span style="font-size:13px;color:var(--text-muted);">${secondary.map(esc).join(", ")}</span>
       </div>`
    : "";

  const instructionsBlock = ex.instructions
    ? `<div class="section-title" style="margin-top:24px;">Cómo se hace</div>
       <div style="background:var(--bg-elev-1);border-radius:var(--radius);padding:16px;
                   font-size:14px;line-height:1.6;color:var(--text-muted);white-space:pre-wrap;">
         ${esc(ex.instructions)}
       </div>`
    : "";

  view.querySelector("#ex-content").innerHTML = `
    <div style="margin-bottom:20px;">
      ${imgBlock}
    </div>
    <div style="text-align:center;margin-bottom:20px;">
      <div style="font-size:20px;font-weight:700;letter-spacing:-0.02em;">${esc(ex.name)}</div>
      <div class="meta" style="margin-top:4px;font-size:13px;">
        ${esc(muscleEs)} · ${esc(equipEs)}${ex.is_custom ? " · custom" : ""}
      </div>
      ${secondaryBlock}
    </div>
    ${instructionsBlock}
  `;
}
