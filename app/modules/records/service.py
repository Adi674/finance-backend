from datetime import datetime, timezone

from app.core.db_queries import (
    db_create_record,
    db_get_record_by_id,
    db_get_records,
    db_update_record,
    db_soft_delete_record,
)
from app.core.exceptions import NotFoundException, BadRequestException
from app.modules.records.schemas import RecordCreate, RecordUpdate, RecordFilter


def create_record(data: RecordCreate, created_by: str) -> dict:
    payload = data.model_dump()
    payload["date"] = str(payload["date"])       # convert date → string for Supabase
    payload["created_by"] = created_by
    return db_create_record(payload)


def list_records(filters: RecordFilter) -> list[dict]:
    return db_get_records(
        record_type=filters.type,
        category=filters.category,
        start_date=str(filters.start_date) if filters.start_date else None,
        end_date=str(filters.end_date) if filters.end_date else None,
        page=filters.page,
        limit=filters.limit,
    )


def get_record(record_id: str) -> dict:
    record = db_get_record_by_id(record_id)
    if not record:
        raise NotFoundException("Record")
    return record


def update_record(record_id: str, data: RecordUpdate) -> dict:
    existing = db_get_record_by_id(record_id)
    if not existing:
        raise NotFoundException("Record")

    payload = data.model_dump(exclude_none=True)
    if not payload:
        raise BadRequestException("No fields provided to update")

    if "date" in payload:
        payload["date"] = str(payload["date"])

    return db_update_record(record_id, payload)


def delete_record(record_id: str) -> dict:
    existing = db_get_record_by_id(record_id)
    if not existing:
        raise NotFoundException("Record")

    deleted_at = datetime.now(timezone.utc).isoformat()
    return db_soft_delete_record(record_id, deleted_at)