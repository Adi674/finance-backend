from typing import List

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from app.core.security import decode_access_token
from app.core.exceptions import CredentialsException, ForbiddenException
from app.core.db_queries import db_get_user_by_id
from app.models.enums import Role, UserStatus

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Extract Bearer token from Authorization header and return the authenticated user."""
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub")
        if not user_id:
            raise CredentialsException()
    except JWTError:
        raise CredentialsException("Invalid or expired token")

    user = db_get_user_by_id(user_id)
    if not user:
        raise CredentialsException("User no longer exists")
    if user.get("status") == UserStatus.INACTIVE:
        raise CredentialsException("Account is inactive")

    return user


def require_role(*roles: Role):
    """
    Dependency factory — restricts endpoint to specified roles.

    Usage:
        @router.get("/admin-only")
        def admin_route(user=Depends(require_role(Role.ADMIN))):
            ...
    """
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    ) -> dict:
        current_user = await get_current_user(credentials)
        if current_user.get("role") not in [r.value for r in roles]:
            raise ForbiddenException()
        return current_user

    return role_checker