"""
Crea ejercicios custom y rutina de 5 días para la usuaria 'marina'.
Idempotente: si la rutina ya existe la borra y rearma; ejercicios que ya estén no se duplican.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session, select

from app.database import engine
from app.enums import Equipment, MuscleGroup, SetType
from app.models import Exercise, Routine, RoutineExercise, RoutineSet, User


USERNAME = "marina"

# 14 ejercicios nuevos (custom de marina)
NEW_EXERCISES = [
    ("Hip Thrust con Barra", MuscleGroup.GLUTES, Equipment.BARBELL, ["hamstrings"]),
    ("Hip Thrust Unilateral con Barra", MuscleGroup.GLUTES, Equipment.BARBELL, ["hamstrings"]),
    ("Abduccion de Cadera en Maquina", MuscleGroup.GLUTES, Equipment.MACHINE, []),
    ("Abduccion de Cadera en Polea", MuscleGroup.GLUTES, Equipment.CABLE, []),
    ("Patada de Gluteo en Polea", MuscleGroup.GLUTES, Equipment.CABLE, ["hamstrings"]),
    ("Pull-through en Polea", MuscleGroup.GLUTES, Equipment.CABLE, ["hamstrings", "lower_back"]),
    ("Peso Muerto Rumano con Mancuernas", MuscleGroup.HAMSTRINGS, Equipment.DUMBBELL, ["glutes", "lower_back"]),
    ("Peso Muerto Sumo con Barra", MuscleGroup.GLUTES, Equipment.BARBELL, ["hamstrings", "quadriceps"]),
    ("Estocadas Bulgaras con Mancuernas", MuscleGroup.QUADRICEPS, Equipment.DUMBBELL, ["glutes"]),
    ("Estocadas Caminando con Mancuernas", MuscleGroup.QUADRICEPS, Equipment.DUMBBELL, ["glutes", "hamstrings"]),
    ("Press de Hombros en Maquina", MuscleGroup.SHOULDERS, Equipment.MACHINE, ["triceps"]),
    ("Crunch en Maquina", MuscleGroup.ABDOMINALS, Equipment.MACHINE, []),
    ("Face Pull en Polea", MuscleGroup.SHOULDERS, Equipment.CABLE, ["traps", "back"]),
    ("Curl Femoral Sentado en Maquina", MuscleGroup.HAMSTRINGS, Equipment.MACHINE, []),
]


# Rutinas: cada item = (titulo, [(nombre_ejercicio, sets, reps, rest_s, nota)])
ROUTINES = [
    (
        "Dia 1 - Gluteo dominante (cadera)",
        [
            ("Hip Thrust con Barra", 4, 10, 120, "2 sets de aproximacion previos"),
            ("Peso Muerto Rumano con Mancuernas", 4, 10, 90, "Foco en estiramiento"),
            ("Abduccion de Cadera en Maquina", 4, 15, 60, "Pausa de 1\" arriba"),
            ("Patada de Gluteo en Polea", 3, 12, 60, "Por pierna"),
            ("Pull-through en Polea", 3, 15, 60, "Bisagra de cadera limpia"),
            ("Plancha", 3, 45, 45, "45 segundos por serie"),
        ],
    ),
    (
        "Dia 2 - Tren superior Push",
        [
            ("Press Inclinado con Mancuernas", 4, 10, 120, None),
            ("Press de Hombros en Maquina", 4, 10, 90, None),
            ("Aperturas en Polea", 3, 12, 60, None),
            ("Elevaciones Laterales", 4, 15, 60, None),
            ("Extensiones en Polea", 3, 12, 60, None),
            ("Crunch en Maquina", 3, 15, 60, None),
        ],
    ),
    (
        "Dia 3 - Cuadriceps + gluteo secundario",
        [
            ("Sentadilla con Barra", 4, 8, 150, "Profundidad comoda"),
            ("Prensa 45", 4, 12, 120, "Pies altos = mas gluteo"),
            ("Estocadas Bulgaras con Mancuernas", 3, 10, 90, "Por pierna"),
            ("Extension de Cuadriceps", 3, 12, 60, "Pausa arriba"),
            ("Elevacion de Talones", 4, 15, 45, None),
            ("Rueda Abdominal", 3, 12, 60, None),
        ],
    ),
    (
        "Dia 4 - Tren superior Pull",
        [
            ("Dominadas", 4, 8, 120, "Asistidas si hace falta"),
            ("Remo Sentado con Cable", 4, 10, 90, None),
            ("Jalon al Pecho Agarre Neutro Cerrado", 3, 12, 60, None),
            ("Face Pull en Polea", 3, 15, 60, "Codos altos"),
            ("Curl con Barra", 3, 10, 60, None),
            ("Curl Martillo", 3, 12, 60, None),
        ],
    ),
    (
        "Dia 5 - Gluteo + femoral",
        [
            ("Hip Thrust Unilateral con Barra", 4, 10, 90, "Por lado"),
            ("Peso Muerto Sumo con Barra", 4, 8, 120, None),
            ("Curl Femoral Acostado", 4, 12, 60, "Pausa contraida arriba"),
            ("Curl Femoral Sentado en Maquina", 3, 12, 60, None),
            ("Abduccion de Cadera en Polea", 3, 15, 60, "Por lado, de pie"),
            ("Estocadas Caminando con Mancuernas", 3, 12, 90, "Por pierna"),
        ],
    ),
]


def main() -> None:
    with Session(engine) as db:
        user = db.exec(select(User).where(User.username == USERNAME)).first()
        if not user:
            raise SystemExit(f"Usuario '{USERNAME}' no encontrado")

        # 1) Crear ejercicios custom faltantes
        existing = {
            e.name: e
            for e in db.exec(
                select(Exercise).where(
                    (Exercise.owner_id == user.id) | (Exercise.owner_id.is_(None))
                )
            ).all()
        }
        created = 0
        for name, muscle, equip, secondary in NEW_EXERCISES:
            if name in existing:
                continue
            ex = Exercise(
                name=name,
                primary_muscle=muscle,
                equipment=equip,
                secondary_muscles=secondary,
                is_custom=True,
                owner_id=user.id,
            )
            db.add(ex)
            created += 1
        db.commit()
        print(f"Ejercicios nuevos creados: {created}")

        # refrescar el indice por nombre
        catalog = {
            e.name: e
            for e in db.exec(
                select(Exercise).where(
                    (Exercise.owner_id == user.id) | (Exercise.owner_id.is_(None))
                )
            ).all()
        }

        # 2) Borrar rutinas previas con los mismos titulos (idempotencia)
        wanted_titles = {title for title, _ in ROUTINES}
        old = db.exec(
            select(Routine).where(
                Routine.owner_id == user.id, Routine.title.in_(wanted_titles)
            )
        ).all()
        for r in old:
            db.delete(r)
        db.commit()

        # 3) Crear las 5 rutinas
        for title, items in ROUTINES:
            routine = Routine(title=title, owner_id=user.id)
            db.add(routine)
            db.flush()  # necesitamos routine.id
            for idx, (ex_name, sets, reps, rest, note) in enumerate(items):
                ex = catalog.get(ex_name)
                if not ex:
                    raise SystemExit(f"Ejercicio faltante en catalogo: {ex_name}")
                re = RoutineExercise(
                    routine_id=routine.id,
                    exercise_id=ex.id,
                    order_index=idx,
                    rest_seconds=rest,
                    note=note,
                )
                db.add(re)
                db.flush()
                for s in range(1, sets + 1):
                    db.add(
                        RoutineSet(
                            routine_exercise_id=re.id,
                            set_number=s,
                            set_type=SetType.NORMAL,
                            target_reps=reps,
                        )
                    )
            print(f"Creada: {title}")
        db.commit()
        print("OK")


if __name__ == "__main__":
    main()
