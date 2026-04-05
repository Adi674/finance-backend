"""
scripts/seed.py
───────────────
Populates Supabase with demo users and financial records.

Run from project root:
    python -m scripts.seed
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.supabase import supabase
from app.core.security import hash_password

# ── Demo Users ─────────────────────────────────────────────────────────────────
USERS = [
    {"name": "Alice Admin",   "email": "admin@finance.com",   "password": "admin123",   "role": "admin"},
    {"name": "Ana Analyst",   "email": "analyst@finance.com", "password": "analyst123", "role": "analyst"},
    {"name": "Victor Viewer", "email": "viewer@finance.com",  "password": "viewer123",  "role": "viewer"},
]

# ── Demo Records ───────────────────────────────────────────────────────────────
RECORDS = [
    {"amount": 85000, "type": "income",  "category": "Salary",      "date": "2024-01-05", "notes": "Monthly salary"},
    {"amount": 12000, "type": "expense", "category": "Rent",         "date": "2024-01-07", "notes": "Office rent"},
    {"amount": 3500,  "type": "expense", "category": "Food",         "date": "2024-01-10", "notes": "Team lunch"},
    {"amount": 5000,  "type": "income",  "category": "Freelance",    "date": "2024-01-15", "notes": "Consulting fee"},
    {"amount": 2000,  "type": "expense", "category": "Utilities",    "date": "2024-01-20", "notes": "Electricity bill"},
    {"amount": 85000, "type": "income",  "category": "Salary",       "date": "2024-02-05", "notes": "Monthly salary"},
    {"amount": 12000, "type": "expense", "category": "Rent",         "date": "2024-02-07", "notes": "Office rent"},
    {"amount": 8000,  "type": "expense", "category": "Software",     "date": "2024-02-12", "notes": "SaaS subscriptions"},
    {"amount": 15000, "type": "income",  "category": "Freelance",    "date": "2024-02-20", "notes": "Project delivery"},
    {"amount": 85000, "type": "income",  "category": "Salary",       "date": "2024-03-05", "notes": "Monthly salary"},
    {"amount": 12000, "type": "expense", "category": "Rent",         "date": "2024-03-07", "notes": "Office rent"},
    {"amount": 4500,  "type": "expense", "category": "Food",         "date": "2024-03-14", "notes": "Client dinner"},
    {"amount": 6000,  "type": "expense", "category": "Travel",       "date": "2024-03-18", "notes": "Conference trip"},
    {"amount": 20000, "type": "income",  "category": "Bonus",        "date": "2024-03-25", "notes": "Q1 performance bonus"},
]


def seed():
    print("🌱 Starting seed...")

    # Insert users
    created_users = []
    for u in USERS:
        # Check if already exists
        existing = supabase.table("users").select("id").eq("email", u["email"]).execute()
        if existing.data:
            print(f"  User {u['email']} already exists, skipping")
            created_users.append(existing.data[0])
            continue

        payload = {**u, "password": hash_password(u["password"]), "status": "active"}
        res = supabase.table("users").insert(payload).execute()
        created_users.append(res.data[0])
        print(f"  Created user: {u['email']} (role: {u['role']})")

    # Use admin user as created_by for records
    admin_user = next((u for u in created_users if "id" in u), None)
    if not admin_user:
        print(" No admin user found, skipping records")
        return

    # Insert records
    for r in RECORDS:
        payload = {**r, "created_by": admin_user["id"]}
        supabase.table("financial_records").insert(payload).execute()

    print(f"   Created {len(RECORDS)} financial records")
    print("\n Seed complete!")
    print("\n Demo credentials:")
    for u in USERS:
        print(f"   {u['role'].upper():10} → {u['email']} / {u['password']}")


if __name__ == "__main__":
    seed()