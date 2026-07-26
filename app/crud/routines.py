from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from ..models import Routine, RoutineExercise, RoutineSet, Exercise
from ..enums import SetType
from ..exceptions import NotFoundError, PermissionDeniedError, ValidationError
from . import exercises as exercises_crud


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# ROUTINES
# ============================================================
def list_routines(db: Session, owner_id: int) -> List[Routine]:
    stmt = (
        select(Routine)
        .where(Routine.owner_id == owner_id)
        .order_by(Routine.updated_at.desc())
    )
    return list(db.exec(stmt).all())


def get_routine(db: Session, routine_id: int, owner_id: int, *, with_details: bool = True) -> Routine:
    stmt = select(Routine).where(Routine.id == routine_id)
    if with_details:
        stmt = stmt.options(
            selectinload(Routine.exercises)
            .selectinload(RoutineExercise.exercise),
            selectinload(Routine.exercises)
            .selectinload(RoutineExercise.sets),
        )
    r = db.exec(stmt).first()
    if not r:
        raise NotFoundError(f"rutina {routine_id} no encontrada")
    if r.owner_id != owner_id:
        raise PermissionDeniedError("rutina no pertenece al user")
    return r


def create_routine(db: Session, owner_id: int, title: str, notes: Optional[str] = None) -> Routine:
    title = title.strip()
    if not title:
        raise ValidationError("title es obligatorio")
    r = Routine(title=title, notes=notes, owner_id=owner_id)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def update_routine(
    db: Session,
    routine_id: int,
    owner_id: int,
    *,
    title: Optional[str] = None,
    notes: Optional[str] = None,
) -> Routine:
    r = get_routine(db, routine_id, owner_id, with_details=False)
    if title is not None:
        title = title.strip()
        if not title:
            raise ValidationError("title no puede ser vacio")
        r.title = title
    if notes is not None:
        r.notes = notes
    r.updated_at = _utcnow()
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def delete_routine(db: Session, routine_id: int, owner_id: int) -> None:
    r = get_routine(db, routine_id, owner_id, with_details=False)
    db.delete(r)
    db.commit()


# ============================================================
# ROUTINE EXERCISES
# ============================================================
def add_exercise_to_routine(
    db: Session,
    routine_id: int,
    exercise_id: int,
    owner_id: int,
    *,
    rest_seconds: int = 0,
    note: Optional[str] = None,
) -> RoutineExercise:
    r = get_routine(db, routine_id, owner_id, with_details=False)
    # validar que el ejercicio sea visible para el user
    exercises_crud.get_exercise(db, exercise_id, owner_id)

    if rest_seconds < 0:
        raise ValidationError("rest_seconds no puede ser negativo")

    # calcular siguiente order_index
    max_order = db.exec(
        select(RoutineExercise.order_index)
        .where(RoutineExercise.routine_id == routine_id)
        .order_by(RoutineExercise.order_index.desc())
    ).first()
    next_order = (max_order + 1) if max_order is not None else 0

    re = RoutineExercise(
        routine_id=routine_id,
        exercise_id=exercise_id,
        order_index=next_order,
        rest_seconds=rest_seconds,
        note=note,
    )
    db.add(re)
    r.updated_at = _utcnow()
    db.add(r)
    db.commit()
    db.refresh(re)
    return re


def get_routine_exercise(db: Session, routine_exercise_id: int, owner_id: int) -> RoutineExercise:
    re = db.get(RoutineExercise, routine_exercise_id)
    if not re:
        raise NotFoundError(f"routine_exercise {routine_exercise_id} no encontrado")
    if re.routine.owner_id != owner_id:
        raise PermissionDeniedError("ese item no pertenece al user")
    return re


def update_routine_exercise(
    db: Session,
    routine_exercise_id: int,
    owner_id: int,
    *,
    rest_seconds: Optional[int] = None,
    note: Optional[str] = None,
) -> RoutineExercise:
    re = get_routine_exercise(db, routine_exercise_id, owner_id)
    if rest_seconds is not None:
        if rest_seconds < 0:
            raise ValidationError("rest_seconds no puede ser negativo")
        re.rest_seconds = rest_seconds
    if note is not None:
        re.note = note
    re.routine.updated_at = _utcnow()
    db.add(re)
    db.commit()
    db.refresh(re)
    return re


