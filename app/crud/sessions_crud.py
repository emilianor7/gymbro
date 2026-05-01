from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from ..models import (
    WorkoutSession,
    SessionExercise,
    SessionSet,
    Routine,
    RoutineExercise,
    Exercise,
)
from ..enums import SetType
from ..exceptions import NotFoundError, PermissionDeniedError, ValidationError, ConflictError
from . import routines as routines_crud
from . import exercises as exercises_crud


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# SESSIONS
# ============================================================
def start_session(
    db: Session,
    user_id: int,
    *,
    routine_id: Optional[int] = None,
    title: Optional[str] = None,
) -> WorkoutSession:
    """
    Si routine_id se especifica, copia la estructura (exercises + sets como targets, no completados).
    Si no, crea una sesion vacia para entrenamiento libre.
    """
    if routine_id is not None:
        r = routines_crud.get_routine(db, routine_id, user_id, with_details=True)
        ws = WorkoutSession(
            user_id=user_id,
            routine_id=routine_id,
            title=title or r.title,
            started_at=_utcnow(),
        )
        db.add(ws)
        db.flush()

        for re in r.exercises:
            se = SessionExercise(
                session_id=ws.id,
                exercise_id=re.exercise_id,
                order_index=re.order_index,
                note=re.note,
            )
            db.add(se)
            db.flush()
            for rs in re.sets:
                ss = SessionSet(
                    session_exercise_id=se.id,
                    set_number=rs.set_number,
                    set_type=rs.set_type,
                    kg=rs.target_kg,
                    reps=rs.target_reps,
                    completed=False,
                )
                db.add(ss)
    else:
        ws = WorkoutSession(
            user_id=user_id,
            title=title or "Workout libre",
            started_at=_utcnow(),
        )
        db.add(ws)

    db.commit()
    db.refresh(ws)
    return ws


def get_session(db: Session, session_id: int, user_id: int, *, with_details: bool = True) -> WorkoutSession:
    stmt = select(WorkoutSession).where(WorkoutSession.id == session_id)
    if with_details:
        stmt = stmt.options(
            selectinload(WorkoutSession.exercises)
            .selectinload(SessionExercise.exercise),
            selectinload(WorkoutSession.exercises)
            .selectinload(SessionExercise.sets),
        )
    ws = db.exec(stmt).first()
    if not ws:
        raise NotFoundError(f"session {session_id} no encontrada")
    if ws.user_id != user_id:
        raise PermissionDeniedError("session no pertenece al user")
    if with_details:
        ws.exercises.sort(key=lambda se: se.order_index)
    return ws


def list_sessions(
    db: Session,
    user_id: int,
    *,
    limit: int = 50,
    offset: int = 0,
    only_finished: bool = False,
) -> List[WorkoutSession]:
    stmt = select(WorkoutSession).where(WorkoutSession.user_id == user_id)
    if only_finished:
        stmt = stmt.where(WorkoutSession.finished_at != None)  # noqa: E711
    stmt = stmt.order_by(WorkoutSession.started_at.desc()).limit(limit).offset(offset)
    return list(db.exec(stmt).all())


def finish_session(db: Session, session_id: int, user_id: int) -> WorkoutSession:
    ws = get_session(db, session_id, user_id, with_details=False)
    if ws.finished_at is not None:
        raise ConflictError("session ya esta finalizada")
    ws.finished_at = _utcnow()
    db.add(ws)
    db.commit()
    db.refresh(ws)
    return ws


def discard_session(db: Session, session_id: int, user_id: int) -> None:
    ws = get_session(db, session_id, user_id, with_details=False)
    db.delete(ws)
    db.commit()


# ============================================================
# SESSION EXERCISES (agregar al vuelo durante el workout)
# ============================================================
def add_exercise_to_session(
    db: Session,
    session_id: int,
    exercise_id: int,
    user_id: int,
    *,
    note: Optional[str] = None,
) -> SessionExercise:
    ws = get_session(db, session_id, user_id, with_details=False)
    if ws.finished_at is not None:
        raise ConflictError("session ya finalizada, no se pueden agregar ejercicios")
    exercises_crud.get_exercise(db, exercise_id, user_id)

    max_order = db.exec(
        select(SessionExercise.order_index)
        .where(SessionExercise.session_id == session_id)
        .order_by(SessionExercise.order_index.desc())
    ).first()
    next_order = (max_order + 1) if max_order is not None else 0

    se = SessionExercise(
        session_id=session_id,
        exercise_id=exercise_id,
        order_index=next_order,
        note=note,
    )
    db.add(se)
    db.commit()
    db.refresh(se)
    return se


# ============================================================
# SESSION SETS
# ============================================================
def _get_session_set(db: Session, set_id: int, user_id: int) -> SessionSet:
    ss = db.get(SessionSet, set_id)
    if not ss:
        raise NotFoundError(f"set {set_id} no encontrado")
    if ss.session_exercise.session.user_id != user_id:
        raise PermissionDeniedError("set no pertenece al user")
    return ss


