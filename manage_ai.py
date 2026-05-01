"""
Gestionar acceso a funciones de IA por usuario.
Uso:
  python manage_ai.py list
  python manage_ai.py enable emiliano
  python manage_ai.py disable emiliano
  python manage_ai.py enable-email tu@email.com
"""
import sys
from sqlmodel import Session, select
from app.database import engine, init_db
from app.models import User


def list_users():
    with Session(engine) as db:
        users = db.exec(select(User).order_by(User.id)).all()
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'AI'}")
        print("-" * 60)
        for u in users:
            ai = "✓ ACTIVO" if u.ai_enabled else "✗ bloqueado"
            print(f"{u.id:<5} {u.username:<20} {u.email:<30} {ai}")


def set_ai(identifier: str, enabled: bool, by_email: bool = False):
    with Session(engine) as db:
        if by_email:
            user = db.exec(select(User).where(User.email == identifier)).first()
        else:
            user = db.exec(select(User).where(User.username == identifier)).first()

        if not user:
            print(f"Usuario no encontrado: {identifier}")
            sys.exit(1)

        user.ai_enabled = enabled
        db.add(user)
        db.commit()
        status = "ACTIVADO" if enabled else "DESACTIVADO"
        print(f"IA {status} para {user.username} ({user.email})")


if __name__ == "__main__":
    init_db()

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        list_users()
    elif cmd == "enable" and len(sys.argv) == 3:
        set_ai(sys.argv[2], True)
    elif cmd == "disable" and len(sys.argv) == 3:
        set_ai(sys.argv[2], False)
    elif cmd == "enable-email" and len(sys.argv) == 3:
        set_ai(sys.argv[2], True, by_email=True)
    elif cmd == "disable-email" and len(sys.argv) == 3:
        set_ai(sys.argv[2], False, by_email=True)
    else:
        print(__doc__)
        sys.exit(1)
