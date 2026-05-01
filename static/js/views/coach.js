import { api } from "../api.js";
import { el, esc, icons, toast } from "../ui.js";
import { appHeader, bottomNav } from "../chrome.js";
import { navigate } from "../router.js";

// cliente IA simple
const aiApi = {
  generate: (data) => fetchAI("/ai/generate-routine", data),
  adjust: (data) => fetchAI("/ai/adjust-routine", data),
  applyAdjustments: (data) => fetchAI("/ai/apply-adjustments", data),
  analyze: (data) => fetchAI("/ai/analyze-workout", data),
  applyFromScan: (data) => fetchAI("/ai/create-from-scan", {
    routine_base_name: data.routine_base_name,
    blocks: data.blocks,
  }),
};

async function fetchAI(path, body) {
  const token = localStorage.getItem("gymbro_token");
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok) {
    if (data.detail === "FEATURE_LOCKED") throw new Error("FEATURE_LOCKED");
    throw new Error(data.detail || `Error ${r.status}`);
  }
  return data;
}

export async function render(container) {
  // verificar si tiene IA habilitada
  const token = localStorage.getItem("gymbro_token");
  const meRes = await fetch("/auth/me", { headers: { "Authorization": `Bearer ${token}` } });
  const me = await meRes.json();

  if (!me.ai_enabled) {
    const view = el(`
      <div class="screen has-bottom-nav">
        <div id="header-slot"></div>
        <div class="content" style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:60vh;text-align:center;">
          <div style="font-size:48px;margin-bottom:16px;">🔒</div>
          <div style="font-size:20px;font-weight:700;margin-bottom:8px;">Coach IA Premium</div>
          <div style="font-size:14px;color:var(--text-muted);line-height:1.7;max-width:280px;margin-bottom:24px;">
            Genera rutinas personalizadas, ajusta pesos automaticamente y recibe analisis de tus entrenamientos con inteligencia artificial.
          </div>
          <a href="mailto:emilianor70@gmail.com?subject=Quiero activar Coach IA en GymBro" class="btn btn-primary" style="text-decoration:none;">
            Contactar para activar
          </a>
          <div style="font-size:12px;color:var(--text-faint);margin-top:12px;">te respondemos en menos de 24hs</div>
        </div>
      </div>
    `);
    view.querySelector("#header-slot").appendChild(appHeader({ title: "Coach IA" }));
    view.appendChild(bottomNav());
    container.replaceChildren(view);
    return;
  }
  const view = el(`
    <div class="screen has-bottom-nav">
      <div id="header-slot"></div>
      <div class="content">

        <!-- SCAN IMAGEN -->
        <div class="section-title">Importar rutina desde foto</div>
        <div class="card" style="padding:14px;">
          <p style="font-size:13.5px;color:var(--text-muted);margin-bottom:12px;line-height:1.6;">
            Saca una foto de tu planilla de entrenamiento y la IA extrae los ejercicios automaticamente.
          </p>
          <label class="btn btn-block" style="cursor:pointer;background:var(--bg-elev-2);">
            ${icons.plus}<span id="scan-label">Seleccionar imagen</span>
            <input type="file" id="scan-file" accept="image/*" capture="environment" style="display:none;">
          </label>
          <div id="scan-preview" class="hidden mt-4" style="text-align:center;">
            <img id="scan-img" style="max-width:100%;border-radius:var(--radius);max-height:200px;object-fit:contain;" />
          </div>
          <button class="btn btn-primary btn-block mt-3 hidden" id="btn-scan">
            ${icons.brain}<span>Escanear con IA</span>
          </button>
          <div id="scan-result" class="hidden mt-4"></div>
        </div>

        <!-- GENERAR RUTINA -->
        <div class="section-title">Generar rutina con IA</div>
        <div class="card" style="padding:14px;">
          <div class="form-field" style="margin-bottom:10px;">
            <label>Que queres lograr?</label>
            <textarea id="gen-prompt" rows="3" placeholder="Ej: hipertrofia 4 dias upper lower, soy intermedio, tengo acceso a maquinas y mancuernas" style="height:80px;padding:10px 14px;width:100%;background:var(--bg-input);border:1px solid var(--border);border-radius:var(--radius);color:var(--text);font-size:14px;resize:none;"></textarea>
          </div>
          <button class="btn btn-primary btn-block" id="btn-generate">
            ${icons.play}<span>Generar rutina</span>
          </button>
          <div id="gen-result" class="hidden mt-4"></div>
        </div>

        <!-- AJUSTAR PESOS -->
        <div class="section-title">Ajustar pesos para proxima semana</div>
        <div class="card" style="padding:14px;">
          <div class="form-field" style="margin-bottom:10px;">
            <label>Rutina a ajustar</label>
            <select id="adj-routine" style="width:100%;height:46px;padding:0 14px;border-radius:var(--radius);background:var(--bg-input);border:1px solid var(--border);color:var(--text);">
              <option value="">Cargando...</option>
            </select>
          </div>
          <button class="btn btn-block" id="btn-adjust" style="background:var(--accent-bg);color:var(--accent);">
            ${icons.history}<span>Analizar y sugerir cambios</span>
          </button>
          <div id="adj-result" class="hidden mt-4"></div>
        </div>

        <!-- ANALISIS POST-WORKOUT -->
        <div class="section-title">Analizar entrenamiento</div>
        <div class="card" style="padding:14px;">
          <div class="form-field" style="margin-bottom:10px;">
            <label>Sesion a analizar</label>
            <select id="ana-session" style="width:100%;height:46px;padding:0 14px;border-radius:var(--radius);background:var(--bg-input);border:1px solid var(--border);color:var(--text);">
              <option value="">Cargando...</option>
            </select>
          </div>
          <button class="btn btn-block" id="btn-analyze" style="background:var(--accent-bg);color:var(--accent);">
            ${icons.dumbbell}<span>Analizar sesion</span>
          </button>
          <div id="ana-result" class="hidden mt-4"></div>
        </div>

      </div>
    </div>
  `);

  view.querySelector("#header-slot").appendChild(appHeader({ title: "Coach IA" }));
  view.appendChild(bottomNav());
  container.replaceChildren(view);

  // cargar datos iniciales
  loadRoutines(view);
  loadSessions(view);

  // ---- SCAN ----
  const scanFile = view.querySelector("#scan-file");
  const scanPreview = view.querySelector("#scan-preview");
  const scanImg = view.querySelector("#scan-img");
  const btnScan = view.querySelector("#btn-scan");
  const scanLabel = view.querySelector("#scan-label");
  const scanResult = view.querySelector("#scan-result");

  scanFile.addEventListener("change", () => {
    const file = scanFile.files[0];
    if (!file) return;
    scanLabel.textContent = file.name;
    const url = URL.createObjectURL(file);
    scanImg.src = url;
    scanPreview.classList.remove("hidden");
    btnScan.classList.remove("hidden");
    scanResult.classList.add("hidden");
  });

  btnScan.addEventListener("click", async () => {
    const file = scanFile.files[0];
    if (!file) return;

    btnScan.disabled = true;
    btnScan.querySelector("span").textContent = "Escaneando...";
    scanResult.classList.add("hidden");

    try {
      const formData = new FormData();
      formData.append("file", file);
      const token = localStorage.getItem("gymbro_token");
      const r = await fetch("/ai/scan-routine", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData,
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || `Error ${r.status}`);

      scanResult.innerHTML = renderScanResult(data);
      scanResult.classList.remove("hidden");

      scanResult.querySelector("#btn-create-scan")?.addEventListener("click", async () => {
        const btn = scanResult.querySelector("#btn-create-scan");
        btn.disabled = true;
        btn.textContent = "Creando rutinas...";
        try {
          const res = await aiApi.applyFromScan(data);
          toast(`Creadas: ${res.routine_titles.join(", ")}`, "success");
          btn.textContent = "Rutinas creadas!";
          await loadRoutines(view);
        } catch (e) {
          toast(e.message || "Error", "error");
          btn.disabled = false;
          btn.textContent = "Confirmar e importar";
        }
      });
    } catch (e) {
      toast(e.message || "Error al escanear", "error");
    } finally {
      btnScan.disabled = false;
      btnScan.querySelector("span").textContent = "Escanear con IA";
    }
  });

  // ---- GENERAR ----
  view.querySelector("#btn-generate").addEventListener("click", async () => {
    const prompt = view.querySelector("#gen-prompt").value.trim();
    if (!prompt) { toast("Describe lo que queres", "error"); return; }
    const btn = view.querySelector("#btn-generate");
    const result = view.querySelector("#gen-result");
    btn.disabled = true;
    btn.querySelector("span").textContent = "Generando...";
    result.classList.add("hidden");
    try {
      const data = await aiApi.generate({ prompt, objective: "hipertrofia" });
      result.innerHTML = `
        <div style="background:var(--accent-bg);border:1px solid var(--accent);border-radius:var(--radius);padding:14px;">
          <div style="font-weight:600;color:var(--accent);margin-bottom:8px;">Rutinas creadas: ${esc(data.routine_titles.join(", "))}</div>
          <div style="font-size:13.5px;line-height:1.6;color:var(--text-muted);">${esc(data.explanation)}</div>
          <button class="btn btn-primary btn-block mt-4" onclick="location.hash='#/routines'">Ver rutinas</button>
        </div>
      `;
      result.classList.remove("hidden");
      toast("Rutinas creadas!", "success");
      await loadRoutines(view);
    } catch (e) {
      toast(e.message || "Error", "error");
    } finally {
      btn.disabled = false;
      btn.querySelector("span").textContent = "Generar rutina";
    }
  });

  // ---- AJUSTAR ----
  view.querySelector("#btn-adjust").addEventListener("click", async () => {
    const routineId = view.querySelector("#adj-routine").value;
    if (!routineId) { toast("Selecciona una rutina", "error"); return; }
    const btn = view.querySelector("#btn-adjust");
    const result = view.querySelector("#adj-result");
    btn.disabled = true;
    btn.querySelector("span").textContent = "Analizando...";
    result.classList.add("hidden");
    try {
      const data = await aiApi.adjust({ routine_id: parseInt(routineId), objective: "hipertrofia" });
      result.innerHTML = renderAdjustments(data, routineId);
      result.classList.remove("hidden");

      result.querySelector("#btn-apply")?.addEventListener("click", async () => {
        try {
          const adjustments = data.adjustments;
          await aiApi.applyAdjustments({ routine_id: parseInt(routineId), adjustments });
          toast("Ajustes aplicados a la rutina", "success");
          result.querySelector("#btn-apply").textContent = "Aplicado!";
          result.querySelector("#btn-apply").disabled = true;
        } catch (e) {
          toast(e.message || "Error aplicando", "error");
        }
      });
    } catch (e) {
      toast(e.message || "Error", "error");
    } finally {
      btn.disabled = false;
      btn.querySelector("span").textContent = "Analizar y sugerir cambios";
    }
  });

  // ---- ANALIZAR ----
  view.querySelector("#btn-analyze").addEventListener("click", async () => {
    const sessionId = view.querySelector("#ana-session").value;
    if (!sessionId) { toast("Selecciona una sesion", "error"); return; }
    const btn = view.querySelector("#btn-analyze");
    const result = view.querySelector("#ana-result");
    btn.disabled = true;
    btn.querySelector("span").textContent = "Analizando...";
    result.classList.add("hidden");
    try {
      const data = await aiApi.analyze({ session_id: parseInt(sessionId), objective: "hipertrofia" });
      result.innerHTML = renderAnalysis(data);
      result.classList.remove("hidden");
    } catch (e) {
      toast(e.message || "Error", "error");
    } finally {
      btn.disabled = false;
      btn.querySelector("span").textContent = "Analizar sesion";
    }
  });
}

