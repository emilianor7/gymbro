import { api } from "../api.js";
import { el, esc, icons, toast, confirm, fmtDuration } from "../ui.js";
import { appHeader } from "../chrome.js";
import { navigate } from "../router.js";
import { pickExercise } from "../exercise_picker.js";

// e1RM estimado (fórmula de Epley): permite comparar PRs entre distintos rangos de reps.
const e1rm = (kg, reps) => (reps === 1 ? kg : kg * (1 + reps / 30));

// ============================================================
// TIMER DE DESCANSO
// ============================================================
let restTimerHandle = null;
let restTimerEl = null;

function startRestTimer(seconds) {
  clearRestTimer();
  let remaining = seconds;
  const total = seconds;
  const bar = el(`
    <div id="rest-bar" style="position:fixed;bottom:calc(var(--bottom-nav-h) + var(--safe-bottom));left:0;right:0;
      background:var(--bg-elev-2);border-top:2px solid var(--accent);
      padding:10px 16px;display:flex;align-items:center;gap:12px;z-index:25;">
      <div style="flex-shrink:0;">
        <div style="font-size:10px;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;">Descanso</div>
        <div id="rest-count" style="font-family:var(--font-mono);font-size:22px;font-weight:700;color:var(--accent);"></div>
      </div>
      <div style="flex:1;height:4px;background:var(--border);border-radius:2px;">
        <div id="rest-prog" style="height:100%;background:var(--accent);border-radius:2px;width:100%;transition:width 1s linear;"></div>
      </div>
      <button id="rest-skip" class="btn btn-sm" style="flex-shrink:0;">Saltar</button>
    </div>
  `);
  document.body.appendChild(bar);
  restTimerEl = bar;
  const countEl = bar.querySelector("#rest-count");
  const progEl = bar.querySelector("#rest-prog");
  const tick = () => {
    const m = Math.floor(remaining / 60);
    const s = remaining % 60;
    countEl.textContent = m > 0 ? `${m}:${String(s).padStart(2,"0")}` : `${s}s`;
    progEl.style.width = `${(remaining/total)*100}%`;
    if (remaining <= 0) { clearRestTimer(); if (navigator.vibrate) navigator.vibrate([200,100,200]); toast("Descanso terminado!","success",2000); return; }
    remaining--;
    restTimerHandle = setTimeout(tick, 1000);
  };
  bar.querySelector("#rest-skip").addEventListener("click", clearRestTimer);
  tick();
}

function clearRestTimer() {
  if (restTimerHandle) { clearTimeout(restTimerHandle); restTimerHandle = null; }
  if (restTimerEl) { restTimerEl.remove(); restTimerEl = null; }
}

function showRestPicker(currentSecs, onSelect) {
  const opts = [{label:"APAGADO",value:0},{label:"30s",value:30},{label:"1 min",value:60},{label:"1:30",value:90},{label:"2 min",value:120},{label:"3 min",value:180}];
  const ov = el(`
    <div class="sheet-overlay">
      <div class="sheet" style="padding:16px;">
        <div style="font-weight:600;font-size:15px;margin-bottom:16px;">Tiempo de descanso</div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
          ${opts.map(o=>`<button class="btn ${o.value===currentSecs?'btn-primary':''}" data-val="${o.value}" style="height:52px;font-size:15px;">${o.label}</button>`).join("")}
        </div>
      </div>
    </div>
  `);
  document.body.appendChild(ov);
  document.body.style.overflow = "hidden";
  ov.querySelectorAll("[data-val]").forEach(btn => btn.addEventListener("click", () => {
    document.body.style.overflow = ""; ov.remove(); onSelect(parseInt(btn.dataset.val));
  }));
  ov.addEventListener("click", e => { if (e.target===ov) { document.body.style.overflow=""; ov.remove(); } });
}

