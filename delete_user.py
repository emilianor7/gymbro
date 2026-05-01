"""
Borrar un usuario y todos sus datos de GymBro.
Uso:
  python delete_user.py list
  python delete_user.py delete emiliano
  python delete_user.py delete-id 3
"""
import sys
from sqlmodel import Session, select
from app.database import engine, init_db
from app.models import (
    User, Exercise, Routine, RoutineExercise, RoutineSet,
    WorkoutSession, SessionExercise, SessionSet,
)


def list_users():
    with Session(engine) as db:
        users = db.exec(select(User).order_by(User.id)).all()
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'AI'}")
        print("-" * 65)
        for u in users:
            ai = "SI" if u.ai_enabled else "no"
            print(f"{u.id:<5} {u.username:<20} {u.email:<30} {ai}")


def delete_user(user: User, db: Session):
    print(f"\nBorrando usuario: {user.username} ({user.email}) id={user.id}")

    # session sets
    sessions = db.exec(select(WorkoutSession).where(WorkoutSession.user_id == user.id)).all()
    total_sessions = len(sessions)
    for ws in sessions:
        ses_exs = db.exec(select(SessionExercise).where(SessionExercise.session_id == ws.id)).all()
        for se in ses_exs:
            db.exec(select(SessionSet).where(SessionSet.session_exercise_id == se.id))
            sets = db.exec(select(SessionSet).where(SessionSet.session_exercise_id == se.id)).all()
            for s in sets:
                db.delete(s)
            db.delete(se)
        db.delete(ws)
    print(f"  Sesiones borradas: {total_sessions}")

    # rutinas
    routines = db.exec(select(Routine).where(Routine.owner_id == user.id)).all()
    total_routines = len(routines)
    for r in routines:
        res = db.exec(select(RoutineExercise).where(RoutineExercise.routine_id == r.id)).all()
        for re in res:
            sets = db.exec(select(RoutineSet).where(RoutineSet.routine_exercise_id == re.id)).all()
            for s in sets:
                db.delete(s)
            db.delete(re)
        db.delete(r)
    print(f"  Rutinas borradas: {total_routines}")

    # ejercicios custom
    custom_exs = db.exec(select(Exercise).where(Exercise.owner_id == user.id)).all()
    total_ex = len(custom_exs)
    for ex in custom_exs:
        db.delete(ex)
    print(f"  Ejercicios custom borrados: {total_ex}")

    db.delete(user)
    db.commit()
    print(f"  Usuario '{user.username}' eliminado correctamente.")


def find_and_delete(identifier: str, by_id: bool = False):
    with Session(engine) as db:
        if by_id:
            user = db.get(User, int(identifier))
        else:
            user = db.exec(select(User).where(User.username == identifier)).first()

        if not user:
            print(f"Usuario no encontrado: {identifier}")
            sys.exit(1)

        print(f"Vas a borrar: {user.username} ({user.email})")
        confirm = input("Confirmar? (escribe SI para continuar): ")
        if confirm.strip() != "SI":
            print("Cancelado.")
            sys.exit(0)

        delete_user(user, db)


if __name__ == "__main__":
    init_db()

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        list_users()
    elif cmd == "delete" and len(sys.argv) == 3:
        find_and_delete(sys.argv[2])
    elif cmd == "delete-id" and len(sys.argv) == 3:
        find_and_delete(sys.argv[2], by_id=True)
    else:
        print(__doc__)
        sys.exit(1)