def add_session_set(
    db: Session,
    session_exercise_id: int,
    user_id: int,
    *,
    kg: Optional[float] = None,
    reps: Optional[int] = None,
    set_type: SetType = SetType.NORMAL,
) -> SessionSet:
    se = db.get(SessionExercise, session_exercise_id)
    if not se:
        raise NotFoundError(f"session_exercise {session_exercise_id} no encontrado")
    if se.session.user_id != user_id:
        raise PermissionDeniedError("session_exercise no pertenece al user")
    if se.session.finished_at is not None:
        raise ConflictError("session ya finalizada")

    max_n = db.exec(
        select(SessionSet.set_number)
        .where(SessionSet.session_exercise_id == session_exercise_id)
        .order_by(SessionSet.set_number.desc())
    ).first()
    next_n = (max_n + 1) if max_n is not None else 1

    ss = SessionSet(
        session_exercise_id=session_exercise_id,
        set_number=next_n,
        set_type=set_type,
        kg=kg,
        reps=reps,
        completed=False,
    )
    db.add(ss)
    db.commit()
    db.refresh(ss)
    return ss


def log_set(
    db: Session,
    set_id: int,
    user_id: int,
    *,
    kg: Optional[float] = None,
    reps: Optional[int] = None,
    rpe: Optional[float] = None,
    effort: Optional[str] = None,
    completed: bool = True,
) -> SessionSet:
    """Registra el resultado real de un set durante el workout."""
    ss = _get_session_set(db, set_id, user_id)
    if ss.session_exercise.session.finished_at is not None:
        raise ConflictError("session ya finalizada")

    if kg is not None:
        if kg < 0:
            raise ValidationError("kg no puede ser negativo")
        ss.kg = kg
    if reps is not None:
        if reps < 0:
            raise ValidationError("reps no puede ser negativo")
        ss.reps = reps
    if rpe is not None:
        if not (0 <= rpe <= 10):
            raise ValidationError("rpe debe estar entre 0 y 10")
        ss.rpe = rpe
    if effort is not None:
        if effort not in ("hard", "normal", "easy"):
            raise ValidationError("effort debe ser hard, normal o easy")
        ss.effort = effort

    ss.completed = completed
    ss.completed_at = _utcnow() if completed else None

    db.add(ss)
    db.commit()
    db.refresh(ss)
    return ss


def delete_session_set(db: Session, set_id: int, user_id: int) -> None:
    ss = _get_session_set(db, set_id, user_id)
    if ss.session_exercise.session.finished_at is not None:
        raise ConflictError("session ya finalizada")
    se_id = ss.session_exercise_id
    removed_n = ss.set_number
    db.delete(ss)
    db.flush()
    siblings = db.exec(
        select(SessionSet)
        .where(SessionSet.session_exercise_id == se_id)
        .where(SessionSet.set_number > removed_n)
        .order_by(SessionSet.set_number)
    ).all()
    for s in siblings:
        s.set_number -= 1
        db.add(s)
    db.commit()


# ============================================================
# HISTORIAL / PROGRESO
# ============================================================
def history_for_exercise(
    db: Session,
    user_id: int,
    exercise_id: int,
    *,
    limit: int = 30,
) -> List[SessionExercise]:
    """Devuelve los SessionExercise (con sets) de las ultimas N sesiones donde aparece ese ejercicio."""
    stmt = (
        select(SessionExercise)
        .join(WorkoutSession, WorkoutSession.id == SessionExercise.session_id)
        .where(WorkoutSession.user_id == user_id)
        .where(SessionExercise.exercise_id == exercise_id)
        .where(WorkoutSession.finished_at != None)  # noqa: E711
        .options(selectinload(SessionExercise.sets))
        .order_by(WorkoutSession.started_at.desc())
        .limit(limit)
    )
    return list(db.exec(stmt).all())


def personal_record(db: Session, user_id: int, exercise_id: int) -> Optional[SessionSet]:
    """Set con mas peso completado para ese ejercicio."""
    stmt = (
        select(SessionSet)
        .join(SessionExercise, SessionExercise.id == SessionSet.session_exercise_id)
        .join(WorkoutSession, WorkoutSession.id == SessionExercise.session_id)
        .where(WorkoutSession.user_id == user_id)
        .where(SessionExercise.exercise_id == exercise_id)
        .where(SessionSet.completed == True)  # noqa: E712
        .where(SessionSet.kg != None)  # noqa: E711
        .order_by(SessionSet.kg.desc(), SessionSet.reps.desc())
        .limit(1)
    )
    return db.exec(stmt).first()


def remove_session_exercise(db: Session, se_id: int, user_id: int) -> None:
    se = db.get(SessionExercise, se_id)
    if not se:
        raise NotFoundError(f"session_exercise {se_id} no encontrado")
    if se.session.user_id != user_id:
        raise PermissionDeniedError("no pertenece al user")
    if se.session.finished_at:
        raise ConflictError("session ya finalizada")
    db.delete(se)
    db.commit()


def update_session_exercise_order(db: Session, se_id: int, user_id: int, order_index: int) -> None:
    se = db.get(SessionExercise, se_id)
    if not se:
        raise NotFoundError(f"session_exercise {se_id} no encontrado")
    if se.session.user_id != user_id:
        raise PermissionDeniedError("no pertenece al user")
    se.order_index = order_index
    db.add(se)
    db.commit()
