from app.core.db_queries import (
    db_get_summary,
    db_get_category_breakdown,
    db_get_monthly_trends,
    db_get_recent_records,
)


def get_summary() -> dict:
    return db_get_summary()


def get_category_breakdown() -> list[dict]:
    return db_get_category_breakdown()


def get_monthly_trends() -> list[dict]:
    return db_get_monthly_trends()


def get_recent_records() -> list[dict]:
    return db_get_recent_records(limit=10)