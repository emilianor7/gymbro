import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"


def _load_env():
    """Carga .env si existe, sin dependencias externas."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


def _ensure_secret():
    """Si no hay JWT_SECRET, genera uno y lo persiste en .env."""
    if os.environ.get("JWT_SECRET"):
        return
    secret = secrets.token_urlsafe(48)
    os.environ["JWT_SECRET"] = secret
    with open(ENV_FILE, "a") as f:
        f.write(f"\nJWT_SECRET={secret}\n")
    print(f"[config] JWT_SECRET generado y guardado en {ENV_FILE}")


_load_env()
_ensure_secret()

JWT_SECRET: str = os.environ["JWT_SECRET"]
JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_DAYS: int = int(os.environ.get("JWT_EXPIRE_DAYS", "30"))

API_HOST: str = os.environ.get("API_HOST", "0.0.0.0")
API_PORT: int = int(os.environ.get("API_PORT", "5999"))

# CORS: por defecto abierto a LAN. Si lo expones a internet poner una lista.
CORS_ORIGINS: list[str] = os.environ.get("CORS_ORIGINS", "*").split(",")
