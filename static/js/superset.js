/**
 * Superseries.
 *
 * El modelo no las guarda como tal: se declaran con un prefijo en la nota del
 * ejercicio, y los miembros de la serie van consecutivos en la rutina.
 *
 *   "SUPERSERIE A1 - seguido y sin descanso con triceps con soga. RIR 1-2..."
 *   "SUPERSERIE A2 - viene de el curl. Recien al terminar esta, descansar..."
 *
 * La letra agrupa (A, B, C...) y el numero es la posicion dentro del bloque.
 */

const RE_SUPERSET = /^\s*SUPER\s?SERIE\s+([A-Z])\s*(\d+)\s*[-–—:.]?\s*/i;

/** Devuelve {letter, pos, rest} o null si la nota no declara superserie. */
export function parseSuperset(note) {
  if (!note) return null;
  const m = RE_SUPERSET.exec(note);
  if (!m) return null;
  return {
    letter: m[1].toUpperCase(),
    pos: parseInt(m[2], 10),
    rest: note.slice(m[0].length),   // la nota sin el prefijo
  };
}

/**
 * Agrupa una lista de ejercicios en bloques consecutivos.
 * Devuelve [{ letter: "A", items: [...] }, { letter: null, items: [uno] }, ...]
 * Un bloque de un solo miembro no se considera superserie (letter = null).
 */
export function groupSupersets(items, getNote) {
  const groups = [];
  for (const item of items) {
    const ss = parseSuperset(getNote(item));
    const last = groups[groups.length - 1];
    if (ss && last && last.letter === ss.letter) {
      last.items.push(item);
    } else {
      groups.push({ letter: ss ? ss.letter : null, items: [item] });
    }
  }
  // un miembro solo no es superserie
  for (const g of groups) if (g.items.length < 2) g.letter = null;
  return groups;
}

/** Contenedor visual de un bloque de superserie. */
export function supersetWrapper(letter, count) {
  const wrap = document.createElement("div");
  wrap.className = "ss-group";
  const head = document.createElement("div");
  head.className = "ss-head";
  head.innerHTML =
    `<span class="ss-badge">SS ${letter}</span>` +
    `<span class="ss-text">Superserie · ${count} ejercicios seguidos, sin descanso entre medio</span>`;
  wrap.appendChild(head);
  return wrap;
}

/** Etiqueta A1 / A2 para el header del card. */
export function supersetTag(note) {
  const ss = parseSuperset(note);
  if (!ss) return "";
  return `<span class="ss-tag">${ss.letter}${ss.pos}</span>`;
}
