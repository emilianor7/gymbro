import { api } from "../api.js";
import { el, esc, icons, toast, confirm } from "../ui.js";
import { bottomNav, appHeader } from "../chrome.js";
import { navigate } from "../router.js";

const foldersApi = {
  list: () => fetchJ("GET", "/folders"),
  create: (name) => fetchJ("POST", "/folders", { name }),
  rename: (id, name) => fetchJ("PATCH", `/folders/${id}`, { name }),
  delete: (id) => fetchJ("DELETE", `/folders/${id}`),
  moveRoutine: (routineId, folderId) =>
    fetchJ("PATCH", `/folders/routines/${routineId}/move`, { folder_id: folderId }),
};

async function fetchJ(method, path, body) {
  const token = localStorage.getItem("gymbro_token");
  const r = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (r.status === 204) return null;
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || `Error ${r.status}`);
  return data;
}

export async function render(container) {
  const view = el(`
    <div class="screen has-bottom-nav">
      <div id="header-slot"></div>
      <div class="content" id="content">
        <div class="muted text-center" style="padding:40px;">Cargando...</div>
      </div>
    </div>
  `);

  view.querySelector("#header-slot").appendChild(appHeader({ title: "Rutinas", right: makePlusBtn() }));
  view.appendChild(bottomNav());
  container.replaceChildren(view);

  function makePlusBtn() {
    const btn = el(`<button class="icon-btn">${icons.plus}</button>`);
    btn.addEventListener("click", () => showCreateMenu(refresh));
    return btn;
  }

  const refresh = async () => {
    try {
      const [folders, routines] = await Promise.all([
        foldersApi.list(),
        api.listRoutines(),
      ]);
      renderContent(view.querySelector("#content"), folders, routines, refresh);
    } catch (e) {
      toast(e.message || "Error", "error");
    }
  };

  await refresh();
}

function renderContent(content, folders, routines, refresh) {
  content.innerHTML = "";

  const inFolder = new Set(routines.filter(r => r.folder_id).map(r => r.folder_id));
  const noFolder = routines.filter(r => !r.folder_id);

  // ---- FOLDERS ----
  for (const folder of folders) {
    const folderRoutines = routines.filter(r => r.folder_id === folder.id);
    const isOpen = sessionStorage.getItem(`folder_open_${folder.id}`) !== "0";

    const folderEl = el(`
      <div class="folder-block" style="margin-bottom:10px;">
        <div class="folder-header" style="display:flex;align-items:center;gap:10px;
          background:var(--bg-elev-1);border-radius:var(--radius-lg);padding:14px 16px;cursor:pointer;">
          <span style="font-size:18px;">📁</span>
          <div style="flex:1;font-weight:600;font-size:15px;">${esc(folder.name)}</div>
          <span style="font-size:12px;color:var(--text-muted);">${folderRoutines.length}</span>
          <span class="folder-chevron" style="color:var(--text-faint);transition:transform 0.2s;
            transform:rotate(${isOpen?'90':'0'}deg);">${icons.chevronRight}</span>
          <button class="icon-btn folder-menu-btn" style="width:32px;height:32px;">${icons.dots}</button>
        </div>
        <div class="folder-body" style="display:${isOpen?'block':'none'};padding:4px 0 0 12px;">
          <div class="folder-routines"></div>
          <button class="btn btn-block" style="margin-top:6px;margin-bottom:4px;
            background:var(--bg-elev-2);font-size:13px;height:36px;" data-add-to-folder>
            ${icons.plus}<span>Agregar rutina a esta carpeta</span>
          </button>
        </div>
      </div>
    `);

    const header = folderEl.querySelector(".folder-header");
    const body = folderEl.querySelector(".folder-body");
    const chevron = folderEl.querySelector(".folder-chevron");
    const routinesEl = folderEl.querySelector(".folder-routines");

    // render rutinas dentro del folder
    for (const r of folderRoutines) {
      routinesEl.appendChild(makeRoutineItem(r, folders, refresh));
    }
    if (!folderRoutines.length) {
      routinesEl.innerHTML = `<div style="padding:10px 4px;font-size:13px;color:var(--text-faint);">Vacia - agrega rutinas aqui</div>`;
    }

    // toggle abrir/cerrar
    header.addEventListener("click", (e) => {
      if (e.target.closest(".folder-menu-btn")) return;
      const open = body.style.display === "none";
      body.style.display = open ? "block" : "none";
      chevron.style.transform = open ? "rotate(90deg)" : "rotate(0deg)";
      sessionStorage.setItem(`folder_open_${folder.id}`, open ? "1" : "0");
    });

    // menu folder (3 puntos)
    folderEl.querySelector(".folder-menu-btn").addEventListener("click", (e) => {
      e.stopPropagation();
      showFolderMenu(folder, refresh);
    });

    // agregar rutina a folder
    folderEl.querySelector("[data-add-to-folder]").addEventListener("click", () => {
      showAddRoutineToFolder(folder, routines.filter(r => !r.folder_id), refresh);
    });

    content.appendChild(folderEl);
  }

  // ---- RUTINAS SIN FOLDER ----
  if (noFolder.length > 0) {
    if (folders.length > 0) {
      content.appendChild(el(`<div class="section-title">Sin carpeta</div>`));
    }
    for (const r of noFolder) {
      content.appendChild(makeRoutineItem(r, folders, refresh));
    }
  }

  if (!folders.length && !routines.length) {
    content.innerHTML = `
      <div class="empty-state">
        <div class="em-title">Sin rutinas</div>
        <div>Tocá el + para crear tu primera rutina o carpeta</div>
      </div>
    `;
  }
}

