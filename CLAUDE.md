# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

GymBro: gym workout tracker (rutinas, sesiones en vivo, historial, stats, Coach IA premium). Single Python process serving both the JSON API and the static SPA. Deployed on a Raspberry Pi 5 behind Caddy at https://gymbro.lat as the `gymbro` systemd unit. See `proyecto.md` for a fuller narrative overview (Spanish).

## Stack

- **Backend**: FastAPI + SQLModel + SQLite with WAL (`app/database.py` sets pragmas on every connect).
- **Frontend**: Vanilla JS ES modules, no build step, no npm. Hash-based router in `static/js/router.js`, dispatch in `static/js/app.js`. Anything you change in `static/` is live on the next page reload.
- **Auth**: PBKDF2-HMAC-SHA256 (`app/security.py`), JWT in `localStorage`, `Authorization: Bearer` header.
- **AI**: Gemini 2.5 Flash via `google-genai` (`app/ai/`), gated by `User.ai_enabled` through `require_ai` dep.

## Commands

```bash
# Run the API + SPA locally (defaults to 0.0.0.0:5999, override via API_PORT in .env)
python run.py

# Seed the global exercise catalog (idempotent)
python seed.py

# Manage premium AI flag per user
python manage_ai.py list
python manage_ai.py enable <username>
python manage_ai.py disable <username>
python manage_ai.py enable-email <email>

# Delete a user and all their data (cascades)
python delete_user.py list
python delete_user.py delete <username>

# Smoke tests — these are scripts, not pytest. Each one is run directly:
python test_crud.py        # in-process; wipes data/gym.db
python test_api.py         # E2E HTTP; expects the API running on 127.0.0.1:5999

# On the Pi (systemd)
sudo systemctl restart gymbro
sudo systemctl status gymbro
journalctl -u gymbro -f
```

There is **no test runner, linter, or formatter configured** — don't invent `pytest`, `ruff`, etc. invocations. `test_crud.py` and `test_api.py` are throwaway smoke scripts; `test_crud.py` deletes `data/gym.db` when it runs, so don't run it against a DB you care about.

## Architecture

### Layering (server)

`app/api/routers/*` → `app/crud/*` → `app/models.py` (SQLModel). Routers do auth + validation; CRUD owns SQL and raises domain exceptions from `app/exceptions.py` (`NotFoundError`, `PermissionDeniedError`, `ValidationError`, `ConflictError`). `app/api/main.py` maps each exception class to an HTTP status — **raise these from CRUD, don't `raise HTTPException` there**. Routers can raise `HTTPException` for transport concerns (auth) but prefer domain exceptions for business rules.

Dependencies live in `app/api/deps.py`: `DbDep`, `CurrentUser`, `RequireAI`. Use them as `Annotated` type aliases on route signatures.

### Naming quirks worth knowing

The sessions modules are intentionally named `sessions_crud.py` and `sessions_router.py` (not `sessions.py`) because plain `sessions.py` is gitignored — old files of that name are blocked at `.gitignore` lines 10–12. If you create a new module, don't reintroduce a bare `sessions.py`.

### Data model invariants (`app/models.py`)

- `Exercise.owner_id IS NULL` ⇒ part of the global catalog; non-null ⇒ a user-custom exercise. Both live in the same table and are queried together with a union pattern.
- Templates vs. executions are separate trees: `Routine → RoutineExercise → RoutineSet` is the plan; `WorkoutSession → SessionExercise → SessionSet` is what actually happened. Don't fold them.
- `WorkoutSession.routine_id` and `Routine.folder_id` use `ON DELETE SET NULL` so deleting a routine or folder never destroys history. Keep that contract when changing the schema.
- Cascade deletes are wired via `sa_relationship_kwargs={"cascade": "all, delete-orphan"}` on relationships — deleting a `Routine` removes its `RoutineExercise`/`RoutineSet` rows automatically; don't manually delete children.
- `RoutineShareLink` backs public `/import/<token>` URLs (the only unauthenticated app route besides `/login`).

### Frontend structure

- `static/js/app.js`: hash router registration; `requireAuth` wraps protected routes.
- `static/js/api.js`: HTTP client; injects JWT; centralizes the base URL.
- `static/js/ui.js`: shared helpers (`el`, `toast`, `sheet`, `confirm`, icons, `fmtDuration`).
- `static/js/chrome.js`: app header + 5-tab bottom nav, rendered by views.
- `static/js/views/*`: one file per route. `workout.js` is the most complex (live timer, volume, PR detection, rest countdown with vibration, long-press to delete sets, 3-dot menu for reorder/replace/remove).

### Schema migrations

**No Alembic.** `init_db()` calls `SQLModel.metadata.create_all` at startup, which only adds missing tables — it does not alter existing columns. If you change a model in a way that's not purely additive (renamed column, changed type, new NOT NULL), expect to need a manual SQLite migration or to wipe `data/gym.db`. Flag this to the user when it comes up.

### Config & secrets

`.env` is loaded by `app/config.py` without `python-dotenv`. If `JWT_SECRET` is missing it is generated and **appended to `.env`** on first boot — be aware when editing that file by hand. `.env`, `data/`, and `*.db*` are gitignored.

## Conventions

- Comments and user-facing strings are in Spanish; keep that idiom when adding new ones.
- Frontend is intentionally zero-build. Don't add a bundler, npm, or TypeScript without asking.
- No external crypto deps — `app/security.py` uses stdlib `hashlib`. Keep it that way.
