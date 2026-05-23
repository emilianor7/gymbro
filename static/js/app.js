import { route, start, navigate } from "./router.js";
import { auth } from "./api.js";

import * as login from "./views/login.js";
import * as routines from "./views/routines.js";
import * as routineEdit from "./views/routine_edit.js";
import * as workout from "./views/workout.js";
import * as entrenar from "./views/entrenar.js";
import * as history from "./views/history.js";
import * as profile from "./views/profile.js";
import * as importRoutine from "./views/import_routine.js";

const app = document.getElementById("app");

const requireAuth = (handler) => (params) => {
  if (!auth.isAuthed) {
    navigate("/login");
    return;
  }
  handler(app, params);
};

route("/", () => {
  if (auth.isAuthed) navigate("/routines");
  else navigate("/login");
});

route("/login", () => login.render(app));

route("/routines", requireAuth((app) => routines.render(app)));
route("/routines/:id", requireAuth((app, p) => routineEdit.render(app, p)));

route("/workout", requireAuth((app) => entrenar.render(app)));
route("/workout/:id", requireAuth((app, p) => workout.render(app, p)));

route("/history", requireAuth((app) => history.render(app)));
route("/coach", requireAuth((app) => coach.render(app)));
route("/profile", requireAuth((app) => profile.render(app)));

// ruta publica para importar rutinas compartidas
route("/import/:token", (params) => importRoutine.render(app, params));

start();