function makeRoutineItem(r, folders, refresh) {
  const item = el(`
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
      <a href="#/routines/${r.id}" class="list-item" style="flex:1;margin-bottom:0;">
        <div class="body">
          <div class="title">${esc(r.title)}</div>
        </div>
        <div class="arrow">${icons.chevronRight}</div>
      </a>
      <button class="icon-btn" style="flex-shrink:0;background:var(--bg-elev-1);border-radius:var(--radius);" data-move>
        ${icons.dots}
      </button>
    </div>
  `);

  item.querySelector("[data-move]").addEventListener("click", () => {
    showMoveMenu(r, folders, refresh);
  });

  return item;
}

function showCreateMenu(refresh) {
  const menu = el(`
    <div class="sheet-overlay">
      <div class="sheet" style="padding:8px 0 16px;">
        <div style="width:36px;height:4px;background:var(--border);border-radius:2px;margin:8px auto 16px;"></div>
        <button class="list-item" data-action="routine" style="border:0;width:100%;text-align:left;">
          <div style="font-size:20px;margin-right:4px;">${icons.dumbbell}</div>
          <div class="body"><div class="title" style="font-size:15px;">Nueva rutina</div></div>
        </button>
        <button class="list-item" data-action="folder" style="border:0;width:100%;text-align:left;">
          <div style="font-size:20px;margin-right:4px;">📁</div>
          <div class="body"><div class="title" style="font-size:15px;">Nueva carpeta</div></div>
        </button>
      </div>
    </div>
  `);
  document.body.appendChild(menu);
  document.body.style.overflow = "hidden";
  const close = () => { document.body.style.overflow = ""; menu.remove(); };
  menu.addEventListener("click", e => { if (e.target === menu) close(); });

  menu.querySelector('[data-action="routine"]').addEventListener("click", async () => {
    close();
    const title = window.prompt("Nombre de la rutina", "Nueva rutina");
    if (!title) return;
    try {
      const r = await api.createRoutine({ title: title.trim() });
      navigate(`/routines/${r.id}`);
    } catch (e) { toast(e.detail || "Error", "error"); }
  });

  menu.querySelector('[data-action="folder"]').addEventListener("click", async () => {
    close();
    const name = window.prompt("Nombre de la carpeta", "");
    if (!name) return;
    try {
      await foldersApi.create(name.trim());
      await refresh();
    } catch (e) { toast(e.message || "Error", "error"); }
  });
}

