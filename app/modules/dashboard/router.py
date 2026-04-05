from fastapi import APIRouter, Depends

from app.core.dependencies import require_role
from app.core.responses import success_response
from app.models.enums import Role
from app.modules.dashboard.service import (
    get_summary, get_category_breakdown, get_monthly_trends, get_recent_records
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def summary(user=Depends(require_role(Role.ANALYST, Role.ADMIN))):
    result = get_summary()
    # Explicit dict — avoids any risk of success_response arg order confusion
    return {"success": True, "message": "Dashboard summary", "data": result}


@router.get("/by-category")
def by_category(user=Depends(require_role(Role.ANALYST, Role.ADMIN))):
    result = get_category_breakdown()
    return {"success": True, "message": f"{len(result)} category groups", "data": result}


@router.get("/trends")
def trends(user=Depends(require_role(Role.ANALYST, Role.ADMIN))):
    result = get_monthly_trends()
    return {"success": True, "message": "Monthly trends (last 6 months)", "data": result}


@router.get("/recent")
def recent(user=Depends(require_role(Role.ANALYST, Role.ADMIN))):
    result = get_recent_records()
    return {"success": True, "message": "Recent 10 records", "data": result}