async function loadRoutines(view) {
  try {
    const routines = await api.listRoutines();
    const sel = view.querySelector("#adj-routine");
    sel.innerHTML = routines.length
      ? routines.map(r => `<option value="${r.id}">${esc(r.title)}</option>`).join("")
      : `<option value="">Sin rutinas</option>`;
  } catch { /* ignorar */ }
}

async function loadSessions(view) {
  try {
    const sessions = await api.listSessions({ only_finished: true, limit: 20 });
    const sel = view.querySelector("#ana-session");
    sel.innerHTML = sessions.length
      ? sessions.map(s => `<option value="${s.id}">${esc(s.title)} - ${new Date(s.started_at).toLocaleDateString("es-AR")}</option>`).join("")
      : `<option value="">Sin sesiones finalizadas</option>`;
  } catch { /* ignorar */ }
}

function renderAdjustments(data, routineId) {
  const rows = data.adjustments.map(a => `
    <div style="border-bottom:1px solid var(--border);padding:10px 0;">
      <div style="font-weight:600;font-size:14px;margin-bottom:4px;">${esc(a.exercise_name)}</div>
      <div style="display:flex;gap:16px;font-size:13px;color:var(--text-muted);margin-bottom:4px;">
        <span>Actual: <span class="numeric">${a.current_kg ?? '—'}kg x ${a.current_reps ?? '—'}</span></span>
        <span style="color:var(--accent);">Sugerido: <span class="numeric">${a.suggested_kg ?? '—'}kg x ${a.suggested_reps ?? '—'}</span></span>
      </div>
      <div style="font-size:12.5px;color:var(--text-faint);">${esc(a.reason)}</div>
    </div>
  `).join("");

  return `
    <div style="background:var(--bg-elev-2);border-radius:var(--radius);padding:14px;">
      <div style="font-size:13.5px;line-height:1.6;color:var(--text-muted);margin-bottom:12px;">${esc(data.summary)}</div>
      ${rows}
      <button class="btn btn-primary btn-block mt-4" id="btn-apply">Aplicar ajustes a la rutina</button>
    </div>
  `;
}

