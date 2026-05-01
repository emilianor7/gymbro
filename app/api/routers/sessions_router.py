from typing import List, Optional
from fastapi import APIRouter, Query, status
from ... import crud, schemas
from ..deps import DbDep, CurrentUser

router = APIRouter(prefix="/sessions", tags=["sessions"])


# ============================================================
# SESSIONS
# ============================================================
@router.get("", response_model=List[schemas.SessionOut])
def list_sessions(
    db: DbDep, user: CurrentUser,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    only_finished: bool = False,
):
    return crud.sessions.list_sessions(db, user.id, limit=limit, offset=offset, only_finished=only_finished)


@router.post("", response_model=schemas.SessionDetail, status_code=201)
def start_session(payload: schemas.SessionStart, db: DbDep, user: CurrentUser):
    ws = crud.sessions.start_session(db, user.id, routine_id=payload.routine_id, title=payload.title)
    return crud.sessions.get_session(db, ws.id, user.id)


@router.get("/{session_id}", response_model=schemas.SessionDetail)
def get_session(session_id: int, db: DbDep, user: CurrentUser):
    return crud.sessions.get_session(db, session_id, user.id)


@router.post("/{session_id}/finish", response_model=schemas.SessionOut)
def finish_session(session_id: int, db: DbDep, user: CurrentUser):
    return crud.sessions.finish_session(db, session_id, user.id)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def discard_session(session_id: int, db: DbDep, user: CurrentUser):
    crud.sessions.discard_session(db, session_id, user.id)


# ============================================================
# SESSION EXERCISES
# ============================================================
@router.post("/{session_id}/exercises", response_model=schemas.SessionExerciseOut, status_code=201)
def add_exercise_to_session(session_id: int, payload: schemas.SessionExerciseAdd, db: DbDep, user: CurrentUser):
    return crud.sessions.add_exercise_to_session(
        db, session_id, payload.exercise_id, user.id, note=payload.note,
    )


@router.delete("/exercises/{se_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_session_exercise(se_id: int, db: DbDep, user: CurrentUser):
    crud.sessions.remove_session_exercise(db, se_id, user.id)


@router.patch("/exercises/{se_id}", status_code=200)
def update_session_exercise(se_id: int, payload: dict, db: DbDep, user: CurrentUser):
    crud.sessions.update_session_exercise_order(db, se_id, user.id, payload.get("order_index", 0))
    return {"ok": True}


# ============================================================
# SESSION SETS
# ============================================================
@router.post("/exercises/{se_id}/sets", response_model=schemas.SessionSetOut, status_code=201)
def add_session_set(se_id: int, payload: schemas.SessionSetCreate, db: DbDep, user: CurrentUser):
    return crud.sessions.add_session_set(
        db, se_id, user.id,
        kg=payload.kg, reps=payload.reps, set_type=payload.set_type,
    )


@router.patch("/sets/{set_id}", response_model=schemas.SessionSetOut)
def log_set(set_id: int, payload: schemas.SessionSetLog, db: DbDep, user: CurrentUser):
    return crud.sessions.log_set(
        db, set_id, user.id,
        kg=payload.kg, reps=payload.reps, rpe=payload.rpe,
        effort=payload.effort, completed=payload.completed,
    )


@router.delete("/sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session_set(set_id: int, db: DbDep, user: CurrentUser):
    crud.sessions.delete_session_set(db, set_id, user.id)


# ============================================================
# HISTORIAL / PROGRESO
# ============================================================
@router.get("/history/{exercise_id}", response_model=List[schemas.SessionExerciseOut])
def history_for_exercise(exercise_id: int, db: DbDep, user: CurrentUser, limit: int = Query(default=30, le=100)):
    return crud.sessions.history_for_exercise(db, user.id, exercise_id, limit=limit)


@router.get("/pr/{exercise_id}", response_model=Optional[schemas.SessionSetOut])
def personal_record(exercise_id: int, db: DbDep, user: CurrentUser):
    return crud.sessions.personal_record(db, user.id, exercise_id)
