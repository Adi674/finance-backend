from app.core.security import hash_password, verify_password, create_access_token
from app.core.db_queries import db_get_user_by_email, db_create_user
from app.core.exceptions import ConflictException, BadRequestException
from app.models.enums import Role, UserStatus
from app.modules.auth.schemas import RegisterRequest, LoginRequest


def register_user(data: RegisterRequest) -> dict:
    # Check if email already taken
    existing = db_get_user_by_email(data.email)
    if existing:
        raise ConflictException("A user with this email already exists")

    payload = {
        "name": data.name,
        "email": data.email,
        "password": hash_password(data.password),
        "role": Role.VIEWER.value,       # default role on self-registration
        "status": UserStatus.ACTIVE.value,
    }
    user = db_create_user(payload)
    return user


def login_user(data: LoginRequest) -> str:
    """Verify credentials and return a JWT access token."""
    user = db_get_user_by_email(data.email)
    if not user or not verify_password(data.password, user["password"]):
        raise BadRequestException("Invalid email or password")

    if user.get("status") == UserStatus.INACTIVE.value:
        raise BadRequestException("Account is inactive. Contact an admin.")

    token = create_access_token({"sub": user["id"], "role": user["role"]})
    return token