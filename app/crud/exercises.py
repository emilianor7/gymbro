from typing import Optional, List
from sqlmodel import Session, select, or_, and_

from ..models import Exercise
from ..enums import MuscleGroup, Equipment
from ..exceptions import NotFoundError, PermissionDeniedError, ValidationError


def list_exercises(
    db: Session,
    user_id: int,
    *,
    muscle: Optional[MuscleGroup] = None,
    equipment: Optional[Equipment] = None,
    search: Optional[str] = None,
    only_custom: bool = False,
    limit: int = 200,
    offset: int = 0,
) -> List[Exercise]:
    """Devuelve catalogo global (owner_id IS NULL) + customs del user."""
    stmt = select(Exercise)

    if only_custom:
        stmt = stmt.where(Exercise.owner_id == user_id)
    else:
        stmt = stmt.where(or_(Exercise.owner_id == None, Exercise.owner_id == user_id))  # noqa: E711

    if muscle is not None:
        stmt = stmt.where(Exercise.primary_muscle == muscle)
    if equipment is not None:
        stmt = stmt.where(Exercise.equipment == equipment)
    if search:
        like = f"%{search.strip().lower()}%"
        stmt = stmt.where(Exercise.name.ilike(like))

    stmt = stmt.order_by(Exercise.name).limit(limit).offset(offset)
    return list(db.exec(stmt).all())


def get_exercise(db: Session, exercise_id: int, user_id: int) -> Exercise:
    """Get con validacion de visibilidad: global o propio del user."""
    ex = db.get(Exercise, exercise_id)
    if not ex:
        raise NotFoundError(f"ejercicio {exercise_id} no encontrado")
    if ex.owner_id is not None and ex.owner_id != user_id:
        raise PermissionDeniedError("ese ejercicio no pertenece al user")
    return ex


def create_custom_exercise(
    db: Session,
    owner_id: int,
    name: str,
    primary_muscle: MuscleGroup,
    *,
    secondary_muscles: Optional[List[MuscleGroup]] = None,
    equipment: Equipment = Equipment.OTHER,
    instructions: Optional[str] = None,
    image_path: Optional[str] = None,
) -> Exercise:
    name = name.strip()
    if not name:
        raise ValidationError("name es obligatorio")
    if len(name) > 128:
        raise ValidationError("name muy largo (max 128)")

    # evitar duplicados del propio user
    existing = db.exec(
        select(Exercise).where(
            and_(Exercise.owner_id == owner_id, Exercise.name == name)
        )
    ).first()
    if existing:
        raise ValidationError(f"ya existe un ejercicio custom con ese nombre: '{name}'")

    ex = Exercise(
        name=name,
        primary_muscle=primary_muscle,
        secondary_muscles=[m.value for m in (secondary_muscles or [])],
        equipment=equipment,
        is_custom=True,
        owner_id=owner_id,
        instructions=instructions,
        image_path=image_path,
    )
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ex


def update_custom_exercise(
    db: Session,
    exercise_id: int,
    owner_id: int,
    *,
    name: Optional[str] = None,
    primary_muscle: Optional[MuscleGroup] = None,
    secondary_muscles: Optional[List[MuscleGroup]] = None,
    equipment: Optional[Equipment] = None,
    instructions: Optional[str] = None,
    image_path: Optional[str] = None,
) -> Exercise:
    ex = db.get(Exercise, exercise_id)
    if not ex:
        raise NotFoundError(f"ejercicio {exercise_id} no encontrado")
    if ex.owner_id != owner_id:
        raise PermissionDeniedError("solo se pueden editar ejercicios custom propios")

    if name is not None:
        ex.name = name.strip()
    if primary_muscle is not None:
        ex.primary_muscle = primary_muscle
    if secondary_muscles is not None:
        ex.secondary_muscles = [m.value for m in secondary_muscles]
    if equipment is not None:
        ex.equipment = equipment
    if instructions is not None:
        ex.instructions = instructions
    if image_path is not None:
        ex.image_path = image_path

    db.add(ex)
    db.commit()
    db.refresh(ex)
    return ex


def delete_custom_exercise(db: Session, exercise_id: int, owner_id: int) -> None:
    ex = db.get(Exercise, exercise_id)
    if not ex:
        raise NotFoundError(f"ejercicio {exercise_id} no encontrado")
    if ex.owner_id != owner_id:
        raise PermissionDeniedError("solo se pueden borrar ejercicios custom propios")
    db.delete(ex)
    db.commit()
