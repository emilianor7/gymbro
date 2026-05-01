from typing import Optional
from sqlmodel import Session, select

from ..models import User
from ..enums import WeightUnit
from ..exceptions import NotFoundError, ConflictError, ValidationError
from ..security import hash_password, verify_password


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    weight_unit: WeightUnit = WeightUnit.KG,
) -> User:
    username = username.strip().lower()
    email = email.strip().lower()
    if not username or not email or not password:
        raise ValidationError("username, email y password son obligatorios")
    if len(password) < 6:
        raise ValidationError("password debe tener al menos 6 caracteres")

    if db.exec(select(User).where(User.username == username)).first():
        raise ConflictError(f"username '{username}' ya existe")
    if db.exec(select(User).where(User.email == email)).first():
        raise ConflictError(f"email '{email}' ya existe")

    u = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        weight_unit=weight_unit,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def get_user(db: Session, user_id: int) -> User:
    u = db.get(User, user_id)
    if not u:
        raise NotFoundError(f"user {user_id} no encontrado")
    return u


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.exec(select(User).where(User.username == username.strip().lower())).first()


def authenticate(db: Session, username: str, password: str) -> Optional[User]:
    u = get_user_by_username(db, username)
    if not u:
        return None
    if not verify_password(password, u.password_hash):
        return None
    return u


def update_user(
    db: Session,
    user_id: int,
    *,
    email: Optional[str] = None,
    weight_unit: Optional[WeightUnit] = None,
    password: Optional[str] = None,
) -> User:
    u = get_user(db, user_id)
    if email is not None:
        email = email.strip().lower()
        if email != u.email and db.exec(select(User).where(User.email == email)).first():
            raise ConflictError(f"email '{email}' ya existe")
        u.email = email
    if weight_unit is not None:
        u.weight_unit = weight_unit
    if password is not None:
        if len(password) < 6:
            raise ValidationError("password debe tener al menos 6 caracteres")
        u.password_hash = hash_password(password)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u
