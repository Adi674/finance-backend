from fastapi import APIRouter, Depends, status
from uuid import UUID

from app.core.dependencies import require_role
from app.core.responses import success_response
from app.core.exceptions import BadRequestException
from app.models.enums import Role
from app.modules.users.schemas import UserUpdate
from app.modules.users.service import get_all_users, get_user_by_id, update_user, deactivate_user

router = APIRouter(prefix="/api/users", tags=["Users"])

def validate_uuid(value: str, label: str = "ID") -> None:
    try:
        UUID(value, version=4)
    except ValueError:
        raise BadRequestException(f"Invalid {label} format — must be a valid UUID")


@router.get("")
def list_users(admin=Depends(require_role(Role.ADMIN))):
    users = get_all_users()
    return success_response(users, f"{len(users)} users found")


@router.get("/{user_id}")
def get_user(user_id: str, admin=Depends(require_role(Role.ADMIN))):
    validate_uuid(user_id, "user ID")
    user = get_user_by_id(user_id)
    return success_response(user)


@router.patch("/{user_id}")
def update_user_route(user_id: str, body: UserUpdate, admin=Depends(require_role(Role.ADMIN))):
    validate_uuid(user_id, "user ID")
    updated = update_user(user_id, body)
    return success_response(updated, "User updated successfully")


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def deactivate_user_route(user_id: str, admin=Depends(require_role(Role.ADMIN))):
    validate_uuid(user_id, "user ID")
    updated = deactivate_user(user_id, admin["id"])
    return success_response(updated, "User deactivated successfully")