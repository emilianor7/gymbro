import { api } from "./api.js";
import { el, esc, sheet, debounce, toast, icons, MUSCLE_LABEL } from "./ui.js";

const MUSCLES = [
  "chest","back","shoulders","biceps","triceps","forearms",
  "quadriceps","hamstrings","glutes","calves","abdominals",
  "obliques","lower_back","traps","lats","other"
];
const EQUIPMENTS = [
  "barbell","dumbbell","machine","cable","smith","bodyweight",
  "kettlebell","band","plate","ez_bar","trx","other"
];

export async function pickExercise(onPick) {
  const body = el(`
    <div>
      <div style="margin:0 0 10px;">
        <button class="btn btn-block" id="create-ex">${icons.plus}<span>Crear ejercicio nuevo</span></button>
      </div>
      <div class="muscle-chips" style="display:flex;gap:6px;overflow-x:auto;margin:0 -16px 10px;padding:0 16px 4px;scrollbar-width:none;-webkit-overflow-scrolling:touch;"></div>
      <div class="sheet-search" style="margin:0 0 12px;">
        <input type="text" id="search" placeholder="Buscar ejercicio..." autocomplete="off" autocapitalize="none">
      </div>
      <div id="results"></div>
    </div>
  `);

  const s = sheet({ title: "Agregar ejercicio", body });
  const searchInput = body.querySelector("#search");
  const resultsEl = body.querySelector("#results");
  const chipsEl = body.querySelector(".muscle-chips");

  let allExercises = [];
  let activeMuscle = "";  // "" = todos

  const chipStyle = (active) => `
    flex:0 0 auto;padding:6px 12px;border-radius:999px;font-size:13px;cursor:pointer;
    border:1px solid ${active ? "var(--accent)" : "var(--border)"};
    background:${active ? "var(--accent)" : "transparent"};
    color:${active ? "var(--bg)" : "var(--text-muted)"};
    white-space:nowrap;font-weight:${active ? "600" : "500"};
  `.replace(/\s+/g, " ");

  const renderChips = () => {
    const presentMuscles = [...new Set(allExercises.map(e => e.primary_muscle))].sort(
      (a, b) => (MUSCLE_LABEL[a] || a).localeCompare(MUSCLE_LABEL[b] || b)
    );
    chipsEl.innerHTML = "";
    const all = el(`<button data-muscle="" style="${chipStyle(activeMuscle === "")}">Todos</button>`);
    chipsEl.appendChild(all);
    for (const m of presentMuscles) {
      const b = el(`<button data-muscle="${esc(m)}" style="${chipStyle(activeMuscle === m)}">${esc(MUSCLE_LABEL[m] || m)}</button>`);
      chipsEl.appendChild(b);
    }
    chipsEl.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        activeMuscle = btn.dataset.muscle;
        renderChips();
        applyFilters();
      });
    });
  };

  const renderList = (items) => {
    if (items.length === 0) {
      resultsEl.innerHTML = `<div class="empty-state" style="padding:40px 0;">Sin resultados</div>`;
      return;
    }
    resultsEl.innerHTML = "";
    for (const ex of items) {
      const thumb = ex.image_path
        ? `<img src="${esc(ex.image_path)}" loading="lazy" alt="" style="width:48px;height:48px;border-radius:8px;object-fit:cover;background:var(--bg-elev-2);">`
        : `<div class="ex-icon" style="width:48px;height:48px;display:flex;align-items:center;justify-content:center;border-radius:8px;background:var(--bg-elev-2);">${icons.dumbbell}</div>`;
      const muscleEs = MUSCLE_LABEL[ex.primary_muscle] || ex.primary_muscle;
      const item = el(`
        <button class="list-item" style="width:100%;text-align:left;border:0;display:flex;align-items:center;gap:12px;">
          ${thumb}
          <div class="body" style="flex:1;min-width:0;">
            <div class="title" style="color:var(--text);font-size:14.5px;">${esc(ex.name)}</div>
            <div class="meta">${esc(muscleEs)} · ${esc(ex.equipment)}${ex.is_custom ? " · custom" : ""}</div>
          </div>
        </button>
      `);
      item.addEventListener("click", () => { s.close(); onPick(ex); });
      resultsEl.appendChild(item);
    }
  };

  const applyFilters = () => {
    const term = searchInput.value.trim().toLowerCase();
    let items = allExercises;
    if (activeMuscle) items = items.filter(e => e.primary_muscle === activeMuscle);
    if (term) items = items.filter(e => e.name.toLowerCase().includes(term));
    renderList(items);
  };

  searchInput.addEventListener("input", debounce(applyFilters, 100));

  // cargar lista
  const loadList = async () => {
    try {
      allExercises = await api.listExercises({ limit: 500 });
      renderChips();
      renderList(allExercises);
      searchInput.focus();
    } catch (e) {
      resultsEl.innerHTML = `<div class="empty-state">Error cargando ejercicios</div>`;
      toast(e.detail || "Error", "error");
    }
  };

  // crear ejercicio nuevo
  body.querySelector("#create-ex").addEventListener("click", () => {
    showCreateForm(s.body, async (newEx) => {
      // recarga la lista y selecciona el nuevo
      allExercises = await api.listExercises({ limit: 500 });
      renderChips();
      applyFilters();
      s.close();
      onPick(newEx);
    });
  });

  await loadList();
}

function showCreateForm(container, onCreated) {
  const muscleOptions = MUSCLES.map(m =>
    `<option value="${m}">${m}</option>`
  ).join("");
  const equipOptions = EQUIPMENTS.map(e =>
    `<option value="${e}">${e}</option>`
  ).join("");

  const form = el(`
    <div style="padding:4px 0;">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
        <button class="icon-btn" id="back-btn">${icons.arrowLeft}</button>
        <span style="font-weight:600;font-size:15px;">Nuevo ejercicio</span>
      </div>

      <div class="form-field">
        <label>Nombre</label>
        <input type="text" id="ex-name" placeholder="Ej: Curl Predicador" autocapitalize="words">
      </div>

      <div class="form-field">
        <label>Músculo principal</label>
        <select id="ex-muscle">${muscleOptions}</select>
      </div>

      <div class="form-field">
        <label>Equipo</label>
        <select id="ex-equip">${equipOptions}</select>
      </div>

      <div class="form-error hidden" id="ex-err"></div>

      <button class="btn btn-primary btn-block" id="ex-save">Guardar ejercicio</button>
    </div>
  `);

  // guardar estado de scroll y reemplazar contenido
  const prev = container.innerHTML;
  container.replaceChildren(form);

  form.querySelector("#back-btn").addEventListener("click", () => {
    container.innerHTML = prev;
  });

  form.querySelector("#ex-save").addEventListener("click", async () => {
    const name = form.querySelector("#ex-name").value.trim();
    const muscle = form.querySelector("#ex-muscle").value;
    const equip = form.querySelector("#ex-equip").value;
    const errEl = form.querySelector("#ex-err");

    if (!name) {
      errEl.textContent = "El nombre es obligatorio";
      errEl.classList.remove("hidden");
      return;
    }

    const btn = form.querySelector("#ex-save");
    btn.disabled = true;
    btn.textContent = "Guardando...";

    try {
      const ex = await api.createExercise({
        name,
        primary_muscle: muscle,
        equipment: equip,
      });
      toast(`"${ex.name}" creado`, "success");
      await onCreated(ex);
    } catch (e) {
      errEl.textContent = e.detail || "Error creando ejercicio";
      errEl.classList.remove("hidden");
      btn.disabled = false;
      btn.textContent = "Guardar ejercicio";
    }
  });
}