// ============================================================
// REORDER SHEET
// ============================================================
function showReorderSheet(exercises, refresh) {
  const items = exercises.map(se => ({ id: se.id, name: se.exercise.name }));

  const renderList = () => items.map((item, idx) => `
    <div class="list-item" data-idx="${idx}" style="display:flex;align-items:center;gap:12px;padding:12px 16px;">
      <span style="flex:1;font-size:15px;">${esc(item.name)}</span>
      <button class="icon-btn move-up" data-idx="${idx}" style="opacity:${idx===0?'0.3':'1'}">▲</button>
      <button class="icon-btn move-dn" data-idx="${idx}" style="opacity:${idx===items.length-1?'0.3':'1'}">▼</button>
    </div>
  `).join("");

  const ov = el(`
    <div class="sheet-overlay">
      <div class="sheet" style="padding:8px 0 16px;">
        <div style="width:36px;height:4px;background:var(--border);border-radius:2px;margin:8px auto 12px;"></div>
        <div style="font-weight:600;font-size:15px;padding:0 16px 12px;">Reordenar ejercicios</div>
        <div id="reorder-list">${renderList()}</div>
        <div style="padding:12px 16px 0;display:flex;gap:8px;">
          <button class="btn btn-ghost btn-block" id="cancel-reorder">Cancelar</button>
          <button class="btn btn-primary btn-block" id="save-reorder">Guardar</button>
        </div>
      </div>
    </div>
  `);

  const listEl = ov.querySelector("#reorder-list");

  const rebind = () => {
    listEl.innerHTML = renderList();
    listEl.querySelectorAll(".move-up").forEach(btn => {
      btn.addEventListener("click", () => {
        const i = parseInt(btn.dataset.idx);
        if (i === 0) return;
        [items[i-1], items[i]] = [items[i], items[i-1]];
        rebind();
      });
    });
    listEl.querySelectorAll(".move-dn").forEach(btn => {
      btn.addEventListener("click", () => {
        const i = parseInt(btn.dataset.idx);
        if (i === items.length-1) return;
        [items[i], items[i+1]] = [items[i+1], items[i]];
        rebind();
      });
    });
  };
  rebind();

  ov.querySelector("#cancel-reorder").addEventListener("click", () => ov.remove());
  ov.querySelector("#save-reorder").addEventListener("click", async () => {
    ov.remove();
    try {
      await Promise.all(items.map((item, idx) =>
        api.patchSessionExercise(item.id, { order_index: idx })
      ));
      await refresh();
    } catch(e) { toast("Error al reordenar","error"); }
  });

  ov.addEventListener("click", e => { if (e.target===ov) ov.remove(); });
  document.body.appendChild(ov);
}

