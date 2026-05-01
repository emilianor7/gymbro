from typing import List
from fastapi import APIRouter, status
from ... import crud, schemas
from ..deps import DbDep, CurrentUser

router = APIRouter(prefix="/routines", tags=["routines"])


# ============================================================
# ROUTINES
# ============================================================
@router.get("", response_model=List[schemas.RoutineOut])
def list_routines(db: DbDep, user: CurrentUser):
    return crud.routines.list_routines(db, user.id)


@router.post("", response_model=schemas.RoutineOut, status_code=201)
def create_routine(payload: schemas.RoutineCreate, db: DbDep, user: CurrentUser):
    return crud.routines.create_routine(db, user.id, payload.title, payload.notes)


@router.get("/{routine_id}", response_model=schemas.RoutineDetail)
def get_routine(routine_id: int, db: DbDep, user: CurrentUser):
    return crud.routines.get_routine(db, routine_id, user.id, with_details=True)


@router.patch("/{routine_id}", response_model=schemas.RoutineOut)
def update_routine(routine_id: int, payload: schemas.RoutineUpdate, db: DbDep, user: CurrentUser):
    return crud.routines.update_routine(db, routine_id, user.id, title=payload.title, notes=payload.notes)


@router.delete("/{routine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routine(routine_id: int, db: DbDep, user: CurrentUser):
    crud.routines.delete_routine(db, routine_id, user.id)


# ============================================================
# ROUTINE EXERCISES
# ============================================================
@router.post("/{routine_id}/exercises", response_model=schemas.RoutineExerciseOut, status_code=201)
def add_exercise(routine_id: int, payload: schemas.RoutineExerciseAdd, db: DbDep, user: CurrentUser):
    re = crud.routines.add_exercise_to_routine(
        db, routine_id, payload.exercise_id, user.id,
        rest_seconds=payload.rest_seconds, note=payload.note,
    )
    db.refresh(re)
    return re


@router.patch("/exercises/{re_id}", response_model=schemas.RoutineExerciseOut)
def update_routine_exercise(re_id: int, payload: schemas.RoutineExerciseUpdate, db: DbDep, user: CurrentUser):
    return crud.routines.update_routine_exercise(
        db, re_id, user.id, rest_seconds=payload.rest_seconds, note=payload.note,
    )


@router.delete("/exercises/{re_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_routine_exercise(re_id: int, db: DbDep, user: CurrentUser):
    crud.routines.remove_exercise_from_routine(db, re_id, user.id)


@router.post("/{routine_id}/reorder", response_model=schemas.RoutineDetail)
def reorder(routine_id: int, payload: schemas.ReorderRequest, db: DbDep, user: CurrentUser):
    return crud.routines.reorder_routine_exercises(db, routine_id, user.id, payload.ordered_ids)


# ============================================================
# ROUTINE SETS
# ============================================================
@router.post("/exercises/{re_id}/sets", response_model=schemas.RoutineSetOut, status_code=201)
def add_set(re_id: int, payload: schemas.RoutineSetCreate, db: DbDep, user: CurrentUser):
    return crud.routines.add_set(
        db, re_id, user.id,
        target_kg=payload.target_kg, target_reps=payload.target_reps, set_type=payload.set_type,
    )


@router.patch("/sets/{set_id}", response_model=schemas.RoutineSetOut)
def update_set(set_id: int, payload: schemas.RoutineSetUpdate, db: DbDep, user: CurrentUser):
    return crud.routines.update_set(
        db, set_id, user.id,
        target_kg=payload.target_kg, target_reps=payload.target_reps, set_type=payload.set_type,
    )


@router.delete("/sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_set(set_id: int, db: DbDep, user: CurrentUser):
    crud.routines.delete_set(db, set_id, user.id)
