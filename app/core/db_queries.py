"""
All Supabase database query functions live here.
Routers and services import from this file — they never call supabase directly.
This keeps DB logic in one place and makes it easy to swap queries later.
"""

from typing import Optional
from app.config.supabase import supabase


# ── Users ─────────────────────────────────────────────────────────────────────

def db_get_user_by_email(email: str) -> Optional[dict]:
    res = supabase.table("users").select("*").eq("email", email).maybe_single().execute()
    return res.data if res else None


def db_get_user_by_id(user_id: str) -> Optional[dict]:
    res = supabase.table("users").select("*").eq("id", user_id).maybe_single().execute()
    return res.data if res else None


def db_get_all_users() -> list[dict]:
    res = supabase.table("users").select("*").order("created_at", desc=True).execute()
    return res.data or []


def db_create_user(payload: dict) -> dict:
    res = supabase.table("users").insert(payload).execute()
    return res.data[0]


def db_update_user(user_id: str, payload: dict) -> dict:
    res = (
        supabase.table("users")
        .update(payload)
        .eq("id", user_id)
        .execute()
    )
    return res.data[0]


# ── Financial Records ─────────────────────────────────────────────────────────

def db_create_record(payload: dict) -> dict:
    res = supabase.table("financial_records").insert(payload).execute()
    return res.data[0]


def db_get_record_by_id(record_id: str) -> Optional[dict]:
    res = (
        supabase.table("financial_records")
        .select("*")
        .eq("id", record_id)
        .is_("deleted_at", "null")
        .maybe_single()
        .execute()
    )
    return res.data if res else None


def db_get_records(
    record_type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
) -> list[dict]:
    query = (
        supabase.table("financial_records")
        .select("*")
        .is_("deleted_at", "null")
        .order("date", desc=True)
    )
    if record_type:
        query = query.eq("type", record_type)
    if category:
        query = query.eq("category", category)
    if start_date:
        query = query.gte("date", start_date)
    if end_date:
        query = query.lte("date", end_date)

    offset = (page - 1) * limit
    query = query.range(offset, offset + limit - 1)

    res = query.execute()
    return res.data or []


def db_update_record(record_id: str, payload: dict) -> dict:
    res = (
        supabase.table("financial_records")
        .update(payload)
        .eq("id", record_id)
        .execute()
    )
    return res.data[0]


def db_soft_delete_record(record_id: str, deleted_at: str) -> dict:
    res = (
        supabase.table("financial_records")
        .update({"deleted_at": deleted_at})
        .eq("id", record_id)
        .execute()
    )
    return res.data[0]


# ── Dashboard Aggregations ────────────────────────────────────────────────────

def db_get_summary() -> dict:
    """Returns total income, total expense, and net balance."""
    res = (
        supabase.table("financial_records")
        .select("type, amount")
        .is_("deleted_at", "null")
        .execute()
    )
    records = res.data or []
    total_income = sum(r["amount"] for r in records if r["type"] == "income")
    total_expense = sum(r["amount"] for r in records if r["type"] == "expense")
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": total_income - total_expense,
    }


def db_get_category_breakdown() -> list[dict]:
    """Returns amount grouped by category and type."""
    res = (
        supabase.table("financial_records")
        .select("category, type, amount")
        .is_("deleted_at", "null")
        .execute()
    )
    records = res.data or []

    # Group in Python since supabase-py doesn't expose GROUP BY directly
    breakdown: dict[str, dict] = {}
    for r in records:
        key = f"{r['category']}|{r['type']}"
        if key not in breakdown:
            breakdown[key] = {"category": r["category"], "type": r["type"], "total": 0}
        breakdown[key]["total"] += r["amount"]

    return list(breakdown.values())


def db_get_monthly_trends() -> list[dict]:
    """Returns income and expense totals grouped by month (last 6 months)."""
    res = (
        supabase.table("financial_records")
        .select("date, type, amount")
        .is_("deleted_at", "null")
        .execute()
    )
    records = res.data or []

    monthly: dict[str, dict] = {}
    for r in records:
        month = r["date"][:7]  # "YYYY-MM"
        if month not in monthly:
            monthly[month] = {"month": month, "income": 0, "expense": 0}
        monthly[month][r["type"]] += r["amount"]

    sorted_months = sorted(monthly.values(), key=lambda x: x["month"], reverse=True)
    return sorted_months[:6]


def db_get_recent_records(limit: int = 10) -> list[dict]:
    res = (
        supabase.table("financial_records")
        .select("*")
        .is_("deleted_at", "null")
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []