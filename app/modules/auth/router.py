from fastapi import APIRouter, Depends, status

from app.modules.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, UserPublic
from app.modules.auth.service import register_user, login_user
from app.core.dependencies import get_current_user
from app.core.responses import success_response

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    user = register_user(body)
    # Strip password before returning
    user.pop("password", None)
    return success_response(user, "Account created successfully")


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    token = login_user(body)
    return TokenResponse(access_token=token)


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    current_user.pop("password", None)
    return success_response(current_user, "Authenticated user")