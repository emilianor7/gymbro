// Hash router minimal con params en path.

const routes = [];

export function route(pattern, handler) {
  // pattern: "/routines/:id"
  const keys = [];
  const regex = new RegExp(
    "^" +
    pattern.replace(/:([a-zA-Z_]+)/g, (_, k) => {
      keys.push(k);
      return "([^/]+)";
    }) +
    "$"
  );
  routes.push({ regex, keys, handler });
}

export function navigate(path) {
  if (location.hash === "#" + path) {
    // mismo hash, dispara manualmente
    handleRoute();
  } else {
    location.hash = "#" + path;
  }
}

export function start() {
  window.addEventListener("hashchange", handleRoute);
  handleRoute();
}

function handleRoute() {
  const hash = location.hash.slice(1) || "/";
  for (const r of routes) {
    const m = hash.match(r.regex);
    if (m) {
      const params = {};
      r.keys.forEach((k, i) => params[k] = decodeURIComponent(m[i + 1]));
      r.handler(params);
      return;
    }
  }
  // 404 -> a routines si esta logueado, sino login
  if (location.hash !== "#/") navigate("/");
}

export function currentPath() {
  return location.hash.slice(1) || "/";
}
