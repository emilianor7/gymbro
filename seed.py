from sqlmodel import Session, select
from app.database import engine, init_db
from app.models import Exercise
from app.enums import MuscleGroup, Equipment

GLOBAL_EXERCISES = [
    # Pecho
    ("Press Banca con Barra", MuscleGroup.CHEST, [MuscleGroup.TRICEPS, MuscleGroup.SHOULDERS], Equipment.BARBELL),
    ("Press Inclinado con Mancuernas", MuscleGroup.CHEST, [MuscleGroup.SHOULDERS, MuscleGroup.TRICEPS], Equipment.DUMBBELL),
    ("Aperturas en Polea", MuscleGroup.CHEST, [], Equipment.CABLE),
    ("Fondos en Paralelas", MuscleGroup.CHEST, [MuscleGroup.TRICEPS], Equipment.BODYWEIGHT),

    # Espalda
    ("Jalon al Pecho Agarre Neutro Cerrado", MuscleGroup.LATS, [MuscleGroup.BICEPS], Equipment.CABLE),
    ("Remo Sentado con Cable", MuscleGroup.BACK, [MuscleGroup.BICEPS, MuscleGroup.LATS], Equipment.CABLE),
    ("Dominadas", MuscleGroup.LATS, [MuscleGroup.BICEPS], Equipment.BODYWEIGHT),
    ("Peso Muerto Convencional", MuscleGroup.BACK, [MuscleGroup.HAMSTRINGS, MuscleGroup.GLUTES, MuscleGroup.LOWER_BACK], Equipment.BARBELL),

    # Hombros
    ("Press Militar con Barra", MuscleGroup.SHOULDERS, [MuscleGroup.TRICEPS], Equipment.BARBELL),
    ("Elevaciones Laterales", MuscleGroup.SHOULDERS, [], Equipment.DUMBBELL),
    ("Pajaros", MuscleGroup.SHOULDERS, [MuscleGroup.BACK], Equipment.DUMBBELL),

    # Biceps
    ("Curl con Barra", MuscleGroup.BICEPS, [MuscleGroup.FOREARMS], Equipment.BARBELL),
    ("Curl Martillo", MuscleGroup.BICEPS, [MuscleGroup.FOREARMS], Equipment.DUMBBELL),
    ("Curl Predicador", MuscleGroup.BICEPS, [], Equipment.EZ_BAR),

    # Triceps
    ("Press Frances", MuscleGroup.TRICEPS, [], Equipment.EZ_BAR),
    ("Extensiones en Polea", MuscleGroup.TRICEPS, [], Equipment.CABLE),

    # Pierna
    ("Sentadilla con Barra", MuscleGroup.QUADRICEPS, [MuscleGroup.GLUTES, MuscleGroup.HAMSTRINGS], Equipment.BARBELL),
    ("Prensa 45", MuscleGroup.QUADRICEPS, [MuscleGroup.GLUTES], Equipment.MACHINE),
    ("Estocadas en Smith", MuscleGroup.QUADRICEPS, [MuscleGroup.GLUTES], Equipment.SMITH),
    ("Curl Femoral Acostado", MuscleGroup.HAMSTRINGS, [], Equipment.MACHINE),
    ("Extension de Cuadriceps", MuscleGroup.QUADRICEPS, [], Equipment.MACHINE),
    ("Elevacion de Talones", MuscleGroup.CALVES, [], Equipment.MACHINE),

    # Core
    ("Plancha", MuscleGroup.ABDOMINALS, [MuscleGroup.OBLIQUES], Equipment.BODYWEIGHT),
    ("Rueda Abdominal", MuscleGroup.ABDOMINALS, [], Equipment.OTHER),
    ("Crunch en Polea", MuscleGroup.ABDOMINALS, [], Equipment.CABLE),
]


def seed():
    init_db()
    with Session(engine) as s:
        existing = s.exec(select(Exercise).where(Exercise.owner_id == None)).all()
        existing_names = {e.name.lower() for e in existing}

        added = 0
        for name, primary, secondary, equip in GLOBAL_EXERCISES:
            if name.lower() in existing_names:
                continue
            ex = Exercise(
                name=name,
                primary_muscle=primary,
                secondary_muscles=[m.value for m in secondary],
                equipment=equip,
                is_custom=False,
                owner_id=None,
            )
            s.add(ex)
            added += 1
        s.commit()
        print(f"Ejercicios agregados: {added}")
        print(f"Total en catalogo global: {len(existing) + added}")


if __name__ == "__main__":
    seed()
