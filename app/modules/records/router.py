from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from datetime import date
from uuid import UUID

from app.core.dependencies import get_current_user, require_role
from app.core.responses import success_response
from app.core.exceptions import BadRequestException
from app.models.enums import Role, RecordType
from app.modules.records.schemas import RecordCreate, RecordUpdate, RecordFilter
from app.modules.records.service import (
    create_record, list_records, get_record, update_record, delete_record
)

router = APIRouter(prefix="/api/records", tags=["Records"])

def validate_uuid(value: str, label: str = "ID") -> None:
    try:
        UUID(value, version=4)
    except ValueError:
        raise BadRequestException(f"Invalid {label} format — must be a valid UUID")


@router.post("", status_code=status.HTTP_201_CREATED)
def create(body: RecordCreate, admin=Depends(require_role(Role.ADMIN))):
    record = create_record(body, created_by=admin["id"])
    return success_response(record, "Record created successfully")


@router.get("")
def list_all(
    type: Optional[RecordType] = Query(None),
    category: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    user=Depends(get_current_user),
):
    filters = RecordFilter(
        type=type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )
    records = list_records(filters)
    return success_response(records, f"{len(records)} records found")


@router.get("/{record_id}")
def get_one(record_id: str, user=Depends(get_current_user)):
    validate_uuid(record_id, "record ID")
    record = get_record(record_id)
    return success_response(record)


@router.patch("/{record_id}")
def update(record_id: str, body: RecordUpdate, admin=Depends(require_role(Role.ADMIN))):
    validate_uuid(record_id, "record ID")
    record = update_record(record_id, body)
    return success_response(record, "Record updated successfully")


@router.delete("/{record_id}")
def delete(record_id: str, admin=Depends(require_role(Role.ADMIN))):
    validate_uuid(record_id, "record ID")
    record = delete_record(record_id)
    return success_response(record, "Record deleted successfully")