def remove_exercise_from_routine(db: Session, routine_exercise_id: int, owner_id: int) -> None:
    re = get_routine_exercise(db, routine_exercise_id, owner_id)
    routine = re.routine
    removed_order = re.order_index
    db.delete(re)
    db.flush()
    # compactar order_index de los que quedan despues
    siblings = db.exec(
        select(RoutineExercise)
        .where(RoutineExercise.routine_id == routine.id)
        .where(RoutineExercise.order_index > removed_order)
        .order_by(RoutineExercise.order_index)
    ).all()
    for s in siblings:
        s.order_index -= 1
        db.add(s)
        db.flush()
    routine.updated_at = _utcnow()
    db.add(routine)
    db.commit()


def reorder_routine_exercises(
    db: Session,
    routine_id: int,
    owner_id: int,
    ordered_routine_exercise_ids: List[int],
) -> Routine:
    """Reordena segun la lista de ids dada. Debe contener todos los ids actuales."""
    r = get_routine(db, routine_id, owner_id, with_details=True)
    current_ids = {re.id for re in r.exercises}
    new_ids = list(ordered_routine_exercise_ids)
    if set(new_ids) != current_ids:
        raise ValidationError("la lista de ids no coincide con los ejercicios de la rutina")

    by_id = {re.id: re for re in r.exercises}
    # estrategia 2 pasos para evitar conflicto con uq_routine_order
    for re in r.exercises:
        re.order_index += 10_000
        db.add(re)
    db.flush()
    for new_pos, re_id in enumerate(new_ids):
        re = by_id[re_id]
        re.order_index = new_pos
        db.add(re)
    r.updated_at = _utcnow()
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


# ============================================================
# ROUTINE SETS
# ============================================================
def add_set(
    db: Session,
    routine_exercise_id: int,
    owner_id: int,
    *,
    target_kg: Optional[float] = None,
    target_reps: Optional[int] = None,
    set_type: SetType = SetType.NORMAL,
) -> RoutineSet:
    re = get_routine_exercise(db, routine_exercise_id, owner_id)

    if target_kg is not None and target_kg < 0:
        raise ValidationError("target_kg no puede ser negativo")
    if target_reps is not None and target_reps < 0:
        raise ValidationError("target_reps no puede ser negativo")

    max_n = db.exec(
        select(RoutineSet.set_number)
        .where(RoutineSet.routine_exercise_id == routine_exercise_id)
        .order_by(RoutineSet.set_number.desc())
    ).first()
    next_n = (max_n + 1) if max_n is not None else 1

    rs = RoutineSet(
        routine_exercise_id=routine_exercise_id,
        set_number=next_n,
        set_type=set_type,
        target_kg=target_kg,
        target_reps=target_reps,
    )
    db.add(rs)
    re.routine.updated_at = _utcnow()
    db.add(re.routine)
    db.commit()
    db.refresh(rs)
    return rs


def update_set(
    db: Session,
    set_id: int,
    owner_id: int,
    *,
    target_kg: Optional[float] = None,
    target_reps: Optional[int] = None,
    set_type: Optional[SetType] = None,
) -> RoutineSet:
    rs = db.get(RoutineSet, set_id)
    if not rs:
        raise NotFoundError(f"set {set_id} no encontrado")
    if rs.routine_exercise.routine.owner_id != owner_id:
        raise PermissionDeniedError("set no pertenece al user")

    if target_kg is not None:
        if target_kg < 0:
            raise ValidationError("target_kg no puede ser negativo")
        rs.target_kg = target_kg
    if target_reps is not None:
        if target_reps < 0:
            raise ValidationError("target_reps no puede ser negativo")
        rs.target_reps = target_reps
    if set_type is not None:
        rs.set_type = set_type

    rs.routine_exercise.routine.updated_at = _utcnow()
    db.add(rs)
    db.commit()
    db.refresh(rs)
    return rs


def delete_set(db: Session, set_id: int, owner_id: int) -> None:
    rs = db.get(RoutineSet, set_id)
    if not rs:
        raise NotFoundError(f"set {set_id} no encontrado")
    re = rs.routine_exercise
    if re.routine.owner_id != owner_id:
        raise PermissionDeniedError("set no pertenece al user")

    removed_n = rs.set_number
    re_id = re.id
    routine = re.routine

    db.delete(rs)
    db.flush()
    # renumerar
    siblings = db.exec(
        select(RoutineSet)
        .where(RoutineSet.routine_exercise_id == re_id)
        .where(RoutineSet.set_number > removed_n)
        .order_by(RoutineSet.set_number)
    ).all()
    for s in siblings:
        s.set_number -= 1
        db.add(s)
    routine.updated_at = _utcnow()
    db.add(routine)
    db.commit()
