import re

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from ..config import CORS_ORIGINS
from ..database import init_db
from ..exceptions import NotFoundError, PermissionDeniedError, ValidationError, ConflictError
from .routers import auth, exercises, routines, folders, share
from .routers.sessions_router import router as sessions_router
from .routers.stats import router as stats_router
from ..ai.router import router as ai_router

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


app = FastAPI(
    title="GymBro API",
    version="0.1.0",
    description="API de rutinas y workouts",
)


# ============================================================
# CORS
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Excepciones de dominio -> HTTP status codes
# ============================================================
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(PermissionDeniedError)
async def permission_handler(request: Request, exc: PermissionDeniedError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


# ============================================================
# Routers
# ============================================================
app.include_router(auth.router)
app.include_router(exercises.router)
app.include_router(routines.router)
app.include_router(folders.router)
app.include_router(share.router)
app.include_router(sessions_router)
app.include_router(stats_router)
app.include_router(ai_router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


# ============================================================
# Static / SPA
# ============================================================
if STATIC_DIR.exists():
    # StaticFiles que fuerza revalidacion via ETag en cada request,
    # asi cambios en JS/CSS se ven sin cache stale.
    class NoCacheStaticFiles(StaticFiles):
        async def get_response(self, path, scope):
            resp = await super().get_response(path, scope)
            resp.headers["Cache-Control"] = "no-cache, must-revalidate"
            return resp

    app.mount("/static", NoCacheStaticFiles(directory=STATIC_DIR), name="static")

    def _static_version() -> str:
        # mtime mas reciente de cualquier .js/.css como version global
        candidates = list((STATIC_DIR / "js").rglob("*.js")) + list((STATIC_DIR / "css").rglob("*.css"))
        if not candidates:
            return "0"
        return str(int(max(p.stat().st_mtime for p in candidates)))

    _STATIC_REF_RE = re.compile(r'(["\'])(/static/[^"\']+?)\1')

    @app.get("/", include_in_schema=False)
    def root():
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        v = _static_version()
        # Cache-bust de las referencias /static/... directas en el HTML.
        # Los imports relativos dentro de los JS se revalidan via ETag.
        html = _STATIC_REF_RE.sub(
            lambda m: f'{m.group(1)}{m.group(2)}?v={v}{m.group(1)}',
            html,
        )
        return HTMLResponse(content=html, headers={"Cache-Control": "no-store"})

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon():
        ico = STATIC_DIR / "favicon.ico"
        if ico.exists():
            return FileResponse(ico)
        return JSONResponse(status_code=404, content={"detail": "no favicon"})


@app.on_event("startup")
def on_startup():
    init_db()
