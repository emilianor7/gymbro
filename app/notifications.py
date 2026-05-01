import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# asegurar que el .env este cargado
from .config import _load_env, _ensure_secret
_load_env()
_ensure_secret()


def _config():
    return {
        "host": os.environ.get("SMTP_HOST", ""),
        "port": int(os.environ.get("SMTP_PORT", "465")),
        "user": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "notify_email": os.environ.get("NOTIFY_EMAIL", ""),
    }


def send_new_user_notification(username: str, email: str, ip: str = "desconocida"):
    cfg = _config()
    if not cfg["host"] or not cfg["notify_email"]:
        print("[notify] SMTP no configurado, omitiendo notificacion")
        return

    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[GymBro] Nuevo usuario: {username}"
    msg["From"] = cfg["user"]
    msg["To"] = cfg["notify_email"]

    body = f"""
Nuevo usuario registrado en GymBro

Usuario:  {username}
Email:    {email}
IP:       {ip}
Fecha:    {now}

Para activar Coach IA:
  python manage_ai.py enable {username}

-- GymBro
"""
    msg.attach(MIMEText(body, "plain"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"], context=context) as server:
            server.login(cfg["user"], cfg["password"])
            server.sendmail(cfg["user"], cfg["notify_email"], msg.as_string())
        print(f"[notify] Email enviado para nuevo usuario: {username}")
    except Exception as e:
        print(f"[notify] Error enviando email: {e}")
