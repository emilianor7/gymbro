import secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from sqlalchemy import and_
from sqlalchemy.orm import selectinload

from ...database import engine
from ...models import RoutineShareLink, Routine, RoutineExercise, RoutineSet, Exercise
from ..deps import DbDep, CurrentUser
from ... import crud

router = APIRouter(prefix="/share", tags=["share"])


class ShareLinkOut(BaseModel):
    token: str
    url: str
    uses: int


class SharedRoutinePreview(BaseModel):
    token: str
    routine_title: str
    owner_username: str
    exercises: list
    total_sets: int


# ============================================================
# GENERAR LINK
# ============================================================
@router.post("/routines/{routine_id}", response_model=ShareLinkOut)
def create_share_link(routine_id: int, db: DbDep, user: CurrentUser):
    # verificar que la rutina pertenece al user
    routine = crud.routines.get_routine(db, routine_id, user.id, with_details=False)

    # si ya existe un link para esta rutina, devolverlo
    existing = db.exec(
        select(RoutineShareLink)
        .where(RoutineShareLink.routine_id == routine_id)
        .where(RoutineShareLink.owner_id == user.id)
    ).first()

    if existing:
        return ShareLinkOut(
            token=existing.token,
            url=f"https://gymbro.lat/#/import/{existing.token}",
            uses=existing.uses,
        )

    token = secrets.token_urlsafe(8)[:12]
    link = RoutineShareLink(token=token, routine_id=routine_id, owner_id=user.id)
    db.add(link)
    db.commit()
    db.refresh(link)

    return ShareLinkOut(
        token=link.token,
        url=f"https://gymbro.lat/#/import/{link.token}",
        uses=0,
    )


@router.get("/routines/{routine_id}/link", response_model=ShareLinkOut)
def get_share_link(routine_id: int, db: DbDep, user: CurrentUser):
    link = db.exec(
        select(RoutineShareLink)
        .where(RoutineShareLink.routine_id == routine_id)
        .where(RoutineShareLink.owner_id == user.id)
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Sin link de compartir")
    return ShareLinkOut(
        token=link.token,
        url=f"https://gymbro.lat/#/import/{link.token}",
        uses=link.uses,
    )


@router.delete("/routines/{routine_id}/link", status_code=204)
def delete_share_link(routine_id: int, db: DbDep, user: CurrentUser):
    link = db.exec(
        select(RoutineShareLink)
        .where(RoutineShareLink.routine_id == routine_id)
        .where(RoutineShareLink.owner_id == user.id)
    ).first()
    if link:
        db.delete(link)
        db.commit()


# ============================================================
# VER PREVIEW (sin auth)
# ============================================================
@router.get("/preview/{token}", response_model=SharedRoutinePreview)
def preview_shared_routine(token: str, db: DbDep):
    link = db.exec(select(RoutineShareLink).where(RoutineShareLink.token == token)).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link invalido o expirado")

    stmt = (
        select(Routine)
        .where(Routine.id == link.routine_id)
        .options(
            selectinload(Routine.exercises).selectinload(RoutineExercise.exercise),
            selectinload(Routine.exercises).selectinload(RoutineExercise.sets),
            selectinload(Routine.owner),
        )
    )
    routine = db.exec(stmt).first()
    if not routine:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")

    exercises_preview = []
    total_sets = 0
    for re in routine.exercises:
        exercises_preview.append({
            "name": re.exercise.name,
            "sets": len(re.sets),
            "target_reps": re.sets[0].target_reps if re.sets else None,
        })
        total_sets += len(re.sets)

    return SharedRoutinePreview(
        token=token,
        routine_title=routine.title,
        owner_username=routine.owner.username,
        exercises=exercises_preview,
        total_sets=total_sets,
    )


# ============================================================
# IMPORTAR (requiere auth)
# ============================================================
@router.post("/import/{token}", status_code=201)
def import_shared_routine(token: str, db: DbDep, user: CurrentUser):
    link = db.exec(select(RoutineShareLink).where(RoutineShareLink.token == token)).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link invalido")

    stmt = (
        select(Routine)
        .where(Routine.id == link.routine_id)
        .options(
            selectinload(Routine.exercises).selectinload(RoutineExercise.exercise),
            selectinload(Routine.exercises).selectinload(RoutineExercise.sets),
        )
    )
    original = db.exec(stmt).first()
    if not original:
        raise HTTPException(status_code=404, detail="Rutina no encontrada")

    # crear copia para el user
    new_routine = crud.routines.create_routine(db, user.id, original.title)

    for re in original.exercises:
        ex = db.exec(
            select(Exercise).where(Exercise.id == re.exercise_id)
        ).first()
        if not ex:
            continue

        # Si es un custom de otro usuario, lo clonamos al catálogo del importador
        # (reutilizando si ya tiene uno con el mismo nombre).
        if ex.owner_id is not None and ex.owner_id != user.id:
            own = db.exec(
                select(Exercise).where(
                    and_(Exercise.owner_id == user.id, Exercise.name == ex.name)
                )
            ).first()
            if own:
                target_id = own.id
            else:
                clone = Exercise(
                    name=ex.name,
                    primary_muscle=ex.primary_muscle,
                    secondary_muscles=list(ex.secondary_muscles or []),
                    equipment=ex.equipment,
                    is_custom=True,
                    owner_id=user.id,
                    instructions=ex.instructions,
                    image_path=ex.image_path,
                )
                db.add(clone)
                db.commit()
                db.refresh(clone)
                target_id = clone.id
        else:
            target_id = ex.id

        new_re = crud.routines.add_exercise_to_routine(
            db, new_routine.id, target_id, user.id,
            rest_seconds=re.rest_seconds,
            note=re.note,
        )
        for s in re.sets:
            crud.routines.add_set(
                db, new_re.id, user.id,
                target_kg=s.target_kg,
                target_reps=s.target_reps,
                set_type=s.set_type,
            )

    # incrementar contador de usos
    link.uses += 1
    db.add(link)
    db.commit()

    return {"routine_id": new_routine.id, "title": new_routine.title}
