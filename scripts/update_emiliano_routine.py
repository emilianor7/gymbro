"""
Aplica ajustes de hipertrofia a la rutina de 5 dias de emiliano:
- Top sets pesados (6-8 reps, 4 sets) en compuestos principales
- Sube laterales a 4 sets
- Elimina Aperturas en Polea del Lunes (redundancia de pecho)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session, select

from app.database import engine
from app.enums import SetType
from app.models import RoutineExercise, RoutineSet


# (routine_exercise_id, sets_objetivo, reps_objetivo)
UPDATES = [
    # Lunes
    (63, 4, 8),   # Press de pecho en maquina: 3x10 -> 4x8
    (66, 4, 15),  # Vuelo lateral: 3x15 -> 4x15
    # Martes
    (70, 4, 8),   # Remo pecho apoyado: 3x10 -> 4x8
    (71, 4, 10),  # Jalon al pecho: 3x10 -> 4x10
    # Jueves
    (75, 4, 8),   # Prensa 45: 4x10 -> 4x8
    # Viernes
    (79, 4, 8),   # Jalon al Pecho Neutro: 3x10 -> 4x8
    (81, 4, 8),   # Press Inclinado: 3x10 -> 4x8
    # Sabado
    (86, 4, 8),   # Hack squat: 3x10 -> 4x8
    (87, 4, 8),   # Hip thrust: 3x10 -> 4x8
]

# routine_exercise_id a eliminar (con sus sets)
DELETIONS = [98]  # Aperturas en Polea (Lunes, redundante con peck deck + DBs)


def main() -> None:
    with Session(engine) as db:
        # 1) Eliminar ejercicios
        for re_id in DELETIONS:
            re = db.get(RoutineExercise, re_id)
            if re:
                # borrar sets manualmente porque no hay cascade FK a nivel SQLite
                for s in db.exec(
                    select(RoutineSet).where(RoutineSet.routine_exercise_id == re_id)
                ).all():
                    db.delete(s)
                db.delete(re)
                print(f"Eliminado routine_exercise {re_id}")
        db.commit()

        # 2) Actualizar sets / reps
        for re_id, target_sets, target_reps in UPDATES:
            existing = sorted(
                db.exec(
                    select(RoutineSet).where(RoutineSet.routine_exercise_id == re_id)
                ).all(),
                key=lambda s: s.set_number,
            )

            # Actualizar reps de los sets existentes
            for s in existing:
                s.target_reps = target_reps
                db.add(s)

            # Sumar sets faltantes
            current = len(existing)
            if target_sets > current:
                for n in range(current + 1, target_sets + 1):
                    db.add(
                        RoutineSet(
                            routine_exercise_id=re_id,
                            set_number=n,
                            set_type=SetType.NORMAL,
                            target_reps=target_reps,
                        )
                    )
            elif target_sets < current:
                # Sacar los de mas alto numero
                for s in existing[target_sets:]:
                    db.delete(s)

            print(f"re_id {re_id}: {target_sets}x{target_reps}")
        db.commit()
        print("OK")


if __name__ == "__main__":
    main()
