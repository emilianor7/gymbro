from typing import List, Optional
from fastapi import APIRouter, status
from pydantic import BaseModel
from ... import crud
from ...exceptions import NotFoundError, PermissionDeniedError, ValidationError
from ..deps import DbDep, CurrentUser

router = APIRouter(prefix="/folders", tags=["folders"])


class FolderOut(BaseModel):
    id: int
    name: str
    order_index: int

    class Config:
        from_attributes = True


class FolderCreate(BaseModel):
    name: str


class MoveRoutineRequest(BaseModel):
    folder_id: Optional[int] = None


@router.get("", response_model=List[FolderOut])
def list_folders(db: DbDep, user: CurrentUser):
    return crud.folders.list_folders(db, user.id)


@router.post("", response_model=FolderOut, status_code=201)
def create_folder(payload: FolderCreate, db: DbDep, user: CurrentUser):
    return crud.folders.create_folder(db, user.id, payload.name)


@router.patch("/{folder_id}", response_model=FolderOut)
def rename_folder(folder_id: int, payload: FolderCreate, db: DbDep, user: CurrentUser):
    return crud.folders.rename_folder(db, folder_id, user.id, payload.name)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(folder_id: int, db: DbDep, user: CurrentUser):
    crud.folders.delete_folder(db, folder_id, user.id)


@router.patch("/routines/{routine_id}/move", status_code=200)
def move_routine(routine_id: int, payload: MoveRoutineRequest, db: DbDep, user: CurrentUser):
    crud.folders.move_routine_to_folder(db, routine_id, user.id, payload.folder_id)
    return {"ok": True}
