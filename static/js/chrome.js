import { el, icons } from "./ui.js";
import { currentPath } from "./router.js";

export function bottomNav() {
  const path = currentPath();
  const isActive = (p) => path.startsWith(p) ? "active" : "";

  return el(`
    <nav class="bottom-nav">
      <a href="#/routines" class="${isActive('/routines')}">
        ${icons.list}<span>Rutinas</span>
      </a>
      <a href="#/workout" class="${isActive('/workout')}">
        ${icons.dumbbell}<span>Entreno</span>
      </a>
      <a href="#/coach" class="${isActive('/coach')}">
        ${icons.brain}<span>Coach</span>
      </a>
      <a href="#/history" class="${isActive('/history')}">
        ${icons.history}<span>Historial</span>
      </a>
      <a href="#/profile" class="${isActive('/profile')}">
        ${icons.user}<span>Perfil</span>
      </a>
    </nav>
  `);
}

export function appHeader({ title, left, right }) {
  const header = el(`
    <header class="app-header">
      <div class="left"></div>
      <h1>${title || ""}</h1>
      <div class="right"></div>
    </header>
  `);
  if (left) header.querySelector(".left").appendChild(left);
  if (right) header.querySelector(".right").appendChild(right);
  return header;
}
