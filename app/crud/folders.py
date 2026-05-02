from typing import Optional, List
from sqlmodel import Session, select
from ..models import RoutineFolder, Routine
from ..exceptions import NotFoundError, PermissionDeniedError, ValidationError


def list_folders(db: Session, owner_id: int) -> List[RoutineFolder]:
    return list(db.exec(
        select(RoutineFolder)
        .where(RoutineFolder.owner_id == owner_id)
        .order_by(RoutineFolder.order_index, RoutineFolder.name)
    ).all())


def create_folder(db: Session, owner_id: int, name: str) -> RoutineFolder:
    name = name.strip()
    if not name:
        raise ValidationError("El nombre es obligatorio")
    f = RoutineFolder(name=name, owner_id=owner_id)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def rename_folder(db: Session, folder_id: int, owner_id: int, name: str) -> RoutineFolder:
    f = db.get(RoutineFolder, folder_id)
    if not f:
        raise NotFoundError(f"Carpeta {folder_id} no encontrada")
    if f.owner_id != owner_id:
        raise PermissionDeniedError("No pertenece al user")
    f.name = name.strip()
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def delete_folder(db: Session, folder_id: int, owner_id: int) -> None:
    f = db.get(RoutineFolder, folder_id)
    if not f:
        raise NotFoundError(f"Carpeta {folder_id} no encontrada")
    if f.owner_id != owner_id:
        raise PermissionDeniedError("No pertenece al user")
    # las rutinas quedan con folder_id=NULL (SET NULL en el FK)
    db.delete(f)
    db.commit()


def move_routine_to_folder(db: Session, routine_id: int, owner_id: int, folder_id: Optional[int]) -> Routine:
    r = db.get(Routine, routine_id)
    if not r:
        raise NotFoundError(f"Rutina {routine_id} no encontrada")
    if r.owner_id != owner_id:
        raise PermissionDeniedError("No pertenece al user")
    if folder_id is not None:
        f = db.get(RoutineFolder, folder_id)
        if not f or f.owner_id != owner_id:
            raise NotFoundError("Carpeta no encontrada")
    r.folder_id = folder_id
    db.add(r)
    db.commit()
    db.refresh(r)
    return r