// ============================================================
// VISTA PRINCIPAL
// ============================================================
export async function render(container, { id }) {
  const view = el(`
    <div class="screen">
      <div id="header-slot"></div>
      <div class="content">
        <div class="stats-bar">
          <div class="stat"><div class="label">Duración</div><div class="value" id="stat-time">0s</div></div>
          <div class="stat"><div class="label">Volumen</div><div class="value" id="stat-vol">0 kg</div></div>
          <div class="stat"><div class="label">Series</div><div class="value" id="stat-sets">0</div></div>
        </div>
        <div id="exercises"></div>
        <button class="btn btn-block mt-4" id="add-ex">${icons.plus}<span>Agregar ejercicio</span></button>
        <button class="btn btn-ghost btn-block mt-2" id="discard" style="color:var(--danger);">Descartar entrenamiento</button>
      </div>
    </div>
  `);

  const headerSlot = view.querySelector("#header-slot");
  const back = el(`<button class="icon-btn">${icons.chevronDown}</button>`);
  back.addEventListener("click", () => { clearRestTimer(); navigate("/routines"); });
  const finishBtn = el(`<button class="btn btn-primary btn-sm btn-pill">Terminar</button>`);
  finishBtn.addEventListener("click", doFinish);
  headerSlot.appendChild(appHeader({ title: "Entreno", left: back, right: finishBtn }));
  container.replaceChildren(view);

  let session = null;
  let historyCache = new Map();
  let prCache = new Map();
  let restConfig = new Map();
  let notesCache = new Map();
  const techniqueOpen = new Map();  // se.id -> bool (estado del expandible por ejercicio)

  const exercisesEl = view.querySelector("#exercises");
  const statTime = view.querySelector("#stat-time");
  const statVol = view.querySelector("#stat-vol");
  const statSets = view.querySelector("#stat-sets");
  const timerHandle = setInterval(() => {
    if (session && !session.finished_at) statTime.textContent = fmtDuration(session.started_at);
  }, 1000);

  // Limpia el interval al salir de esta vista (bottom-nav, back del browser, etc.)
  const onHashChange = () => {
    if (location.hash !== `#/workout/${id}`) {
      clearInterval(timerHandle);
      clearRestTimer();
      window.removeEventListener("hashchange", onHashChange);
    }
  };
  window.addEventListener("hashchange", onHashChange);

  const refresh = async () => {
    try { session = await api.getSession(id); }
    catch (e) { toast(e.detail||"Error","error"); navigate("/routines"); return; }
    if (session.finished_at) { clearInterval(timerHandle); clearRestTimer(); navigate("/history"); return; }
    let vol=0, comp=0;
    for (const se of session.exercises)
      for (const s of se.sets)
        if (s.completed && s.kg && s.reps) { vol += s.kg*s.reps; comp++; }
    statVol.textContent = `${vol.toFixed(0)} kg`;
    statSets.textContent = comp;
    await loadHistory(session.exercises);
    // Auto-open de "Ver técnica" en el primer ejercicio activo (con image y sin sets completados)
    // solo si nunca lo abrieron/cerraron manualmente.
    const firstActive = session.exercises.find(se =>
      se.exercise.image_path && !se.sets.some(s => s.completed)
    );
    if (firstActive && !techniqueOpen.has(firstActive.id)) {
      techniqueOpen.set(firstActive.id, true);
    }
    exercisesEl.innerHTML = "";
    for (const se of session.exercises)
      exercisesEl.appendChild(renderExercise(se, refresh, historyCache, prCache, restConfig, notesCache, session, techniqueOpen));
    if (!session.exercises.length)
      exercisesEl.innerHTML = `<div class="empty-state"><div class="em-title">Sin ejercicios</div><div>Agregá uno para empezar</div></div>`;
  };

  const loadHistory = async (exs) => {
    const ids = [...new Set(exs.map(se=>se.exercise.id))];
    await Promise.all(ids.map(async exId => {
      if (historyCache.has(exId)) return;
      try {
        const hist = await api.historyForExercise(exId, 10);
        const prev = hist.find(se=>se.session_id!==session.id)||null;
        const map = {};
        if (prev) for (const s of prev.sets) if (s.completed&&s.kg!=null&&s.reps!=null) map[s.set_number]=`${s.kg}kg x ${s.reps}`;
        historyCache.set(exId, map);
        let best=0;
        for (const se of hist) if (se.session_id!==session.id) for (const s of se.sets) {
          if (s.completed && s.kg!=null && s.kg>0 && s.reps!=null && s.reps>0) {
            const e = e1rm(s.kg, s.reps);
            if (e>best) best=e;
          }
        }
        prCache.set(exId, best);
      } catch { historyCache.set(exId,{}); prCache.set(exId,0); }
    }));
  };

  view.querySelector("#add-ex").addEventListener("click", () => {
    pickExercise(async ex => {
      try {
        const se = await api.addSessionExercise(id, {exercise_id:ex.id});
        await api.addSessionSet(se.id, {kg:null,reps:null});
        await refresh();
      } catch(e) { toast(e.detail||"Error","error"); }
    });
  });

  view.querySelector("#discard").addEventListener("click", async () => {
    if (!await confirm("¿Descartar el entrenamiento?")) return;
    clearInterval(timerHandle); clearRestTimer();
    await api.discardSession(id);
    toast("Descartado","success");
    navigate("/routines");
  });

  async function doFinish() {
    if (!session) return;
    const c = session.exercises.flatMap(se=>se.sets).filter(s=>s.completed).length;
    if (c===0 && !await confirm("No marcaste series. ¿Finalizar igual?")) return;
    clearInterval(timerHandle); clearRestTimer();
    await api.finishSession(id);
    toast("¡Entrenamiento guardado!","success");
    navigate("/history");
  }

  await refresh();
}