function showFolderMenu(folder, refresh) {
  const menu = el(`
    <div class="sheet-overlay">
      <div class="sheet" style="padding:8px 0 16px;">
        <div style="width:36px;height:4px;background:var(--border);border-radius:2px;margin:8px auto 12px;"></div>
        <div style="padding:4px 16px 12px;font-weight:600;font-size:15px;color:var(--text-muted);">📁 ${esc(folder.name)}</div>
        <button class="list-item" data-action="rename" style="border:0;width:100%;text-align:left;">
          <div class="body"><div class="title">Renombrar carpeta</div></div>
        </button>
        <button class="list-item" data-action="delete" style="border:0;width:100%;text-align:left;">
          <div class="body"><div class="title" style="color:var(--danger);">Eliminar carpeta</div></div>
        </button>
      </div>
    </div>
  `);
  document.body.appendChild(menu);
  document.body.style.overflow = "hidden";
  const close = () => { document.body.style.overflow = ""; menu.remove(); };
  menu.addEventListener("click", e => { if (e.target === menu) close(); });

  menu.querySelector('[data-action="rename"]').addEventListener("click", async () => {
    close();
    const name = window.prompt("Nuevo nombre", folder.name);
    if (!name || name === folder.name) return;
    try { await foldersApi.rename(folder.id, name.trim()); await refresh(); }
    catch (e) { toast(e.message || "Error", "error"); }
  });

  menu.querySelector('[data-action="delete"]').addEventListener("click", async () => {
    close();
    if (!await confirm(`¿Eliminar carpeta "${folder.name}"? Las rutinas quedan sin carpeta.`)) return;
    try { await foldersApi.delete(folder.id); await refresh(); }
    catch (e) { toast(e.message || "Error", "error"); }
  });
}

function showMoveMenu(routine, folders, refresh) {
  const opts = [
    `<button class="list-item" data-folder-id="null" style="border:0;width:100%;text-align:left;">
      <div class="body"><div class="title">Sin carpeta</div></div>
    </button>`,
    ...folders.map(f => `
      <button class="list-item" data-folder-id="${f.id}" style="border:0;width:100%;text-align:left;">
        <div style="font-size:18px;margin-right:4px;">📁</div>
        <div class="body"><div class="title">${esc(f.name)}</div></div>
        ${routine.folder_id === f.id ? `<div style="color:var(--accent);">✓</div>` : ""}
      </button>
    `)
  ].join("");

  const menu = el(`
    <div class="sheet-overlay">
      <div class="sheet" style="padding:8px 0 16px;">
        <div style="width:36px;height:4px;background:var(--border);border-radius:2px;margin:8px auto 12px;"></div>
        <div style="padding:4px 16px 12px;font-weight:600;font-size:15px;color:var(--text-muted);">Mover "${esc(routine.title)}"</div>
        ${opts}
      </div>
    </div>
  `);
  document.body.appendChild(menu);
  document.body.style.overflow = "hidden";
  const close = () => { document.body.style.overflow = ""; menu.remove(); };
  menu.addEventListener("click", e => { if (e.target === menu) close(); });

  menu.querySelectorAll("[data-folder-id]").forEach(btn => {
    btn.addEventListener("click", async () => {
      close();
      const fid = btn.dataset.folderId === "null" ? null : parseInt(btn.dataset.folderId);
      try { await foldersApi.moveRoutine(routine.id, fid); await refresh(); }
      catch (e) { toast(e.message || "Error", "error"); }
    });
  });
}

function showAddRoutineToFolder(folder, availableRoutines, refresh) {
  if (!availableRoutines.length) {
    toast("No hay rutinas sin carpeta para agregar", "error");
    return;
  }
  const opts = availableRoutines.map(r => `
    <button class="list-item" data-routine-id="${r.id}" style="border:0;width:100%;text-align:left;">
      <div class="body"><div class="title">${esc(r.title)}</div></div>
    </button>
  `).join("");

  const menu = el(`
    <div class="sheet-overlay">
      <div class="sheet" style="padding:8px 0 16px;">
        <div style="width:36px;height:4px;background:var(--border);border-radius:2px;margin:8px auto 12px;"></div>
        <div style="padding:4px 16px 12px;font-weight:600;font-size:15px;color:var(--text-muted);">Agregar a 📁 ${esc(folder.name)}</div>
        ${opts}
      </div>
    </div>
  `);
  document.body.appendChild(menu);
  document.body.style.overflow = "hidden";
  const close = () => { document.body.style.overflow = ""; menu.remove(); };
  menu.addEventListener("click", e => { if (e.target === menu) close(); });

  menu.querySelectorAll("[data-routine-id]").forEach(btn => {
    btn.addEventListener("click", async () => {
      close();
      try { await foldersApi.moveRoutine(parseInt(btn.dataset.routineId), folder.id); await refresh(); }
      catch (e) { toast(e.message || "Error", "error"); }
    });
  });
}
