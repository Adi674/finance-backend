from app.core.db_queries import db_get_all_users, db_get_user_by_id, db_update_user
from app.core.exceptions import NotFoundException, BadRequestException
from app.modules.users.schemas import UserUpdate


def get_all_users() -> list[dict]:
    users = db_get_all_users()
    for u in users:
        u.pop("password", None)
    return users


def get_user_by_id(user_id: str) -> dict:
    user = db_get_user_by_id(user_id)
    if not user:
        raise NotFoundException("User")
    user.pop("password", None)
    return user


def update_user(user_id: str, data: UserUpdate) -> dict:
    # Ensure user exists
    existing = db_get_user_by_id(user_id)
    if not existing:
        raise NotFoundException("User")

    payload = data.model_dump(exclude_none=True)
    if not payload:
        raise BadRequestException("No fields provided to update")

    updated = db_update_user(user_id, payload)
    updated.pop("password", None)
    return updated


def deactivate_user(user_id: str, current_user_id: str) -> dict:
    if user_id == current_user_id:
        raise BadRequestException("You cannot deactivate your own account")

    existing = db_get_user_by_id(user_id)
    if not existing:
        raise NotFoundException("User")

    updated = db_update_user(user_id, {"status": "inactive"})
    updated.pop("password", None)
    return updated