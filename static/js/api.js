// API client. Auto-injecta JWT, parsea JSON, redirige a login en 401.

const TOKEN_KEY = "gymbro_token";
const USER_KEY = "gymbro_user";

export const auth = {
  get token() { return localStorage.getItem(TOKEN_KEY); },
  get user() {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  set(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  get isAuthed() { return !!this.token; },
};

class ApiError extends Error {
  constructor(status, detail) {
    super(detail || `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function request(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  if (auth.token) headers["Authorization"] = `Bearer ${auth.token}`;

  const opts = { method, headers };
  if (body !== undefined) opts.body = JSON.stringify(body);

  let res;
  try {
    res = await fetch(path, opts);
  } catch (e) {
    throw new ApiError(0, "no se pudo conectar al servidor");
  }

  if (res.status === 401) {
    auth.clear();
    if (location.hash !== "#/login") location.hash = "#/login";
    throw new ApiError(401, "sesion expirada");
  }

  if (res.status === 204) return null;

  let data = null;
  try { data = await res.json(); } catch { /* sin body */ }

  if (!res.ok) {
    const detail = data?.detail
      || (Array.isArray(data?.detail) ? data.detail.map(d => d.msg).join(", ") : null)
      || `Error ${res.status}`;
    throw new ApiError(res.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  return data;
}

export const api = {
  // auth
  register: (username, email, password) => request("POST", "/auth/register", { username, email, password }),
  login: (username, password) => request("POST", "/auth/login", { username, password }),
  me: () => request("GET", "/auth/me"),

  // exercises
  listExercises: (params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== "" && v !== null)
    ).toString();
    return request("GET", `/exercises${qs ? "?" + qs : ""}`);
  },
  createExercise: (data) => request("POST", "/exercises", data),

  // routines
  listRoutines: () => request("GET", "/routines"),
  getRoutine: (id) => request("GET", `/routines/${id}`),
  createRoutine: (data) => request("POST", "/routines", data),
  updateRoutine: (id, data) => request("PATCH", `/routines/${id}`, data),
  deleteRoutine: (id) => request("DELETE", `/routines/${id}`),

  addExerciseToRoutine: (routineId, data) => request("POST", `/routines/${routineId}/exercises`, data),
  updateRoutineExercise: (reId, data) => request("PATCH", `/routines/exercises/${reId}`, data),
  removeRoutineExercise: (reId) => request("DELETE", `/routines/exercises/${reId}`),
  reorderRoutine: (routineId, ids) => request("POST", `/routines/${routineId}/reorder`, { ordered_ids: ids }),

  addRoutineSet: (reId, data) => request("POST", `/routines/exercises/${reId}/sets`, data),
  updateRoutineSet: (setId, data) => request("PATCH", `/routines/sets/${setId}`, data),
  deleteRoutineSet: (setId) => request("DELETE", `/routines/sets/${setId}`),

  // sessions
  listSessions: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request("GET", `/sessions${qs ? "?" + qs : ""}`);
  },
  startSession: (data) => request("POST", "/sessions", data),
  getSession: (id) => request("GET", `/sessions/${id}`),
  finishSession: (id) => request("POST", `/sessions/${id}/finish`),
  discardSession: (id) => request("DELETE", `/sessions/${id}`),

  addSessionExercise: (sessionId, data) => request("POST", `/sessions/${sessionId}/exercises`, data),
  deleteSessionExercise: (seId) => request("DELETE", `/sessions/exercises/${seId}`),
  patchSessionExercise: (seId, data) => request("PATCH", `/sessions/exercises/${seId}`, data),
  addSessionSet: (seId, data) => request("POST", `/sessions/exercises/${seId}/sets`, data),
  logSet: (setId, data) => request("PATCH", `/sessions/sets/${setId}`, data),
  deleteSessionSet: (setId) => request("DELETE", `/sessions/sets/${setId}`),

  historyForExercise: (exerciseId, limit = 30) => request("GET", `/sessions/history/${exerciseId}?limit=${limit}`),
  pr: (exerciseId) => request("GET", `/sessions/pr/${exerciseId}`),
};

export { ApiError };