// ============================================================
// CARD DE EJERCICIO
// ============================================================
function renderExercise(se, refresh, historyCache, prCache, restConfig, notesCache, session, techniqueOpen) {
  const prevMap = historyCache.get(se.exercise.id)||{};
  const bestE1rm = prCache.get(se.exercise.id)||0;
  const restSecs = restConfig.get(se.id)||0;
  const note = notesCache.get(se.id) ?? (se.note||"");
  const hasImage = !!se.exercise.image_path;
  const techOpen = techniqueOpen?.get(se.id) ?? false;

  const fmtRest = s => s===0?"APAGADO":s>=60?`${Math.floor(s/60)}:${String(s%60).padStart(2,"0")}`:`${s}s`;

  const techniqueBlock = hasImage ? `
    <div class="technique-section">
      <button class="technique-toggle" style="display:flex;align-items:center;gap:8px;background:none;border:0;color:var(--text-muted);font-size:13px;padding:6px 0;cursor:pointer;">
        <span class="tech-caret" style="display:inline-block;transition:transform .15s;${techOpen?'transform:rotate(180deg);':''}">▾</span>
        <span class="tech-label">${techOpen ? 'Ocultar técnica' : 'Ver técnica'}</span>
      </button>
      <div class="technique-body" style="${techOpen ? '' : 'display:none;'}max-width:280px;margin:6px 0 10px;">
        <img src="${esc(se.exercise.image_path)}" loading="lazy" alt=""
          style="width:100%;aspect-ratio:1;border-radius:var(--radius);object-fit:cover;background:var(--bg-elev-2);display:block;">
      </div>
    </div>
  ` : "";

  const card = el(`
    <div class="card">
      <div class="card-header">
        <div class="ex-icon">${icons.dumbbell}</div>
        <div class="title">${esc(se.exercise.name)}</div>
        <button class="icon-btn dots-btn">${icons.dots}</button>
      </div>
      ${techniqueBlock}
      <div class="rest-row" style="cursor:pointer;">${icons.timer}<span class="rest-label">Descanso: ${fmtRest(restSecs)}</span></div>
      <textarea class="ex-note-input" placeholder="Agregar notas aqui...">${esc(note)}</textarea>
      <div class="sets">
        <div class="sets-head">
          <div>SERIE</div><div class="h-prev">ANTERIOR</div><div>KG</div><div>REPS</div><div>${icons.check}</div>
        </div>
        <div class="rows" style="display:contents;"></div>
      </div>
      <button class="add-set">${icons.plus}<span>Agregar serie</span></button>
    </div>
  `);

  const noteEl = card.querySelector(".ex-note-input");
  noteEl.style.height = noteEl.scrollHeight + "px";
  noteEl.addEventListener("input", () => {
    notesCache.set(se.id, noteEl.value);
    noteEl.style.height = "auto";
    noteEl.style.height = noteEl.scrollHeight + "px";
  });

  const rows = card.querySelector(".rows");
  // PR: el set con mayor e1RM de la sesión que supera el récord histórico.
  // Empates van al primer set (menor set_number).
  let prSetId = null;
  if (bestE1rm > 0) {
    let prVal = bestE1rm;
    for (const s of se.sets) {
      if (s.completed && s.kg > 0 && s.reps > 0) {
        const e = e1rm(s.kg, s.reps);
        if (e > prVal) {
          prVal = e;
          prSetId = s.id;
        }
      }
    }
  }
  for (const s of se.sets) {
    const isPR = s.id === prSetId;
    rows.appendChild(renderSetRow(s, prevMap[s.set_number], refresh, isPR, se.id, restConfig));
  }

  if (hasImage) {
    const toggle = card.querySelector(".technique-toggle");
    const body = card.querySelector(".technique-body");
    const caret = card.querySelector(".tech-caret");
    const label = card.querySelector(".tech-label");
    toggle.addEventListener("click", () => {
      const nowOpen = body.style.display === "none";
      body.style.display = nowOpen ? "" : "none";
      caret.style.transform = nowOpen ? "rotate(180deg)" : "";
      label.textContent = nowOpen ? "Ocultar técnica" : "Ver técnica";
      techniqueOpen?.set(se.id, nowOpen);
    });
  }

  card.querySelector(".rest-row").addEventListener("click", () => {
    showRestPicker(restConfig.get(se.id)||0, val => {
      restConfig.set(se.id, val);
      card.querySelector(".rest-label").textContent = `Descanso: ${fmtRest(val)}`;
    });
  });

  card.querySelector(".add-set").addEventListener("click", async () => {
    const last = se.sets[se.sets.length-1];
    try {
      await api.addSessionSet(se.id, {kg:last?.kg??null, reps:last?.reps??null});
      await refresh();
    } catch(e) { toast(e.detail||"Error","error"); }
  });

  // menu 3 puntos
  card.querySelector(".dots-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    const ov = el(`
      <div class="sheet-overlay">
        <div class="sheet" style="padding:8px 0 16px;">
          <div style="width:36px;height:4px;background:var(--border);border-radius:2px;margin:8px auto 16px;"></div>
          <button class="dots-opt" data-action="detail" style="display:flex;align-items:center;gap:14px;width:100%;border:0;background:none;padding:14px 20px;cursor:pointer;font-size:15px;color:var(--text);">
            <span style="font-size:18px;width:24px;text-align:center;">ⓘ</span> Ver detalle del ejercicio
          </button>
          <button class="dots-opt" data-action="reorder" style="display:flex;align-items:center;gap:14px;width:100%;border:0;background:none;padding:14px 20px;cursor:pointer;font-size:15px;color:var(--text);">
            <span style="font-size:18px;width:24px;text-align:center;">↕</span> Reordenar ejercicios
          </button>
          <button class="dots-opt" data-action="replace" style="display:flex;align-items:center;gap:14px;width:100%;border:0;background:none;padding:14px 20px;cursor:pointer;font-size:15px;color:var(--text);">
            <span style="font-size:18px;width:24px;text-align:center;">🔄</span> Reemplazar ejercicio
          </button>
          <button class="dots-opt" data-action="remove" style="display:flex;align-items:center;gap:14px;width:100%;border:0;background:none;padding:14px 20px;cursor:pointer;font-size:15px;color:var(--danger);">
            <span style="font-size:18px;width:24px;text-align:center;">🗑️</span> Eliminar ejercicio
          </button>
        </div>
      </div>
    `);

    ov.addEventListener("click", ev => { if (ev.target === ov) ov.remove(); });

    ov.querySelectorAll(".dots-opt").forEach(btn => {
      btn.addEventListener("click", async () => {
        ov.remove();
        const action = btn.dataset.action;

        if (action === "detail") {
          navigate(`/exercise/${se.exercise.id}`);

        } else if (action === "remove") {
          if (!await confirm(`¿Eliminar ${se.exercise.name}?`)) return;
          try {
            await api.deleteSessionExercise(se.id);
            await refresh();
          } catch(e) { toast(e.detail||"Error al eliminar","error"); }

        } else if (action === "replace") {
          pickExercise(async ex => {
            try {
              const newSe = await api.addSessionExercise(session.id, {exercise_id: ex.id});
              await api.addSessionSet(newSe.id, {kg: null, reps: null});
              await api.patchSessionExercise(newSe.id, {order_index: se.order_index ?? 0});
              await api.deleteSessionExercise(se.id);
              await refresh();
            } catch(e) { toast(e.detail||"Error al reemplazar","error"); }
          });

        } else if (action === "reorder") {
          showReorderSheet(session.exercises, refresh);
        }
      });
    });

    document.body.appendChild(ov);
  });

  return card;
}

// ============================================================
// SET ROW - long press en numero para eliminar
// ============================================================
function renderSetRow(s, prevText, refresh, isPR, seId, restConfig) {
  const completed = s.completed;
  const numDisplay = isPR ? "🥇" : (completed ? "✓" : s.set_number);
  const numColor = completed && !isPR ? "var(--accent)" : "var(--text)";

  const kgVal = s.completed ? (s.kg ?? '') : '';
  const repsVal = s.completed ? (s.reps ?? '') : '';
  const kgPlaceholder = (!s.completed && s.kg) ? s.kg : '';
  const repsPlaceholder = (!s.completed && s.reps) ? s.reps : '';

  const row = el(`
    <div class="set-row ${completed?'completed':''}">
      <div class="num" style="cursor:pointer;color:${numColor};user-select:none;">${numDisplay}</div>
      <div class="prev ${prevText?'':'empty'}">${esc(prevText||'')}</div>
      <div><input class="set-input" type="number" inputmode="decimal" step="0.5" value="${kgVal}" placeholder="${kgPlaceholder}" data-field="kg"></div>
      <div><input class="set-input" type="number" inputmode="numeric" value="${repsVal}" placeholder="${repsPlaceholder}" data-field="reps"></div>
      <button class="check-btn">${icons.check}</button>
    </div>
  `);

  const kgIn = row.querySelector('[data-field="kg"]');
  const repsIn = row.querySelector('[data-field="reps"]');
  const numEl = row.querySelector(".num");
  const checkBtn = row.querySelector(".check-btn");

  const persistOnBlur = async () => {
    if (!s.completed) return;
    try {
      await api.logSet(s.id, {
        kg: kgIn.value===""?null:parseFloat(kgIn.value),
        reps: repsIn.value===""?null:parseInt(repsIn.value),
        completed: true,
      });
      await refresh();
    } catch(e) { toast(e.detail||"Error","error"); }
  };
  kgIn.addEventListener("blur", persistOnBlur);
  repsIn.addEventListener("blur", persistOnBlur);

  const doToggle = async () => {
    const kg = kgIn.value===""?null:parseFloat(kgIn.value);
    const reps = repsIn.value===""?null:parseInt(repsIn.value);
    if (!s.completed && (kg==null||reps==null)) { toast("Completá kg y reps primero","error"); return; }
    try {
      await api.logSet(s.id, {kg, reps, completed:!s.completed});
      if (!s.completed) { const secs=restConfig.get(seId)||0; if (secs>0) startRestTimer(secs); }
      else clearRestTimer();
      await refresh();
    } catch(e) { toast(e.detail||"Error","error"); }
  };
  checkBtn.addEventListener("click", doToggle);

  let longPressTimer = null;
  numEl.addEventListener("touchstart", () => {
    longPressTimer = setTimeout(async () => {
      if (await confirm(`¿Eliminar serie ${s.set_number}?`)) {
        try { await api.deleteSessionSet(s.id); await refresh(); }
        catch(e) { toast(e.detail||"Error","error"); }
      }
    }, 600);
  }, {passive:true});
  numEl.addEventListener("touchend", () => clearTimeout(longPressTimer));
  numEl.addEventListener("touchmove", () => clearTimeout(longPressTimer));
  numEl.addEventListener("click", doToggle);

  return row;
}