function renderAnalysis(data) {
  const scoreColor = data.score >= 80 ? "var(--success)" : data.score >= 60 ? "var(--warning)" : "var(--danger)";
  const highlights = data.highlights.map(h => `<li style="margin-bottom:4px;">✓ ${esc(h)}</li>`).join("");
  const improvements = data.improvements.map(i => `<li style="margin-bottom:4px;">→ ${esc(i)}</li>`).join("");

  return `
    <div style="background:var(--bg-elev-2);border-radius:var(--radius);padding:14px;">
      <div style="text-align:center;margin-bottom:16px;">
        <div style="font-size:48px;font-weight:700;color:${scoreColor};font-family:var(--font-mono);">${data.score}</div>
        <div style="font-size:12px;color:var(--text-faint);text-transform:uppercase;letter-spacing:0.08em;">Score</div>
      </div>
      <div style="font-size:13.5px;line-height:1.7;color:var(--text-muted);margin-bottom:14px;">${esc(data.feedback)}</div>
      ${highlights ? `<ul style="list-style:none;font-size:13px;color:var(--success);margin-bottom:10px;">${highlights}</ul>` : ""}
      ${improvements ? `<ul style="list-style:none;font-size:13px;color:var(--warning);">${improvements}</ul>` : ""}
      ${data.next_session_tip ? `
        <div style="margin-top:12px;padding:10px;background:var(--accent-bg);border-radius:var(--radius);font-size:13px;color:var(--accent);">
          <strong>Proximo entreno:</strong> ${esc(data.next_session_tip)}
        </div>` : ""}
    </div>
  `;
}

