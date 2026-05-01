from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

from ..database import engine
from ..models import User
from .jwt_utils import decode_token


bearer_scheme = HTTPBearer(auto_error=True)


def get_db():
    with Session(engine) as session:
        yield session


DbDep = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbDep,
    creds: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> User:
    user_id = decode_token(creds.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user no existe",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_ai(user: CurrentUser) -> User:
    if not user.ai_enabled:
        raise HTTPException(
            status_code=403,
            detail="FEATURE_LOCKED",
        )
    return user

RequireAI = Annotated[User, Depends(require_ai)]
