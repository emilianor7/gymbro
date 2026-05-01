from typing import Optional, List
from fastapi import APIRouter, Query, status
from ... import crud, schemas
from ...enums import MuscleGroup, Equipment
from ..deps import DbDep, CurrentUser

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=List[schemas.ExerciseOut])
def list_exercises(
    db: DbDep,
    user: CurrentUser,
    muscle: Optional[MuscleGroup] = None,
    equipment: Optional[Equipment] = None,
    search: Optional[str] = None,
    only_custom: bool = False,
    limit: int = Query(default=200, le=500),
    offset: int = 0,
):
    return crud.exercises.list_exercises(
        db, user.id,
        muscle=muscle, equipment=equipment, search=search,
        only_custom=only_custom, limit=limit, offset=offset,
    )


@router.post("", response_model=schemas.ExerciseOut, status_code=201)
def create_exercise(payload: schemas.ExerciseCreate, db: DbDep, user: CurrentUser):
    return crud.exercises.create_custom_exercise(
        db, user.id, payload.name, payload.primary_muscle,
        secondary_muscles=payload.secondary_muscles,
        equipment=payload.equipment,
        instructions=payload.instructions,
        image_path=payload.image_path,
    )


@router.get("/{exercise_id}", response_model=schemas.ExerciseOut)
def get_exercise(exercise_id: int, db: DbDep, user: CurrentUser):
    return crud.exercises.get_exercise(db, exercise_id, user.id)


@router.patch("/{exercise_id}", response_model=schemas.ExerciseOut)
def update_exercise(exercise_id: int, payload: schemas.ExerciseUpdate, db: DbDep, user: CurrentUser):
    return crud.exercises.update_custom_exercise(
        db, exercise_id, user.id,
        name=payload.name,
        primary_muscle=payload.primary_muscle,
        secondary_muscles=payload.secondary_muscles,
        equipment=payload.equipment,
        instructions=payload.instructions,
        image_path=payload.image_path,
    )


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(exercise_id: int, db: DbDep, user: CurrentUser):
    crud.exercises.delete_custom_exercise(db, exercise_id, user.id)
