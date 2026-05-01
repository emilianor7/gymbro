import { api } from "./api.js";
import { el, esc, sheet, debounce, toast, icons } from "./ui.js";

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
      <div class="sheet-search" style="margin:0 0 12px;">
        <input type="text" id="search" placeholder="Buscar ejercicio..." autocomplete="off" autocapitalize="none">
      </div>
      <div id="results"></div>
    </div>
  `);

  const s = sheet({ title: "Agregar ejercicio", body });
  const searchInput = body.querySelector("#search");
  const resultsEl = body.querySelector("#results");

  let allExercises = [];

  const renderList = (items) => {
    if (items.length === 0) {
      resultsEl.innerHTML = `<div class="empty-state" style="padding:40px 0;">Sin resultados</div>`;
      return;
    }
    resultsEl.innerHTML = "";
    for (const ex of items) {
      const item = el(`
        <button class="list-item" style="width:100%;text-align:left;border:0;">
          <div class="card-header" style="padding:0;">
            <div class="ex-icon">${icons.dumbbell}</div>
          </div>
          <div class="body">
            <div class="title" style="color:var(--text);font-size:14.5px;">${esc(ex.name)}</div>
            <div class="meta">${esc(ex.primary_muscle)} · ${esc(ex.equipment)}${ex.is_custom ? " · custom" : ""}</div>
          </div>
        </button>
      `);
      item.addEventListener("click", () => { s.close(); onPick(ex); });
      resultsEl.appendChild(item);
    }
  };

  const filter = (q) => {
    const term = q.trim().toLowerCase();
    if (!term) return renderList(allExercises);
    renderList(allExercises.filter(e => e.name.toLowerCase().includes(term)));
  };

  searchInput.addEventListener("input", debounce(() => filter(searchInput.value), 100));

  // cargar lista
  const loadList = async () => {
    try {
      allExercises = await api.listExercises({ limit: 500 });
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
      renderList(allExercises);
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