function renderScanResult(data) {
  const blocksHtml = data.blocks.map(block => {
    const exRows = block.exercises.map(ex => `
      <div style="display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid var(--border);">
        <div style="font-size:13.5px;flex:1;">${esc(ex.name)}</div>
        <div style="font-size:12px;color:var(--text-muted);font-family:var(--font-mono);white-space:nowrap;margin-left:8px;">${ex.sets}x${ex.target_reps}</div>
      </div>
    `).join("");

    return `
      <div style="margin-bottom:14px;">
        <div style="font-weight:600;font-size:13px;color:var(--accent);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">${esc(block.label)}</div>
        ${exRows}
      </div>
    `;
  }).join("");

  return `
    <div style="background:var(--bg-elev-2);border-radius:var(--radius);padding:14px;">
      <div style="font-weight:600;font-size:15px;margin-bottom:4px;">${esc(data.routine_base_name)}</div>
      ${data.notes ? `<div style="font-size:12.5px;color:var(--text-muted);margin-bottom:12px;">${esc(data.notes)}</div>` : ""}
      <div style="font-size:12px;color:var(--text-faint);margin-bottom:12px;">Se van a crear ${data.blocks.length} rutina${data.blocks.length > 1 ? 's' : ''}: ${data.blocks.map(b => `${esc(data.routine_base_name)} - ${esc(b.label)}`).join(", ")}</div>
      ${blocksHtml}
      <button class="btn btn-primary btn-block mt-2" id="btn-create-scan">Confirmar e importar</button>
    </div>
  `;
}
