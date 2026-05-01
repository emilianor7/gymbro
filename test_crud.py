"""Smoke test del CRUD entero. Crea user, rutina, sesion, registra sets, valida historial."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session, select
from app.database import engine, init_db
from app.models import User, Exercise
from app.enums import MuscleGroup, Equipment, SetType
from app import crud
from app.exceptions import PermissionDeniedError, ConflictError, ValidationError, NotFoundError


def fresh_db():
    """Borra y recrea para test limpio."""
    from app.database import DB_PATH
    if DB_PATH.exists():
        DB_PATH.unlink()
    for ext in ("-wal", "-shm"):
        p = DB_PATH.parent / (DB_PATH.name + ext)
        if p.exists():
            p.unlink()
    init_db()
    # seed catalogo
    from seed import seed
    seed()


def main():
    fresh_db()

    with Session(engine) as db:
        # 1. crear users
        emi = crud.users.create_user(db, "emi", "emi@local", "secreta1")
        otro = crud.users.create_user(db, "otro", "otro@local", "secreta2")
        print(f"OK users: emi.id={emi.id}, otro.id={otro.id}")

        # validar duplicado
        try:
            crud.users.create_user(db, "EMI", "x@x", "secreta3")
            raise AssertionError("deberia haber fallado")
        except ConflictError:
            print("OK conflict en username duplicado")

        # auth
        assert crud.users.authenticate(db, "emi", "secreta1") is not None
        assert crud.users.authenticate(db, "emi", "wrong") is None
        print("OK auth")

        # 2. listar catalogo
        all_ex = crud.exercises.list_exercises(db, emi.id)
        print(f"OK catalogo global: {len(all_ex)} ejercicios visibles para emi")

        # crear custom
        custom = crud.exercises.create_custom_exercise(
            db, emi.id, "Biceps Supino Alternado C/Man",
            MuscleGroup.BICEPS, equipment=Equipment.DUMBBELL,
        )
        print(f"OK custom exercise: id={custom.id}, is_custom={custom.is_custom}")

        # otro user no lo ve
        otro_view = crud.exercises.list_exercises(db, otro.id, only_custom=True)
        assert len(otro_view) == 0
        emi_view = crud.exercises.list_exercises(db, emi.id, only_custom=True)
        assert len(emi_view) == 1
        print("OK aislamiento de customs entre users")

        # otro user no puede acceder al custom de emi
        try:
            crud.exercises.get_exercise(db, custom.id, otro.id)
            raise AssertionError()
        except PermissionDeniedError:
            print("OK permission denied cross-user")

        # 3. crear rutina Upper B
        upper = crud.routines.create_routine(db, emi.id, "Upper B")
        jalon = db.exec(select(Exercise).where(Exercise.name == "Jalon al Pecho Agarre Neutro Cerrado")).first()
        remo = db.exec(select(Exercise).where(Exercise.name == "Remo Sentado con Cable")).first()

        re_jalon = crud.routines.add_exercise_to_routine(db, upper.id, jalon.id, emi.id, rest_seconds=90)
        re_remo = crud.routines.add_exercise_to_routine(db, upper.id, remo.id, emi.id, rest_seconds=90)
        print(f"OK rutina con 2 ejercicios, orders: {re_jalon.order_index}, {re_remo.order_index}")

        # sets jalon como en el screenshot
        for kg, reps in [(70, 10), (80, 9), (80, 8), (80, 7)]:
            crud.routines.add_set(db, re_jalon.id, emi.id, target_kg=kg, target_reps=reps)
        for kg, reps in [(50, 12), (60, 10), (60, 10)]:
            crud.routines.add_set(db, re_remo.id, emi.id, target_kg=kg, target_reps=reps)

        full = crud.routines.get_routine(db, upper.id, emi.id)
        print(f"OK rutina con detalles:")
        for re in full.exercises:
            print(f"   [{re.order_index}] {re.exercise.name} ({len(re.sets)} sets)")

        # 4. reorder
        crud.routines.reorder_routine_exercises(db, upper.id, emi.id, [re_remo.id, re_jalon.id])
        full = crud.routines.get_routine(db, upper.id, emi.id)
        assert full.exercises[0].id == re_remo.id
        print("OK reorder")

        # restaurar orden original
        crud.routines.reorder_routine_exercises(db, upper.id, emi.id, [re_jalon.id, re_remo.id])

        # 5. iniciar workout session desde rutina
        ws = crud.sessions.start_session(db, emi.id, routine_id=upper.id)
        ws_full = crud.sessions.get_session(db, ws.id, emi.id)
        total_sets = sum(len(se.sets) for se in ws_full.exercises)
        print(f"OK session iniciada: {len(ws_full.exercises)} ejercicios, {total_sets} sets como targets")

        # 6. loggear sets reales
        first_ex = ws_full.exercises[0]
        for ss in first_ex.sets:
            crud.sessions.log_set(db, ss.id, emi.id, kg=ss.kg, reps=ss.reps - 1, rpe=8.5)
        print(f"OK loggeados {len(first_ex.sets)} sets del primer ejercicio")

        # 7. agregar set extra al vuelo
        extra = crud.sessions.add_session_set(db, first_ex.id, emi.id, kg=60, reps=10, set_type=SetType.DROPSET)
        crud.sessions.log_set(db, extra.id, emi.id, kg=60, reps=10)
        print(f"OK dropset agregado al vuelo: set_number={extra.set_number}")

        # 8. finalizar
        ws_done = crud.sessions.finish_session(db, ws.id, emi.id)
        assert ws_done.finished_at is not None
        print(f"OK session finalizada en {ws_done.finished_at}")

        # no se puede modificar despues
        try:
            crud.sessions.log_set(db, first_ex.sets[0].id, emi.id, kg=100, reps=5)
            raise AssertionError()
        except ConflictError:
            print("OK no se puede loggear en session finalizada")

        # 9. historial y PR
        hist = crud.sessions.history_for_exercise(db, emi.id, jalon.id)
        print(f"OK historial jalon: {len(hist)} apariciones")
        pr = crud.sessions.personal_record(db, emi.id, jalon.id)
        print(f"OK PR jalon: {pr.kg}kg x {pr.reps}")

        # 10. otro user no ve la rutina
        try:
            crud.routines.get_routine(db, upper.id, otro.id)
            raise AssertionError()
        except PermissionDeniedError:
            print("OK rutina aislada entre users")

        # 11. delete cascada
        crud.routines.delete_routine(db, upper.id, emi.id)
        try:
            crud.routines.get_routine(db, upper.id, emi.id)
            raise AssertionError()
        except NotFoundError:
            print("OK rutina borrada")
        # la sesion sigue existiendo (no se borra historial al borrar rutina)
        ws_check = crud.sessions.get_session(db, ws.id, emi.id, with_details=False)
        assert ws_check is not None
        print("OK historial preservado tras borrar rutina")

    print("\n=== TODOS LOS TESTS OK ===")


if __name__ == "__main__":
    main()
