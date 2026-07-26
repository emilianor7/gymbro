import { api } from "../api.js";
import { el, esc, icons, toast, confirm } from "../ui.js";
import { appHeader, bottomNav } from "../chrome.js";
import { navigate } from "../router.js";
import { pickExercise } from "../exercise_picker.js";
import { groupSupersets, supersetWrapper, supersetTag, parseSuperset } from "../superset.js";

const fmtRest = s => s >= 60 ? `${Math.floor(s/60)}:${String(s%60).padStart(2,"0")}` : `${s}s`;

export async function render(container, { id }) {
  const view = el(`
    <div class="screen has-bottom-nav">
      <div id="header-slot"></div>
      <div class="content">
        <div id="meta" class="mb-4"></div>
        <div id="exercises"></div>
        <button class="btn btn-block mt-4" id="add-ex">${icons.plus}<span>Agregar ejercicio</span></button>
        <button class="btn btn-primary btn-block mt-2" id="start">${icons.play}<span>Iniciar entrenamiento</span></button>
        <button class="btn btn-block mt-4" id="share" style="background:var(--bg-elev-2);">🔗<span style="margin-left:8px;">Compartir rutina</span></button>
        <button class="btn btn-ghost btn-block mt-2" id="del" style="color:var(--danger);">Eliminar rutina</button>
      </div>
    </div>
  `);

  const headerSlot = view.querySelector("#header-slot");
  const back = el(`<button class="icon-btn">${icons.arrowLeft}</button>`);
  back.addEventListener("click", () => navigate("/routines"));
  headerSlot.appendChild(appHeader({ title: "Rutina", left: back }));
  view.appendChild(bottomNav());
  container.replaceChildren(view);

  let routine = null;
  const exercisesEl = view.querySelector("#exercises");
  const metaEl = view.querySelector("#meta");

  const refresh = async () => {
    try {
      routine = await api.getRoutine(id);
    } catch (e) {
      toast(e.detail || "No se pudo cargar", "error");
      navigate("/routines");
      return;
    }
    headerSlot.replaceChildren(appHeader({ title: routine.title, left: back }));
    metaEl.innerHTML = `<div class="muted" style="font-size:13px;">${routine.exercises.length} ejercicios · ${countSets(routine)} series</div>`;

    exercisesEl.innerHTML = "";
    for (const g of groupSupersets(routine.exercises, re => re.note)) {
      const target = g.letter
        ? exercisesEl.appendChild(supersetWrapper(g.letter, g.items.length))
        : exercisesEl;
      for (const re of g.items) target.appendChild(renderExerciseCard(re, refresh));
    }
    if (routine.exercises.length === 0) {
      exercisesEl.innerHTML = `<div class="empty-state"><div class="em-title">Vacia</div><div>Agregá ejercicios para empezar</div></div>`;
    }
  };

  view.querySelector("#add-ex").addEventListener("click", () => {
    pickExercise(async (ex) => {
      try {
        const re = await api.addExerciseToRoutine(id, { exercise_id: ex.id, rest_seconds: 90 });
        // agregar 3 sets default
        for (let i = 0; i < 3; i++) {
          await api.addRoutineSet(re.id, { target_kg: null, target_reps: 10 });
        }
        await refresh();
      } catch (e) {
        toast(e.detail || "No se pudo agregar", "error");
      }
    });
  });

  view.querySelector("#start").addEventListener("click", async () => {
    if (!routine || routine.exercises.length === 0) {
      toast("Agregá al menos un ejercicio", "error");
      return;
    }
    try {
      // verificar sesion activa de esta rutina
      const activeSessions = await api.listSessions({ limit: 5 });
      const activeOfThisRoutine = activeSessions.find(
        s => !s.finished_at && s.routine_id === routine.id
      );

      if (activeOfThisRoutine) {
        const continuar = await confirm(
          `Ya tenes un entrenamiento de "${routine.title}" en curso. ¿Continuar ese entrenamiento?`
        );
        if (continuar) {
          navigate(`/workout/${activeOfThisRoutine.id}`);
        } else {
          await api.discardSession(activeOfThisRoutine.id);
          const session = await api.startSession({ routine_id: routine.id });
          navigate(`/workout/${session.id}`);
        }
        return;
      }

      const session = await api.startSession({ routine_id: routine.id });
      navigate(`/workout/${session.id}`);
    } catch (e) {
      toast(e.detail || "No se pudo iniciar", "error");
    }
  });

  view.querySelector("#del").addEventListener("click", async () => {
    if (!await confirm("¿Eliminar esta rutina?")) return;
    try {
      await api.deleteRoutine(id);
      toast("Rutina eliminada", "success");
      navigate("/routines");
    } catch (e) {
      toast(e.detail || "Error", "error");
    }
  });

  view.querySelector("#share").addEventListener("click", async () => {
    try {
      const token = localStorage.getItem("gymbro_token");
      const r = await fetch(`/share/routines/${id}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail);

      // mostrar sheet con el link
      const { sheet } = await import("../ui.js");
      const s = sheet({
        title: "Compartir rutina",
        body: el(`
          <div>
            <p style="font-size:13.5px;color:var(--text-muted);margin-bottom:16px;line-height:1.6;">
              Cualquiera con este link puede importar una copia de la rutina a su cuenta.
            </p>
            <div style="background:var(--bg-input);border-radius:var(--radius);padding:12px 14px;
              font-family:var(--font-mono);font-size:13px;word-break:break-all;margin-bottom:14px;color:var(--accent);">
              ${data.url}
            </div>
            <button class="btn btn-primary btn-block" id="copy-link">Copiar link</button>
            ${data.uses > 0 ? `<div style="text-align:center;font-size:12px;color:var(--text-faint);margin-top:10px;">${data.uses} persona${data.uses>1?'s':''} ya importaron esta rutina</div>` : ''}
          </div>
        `),
      });
      s.body.querySelector("#copy-link").addEventListener("click", () => {
        navigator.clipboard.writeText(data.url).then(() => {
          toast("Link copiado!", "success");
        }).catch(() => {
          // fallback para cuando clipboard no esta disponible
          const input = document.createElement("input");
          input.value = data.url;
          document.body.appendChild(input);
          input.select();
          document.execCommand("copy");
          document.body.removeChild(input);
          toast("Link copiado!", "success");
        });
      });
    } catch (e) {
      toast(e.detail || "Error generando link", "error");
    }
  });

  await refresh();
}

function countSets(routine) {
  return routine.exercises.reduce((acc, re) => acc + re.sets.length, 0);
}

function renderExerciseCard(re, refresh) {
  // La nota se muestra en modo lectura: es la indicacion tecnica del plan.
  // Se edita en la sesion en vivo. Al prefijo "SUPERSERIE A1" ya lo representa
  // el badge del bloque, asi que no lo repetimos.
  const ss = parseSuperset(re.note);
  const noteText = ss ? ss.rest : (re.note || "");
  const meta = [];
  if (re.rest_seconds > 0) meta.push(`Descanso ${fmtRest(re.rest_seconds)}`);
  else if (ss) meta.push("Sin descanso · encadenar");

  const card = el(`
    <div class="card">
      <div class="card-header">
        <div class="ex-icon">${icons.dumbbell}</div>
        <div class="title">${esc(re.exercise.name)}</div>
        ${supersetTag(re.note)}
        <button class="icon-btn" data-action="remove">${icons.trash}</button>
      </div>
      ${meta.length ? `<div class="ex-meta">${icons.timer}<span>${meta.join(" · ")}</span></div>` : ""}
      ${noteText.trim() ? `<div class="ex-note-read">${esc(noteText.trim())}</div>` : ""}

      <div class="sets">
        <div class="sets-head">
          <div>SET</div>
          <div></div>
          <div>KG</div>
          <div>REPS</div>
          <div></div>
        </div>
        <div class="rows"></div>
      </div>
      <button class="add-set">${icons.plus}<span>Agregar serie</span></button>
    </div>
  `);

  const rows = card.querySelector(".rows");
  for (const s of re.sets) {
    rows.appendChild(renderRoutineSetRow(s, refresh));
  }

  card.querySelector(".add-set").addEventListener("click", async () => {
    try {
      const last = re.sets[re.sets.length - 1];
      await api.addRoutineSet(re.id, {
        target_kg: last?.target_kg ?? null,
        target_reps: last?.target_reps ?? 10,
      });
      await refresh();
    } catch (e) {
      toast(e.detail || "Error", "error");
    }
  });

  card.querySelector('[data-action="remove"]').addEventListener("click", async () => {
    if (!await confirm(`¿Quitar ${re.exercise.name}?`)) return;
    try {
      await api.removeRoutineExercise(re.id);
      await refresh();
    } catch (e) {
      toast(e.detail || "Error", "error");
    }
  });

  return card;
}

function renderRoutineSetRow(s, refresh) {
  const row = el(`
    <div class="set-row">
      <div class="num">${s.set_number}</div>
      <div class="prev empty"></div>
      <div><input class="set-input" type="number" inputmode="decimal" step="0.5" value="${s.target_kg ?? ''}" data-field="kg"></div>
      <div><input class="set-input" type="number" inputmode="numeric" value="${s.target_reps ?? ''}" data-field="reps"></div>
      <button class="icon-btn" style="width:32px;height:32px;color:var(--text-faint);" data-del>${icons.close}</button>
    </div>
  `);

  const kgIn = row.querySelector('[data-field="kg"]');
  const repsIn = row.querySelector('[data-field="reps"]');

  const persist = async () => {
    const payload = {
      target_kg: kgIn.value === "" ? null : parseFloat(kgIn.value),
      target_reps: repsIn.value === "" ? null : parseInt(repsIn.value),
    };
    try {
      await api.updateRoutineSet(s.id, payload);
    } catch (e) {
      toast(e.detail || "Error guardando", "error");
    }
  };

  kgIn.addEventListener("blur", persist);
  repsIn.addEventListener("blur", persist);

  row.querySelector("[data-del]").addEventListener("click", async () => {
    try {
      await api.deleteRoutineSet(s.id);
      await refresh();
    } catch (e) {
      toast(e.detail || "Error", "error");
    }
  });

  return row;
}
