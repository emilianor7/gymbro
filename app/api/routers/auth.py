from fastapi import APIRouter, HTTPException, status, Request
from ... import crud, schemas
from ..deps import DbDep, CurrentUser
from ..jwt_utils import create_access_token
from ...notifications import send_new_user_notification
import threading

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.TokenResponse, status_code=201)
def register(payload: schemas.UserCreate, request: Request, db: DbDep):
    user = crud.users.create_user(db, payload.username, payload.email, payload.password)
    token, expires_at = create_access_token(user.id)

    # notificar en background para no bloquear la respuesta
    ip = request.client.host if request.client else "desconocida"
    threading.Thread(
        target=send_new_user_notification,
        args=(user.username, user.email, ip),
        daemon=True,
    ).start()

    return schemas.TokenResponse(
        access_token=token,
        expires_at=expires_at,
        user=schemas.UserOut.model_validate(user),
    )


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.UserLogin, db: DbDep):
    user = crud.users.authenticate(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="credenciales invalidas")
    token, expires_at = create_access_token(user.id)
    return schemas.TokenResponse(
        access_token=token,
        expires_at=expires_at,
        user=schemas.UserOut.model_validate(user),
    )


@router.get("/me", response_model=schemas.UserOut)
def me(user: CurrentUser):
    return user
