"""
scripts/test_api.py
────────────────────
Automated test script that covers every endpoint and access-control

Run from project root (server must be running):
    python -m scripts.test_api

"""

import sys
import requests

BASE_URL = "http://localhost:8000"

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

passed = 0
failed = 0


def ok(label):
    global passed
    passed += 1
    print(f"  {GREEN} PASS{RESET}  {label}")


def fail(label, detail=""):
    global failed
    failed += 1
    print(f"  {RED} FAIL{RESET}  {label}")
    if detail:
        print(f"         {YELLOW}{detail}{RESET}")


def section(title):
    print(f"\n{BOLD}{CYAN}{'─'*55}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*55}{RESET}")


def check(label, response, expected_status, key=None):
    """Assert status code matches; optionally return a value from response JSON."""
    if response.status_code == expected_status:
        ok(f"{label} [{response.status_code}]")
        if key:
            try:
                return response.json()["data"][key]
            except Exception:
                return None
    else:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        fail(f"{label} [expected {expected_status}, got {response.status_code}]", str(detail))
    return None


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}



def test_auth():
    section("AUTH MODULE")

    # Register a fresh test user
    res = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Test User",
        "email": "testuser_auto@finance.com",
        "password": "test1234"
    })
    # 201 = created, 409 = already exists (both are fine for this test)
    if res.status_code in (201, 409):
        ok(f"POST /api/auth/register [{res.status_code}]")
    else:
        fail(f"POST /api/auth/register [expected 201/409, got {res.status_code}]", str(res.json()))

    # Reject duplicate email
    res = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Test User",
        "email": "testuser_auto@finance.com",
        "password": "test1234"
    })
    check("POST /api/auth/register — duplicate email → 409", res, 409)

    # Reject short password
    res = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Bad",
        "email": "bad@finance.com",
        "password": "123"
    })
    check("POST /api/auth/register — short password → 422", res, 422)

    # Login with wrong password
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@finance.com",
        "password": "wrongpassword"
    })
    check("POST /api/auth/login — wrong password → 400", res, 400)

    # Login as admin
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@finance.com",
        "password": "admin123"
    })
    admin_token = None
    if res.status_code == 200:
        ok(f"POST /api/auth/login — admin [200]")
        admin_token = res.json().get("access_token")
    else:
        fail("POST /api/auth/login — admin", str(res.json()))

    # Login as analyst
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "analyst@finance.com",
        "password": "analyst123"
    })
    analyst_token = res.json().get("access_token") if res.status_code == 200 else None
    if analyst_token:
        ok("POST /api/auth/login — analyst [200]")
    else:
        fail("POST /api/auth/login — analyst")

    # Login as viewer
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "viewer@finance.com",
        "password": "viewer123"
    })
    viewer_token = res.json().get("access_token") if res.status_code == 200 else None
    if viewer_token:
        ok("POST /api/auth/login — viewer [200]")
    else:
        fail("POST /api/auth/login — viewer")

    # GET /me
    if admin_token:
        res = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_header(admin_token))
        check("GET /api/auth/me — returns current user → 200", res, 200)

    # GET /me with bad token
    res = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_header("badtoken"))
    check("GET /api/auth/me — invalid token → 401", res, 401)

    return admin_token, analyst_token, viewer_token


def test_users(admin_token, viewer_token):
    section("USERS MODULE  (Admin only)")

    # List all users
    res = requests.get(f"{BASE_URL}/api/users", headers=auth_header(admin_token))
    users = None
    if res.status_code == 200:
        ok("GET /api/users — admin → 200")
        data = res.json().get("data", [])
        users = data if isinstance(data, list) else []
    else:
        fail("GET /api/users — admin", str(res.json()))

    # Get user by ID
    user_id = None
    if users and isinstance(users[0], dict):
        user_id = users[0].get("id")
        res = requests.get(f"{BASE_URL}/api/users/{user_id}", headers=auth_header(admin_token))
        check(f"GET /api/users/{{id}} — admin → 200", res, 200)

    # Get non-existent user
    res = requests.get(f"{BASE_URL}/api/users/00000000-0000-0000-0000-000000000000",
                       headers=auth_header(admin_token))
    check("GET /api/users/{id} — not found → 404", res, 404)

    # Update user role
    if user_id:
        res = requests.patch(f"{BASE_URL}/api/users/{user_id}",
                             json={"role": "analyst"},
                             headers=auth_header(admin_token))
        check("PATCH /api/users/{id} — change role → 200", res, 200)

        # Restore original role
        requests.patch(f"{BASE_URL}/api/users/{user_id}",
                       json={"role": "viewer"},
                       headers=auth_header(admin_token))

    res = requests.get(f"{BASE_URL}/api/users", headers=auth_header(viewer_token))
    check("GET /api/users — viewer → 403 (forbidden)", res, 403)


def test_records(admin_token, analyst_token, viewer_token):
    section("RECORDS MODULE")

    created_id = None

    # Create income record
    res = requests.post(f"{BASE_URL}/api/records", json={
        "amount": 50000,
        "type": "income",
        "category": "Salary",
        "date": "2024-06-01",
        "notes": "Auto test record"
    }, headers=auth_header(admin_token))
    if res.status_code == 201:
        ok("POST /api/records — income → 201")
        data = res.json().get("data")
        created_id = data.get("id") if isinstance(data, dict) else None
    else:
        fail("POST /api/records — income", str(res.json()))

    # Create expense record
    res = requests.post(f"{BASE_URL}/api/records", json={
        "amount": 1200,
        "type": "expense",
        "category": "Utilities",
        "date": "2024-06-05"
    }, headers=auth_header(admin_token))
    check("POST /api/records — expense → 201", res, 201)

    # Reject invalid amount
    res = requests.post(f"{BASE_URL}/api/records", json={
        "amount": -500,
        "type": "income",
        "category": "Test",
        "date": "2024-06-01"
    }, headers=auth_header(admin_token))
    check("POST /api/records — negative amount → 422", res, 422)

    # List all records
    res = requests.get(f"{BASE_URL}/api/records", headers=auth_header(admin_token))
    check("GET /api/records — list all → 200", res, 200)

    # Filter by type
    res = requests.get(f"{BASE_URL}/api/records?type=income", headers=auth_header(admin_token))
    check("GET /api/records?type=income → 200", res, 200)

    # Filter by category
    res = requests.get(f"{BASE_URL}/api/records?category=Salary", headers=auth_header(admin_token))
    check("GET /api/records?category=Salary → 200", res, 200)

    # Filter by date range
    res = requests.get(f"{BASE_URL}/api/records?start_date=2024-01-01&end_date=2024-12-31",
                       headers=auth_header(admin_token))
    check("GET /api/records?start_date=...&end_date=... → 200", res, 200)

    # Pagination
    res = requests.get(f"{BASE_URL}/api/records?page=1&limit=5", headers=auth_header(admin_token))
    check("GET /api/records?page=1&limit=5 → 200", res, 200)

    # Get single record
    if created_id:
        res = requests.get(f"{BASE_URL}/api/records/{created_id}", headers=auth_header(admin_token))
        check("GET /api/records/{id} → 200", res, 200)

    # Get non-existent record
    res = requests.get(f"{BASE_URL}/api/records/00000000-0000-0000-0000-000000000000",
                       headers=auth_header(admin_token))
    check("GET /api/records/{id} — not found → 404", res, 404)

    # Update record
    if created_id:
        res = requests.patch(f"{BASE_URL}/api/records/{created_id}",
                             json={"amount": 55000, "category": "Bonus"},
                             headers=auth_header(admin_token))
        check("PATCH /api/records/{id} → 200", res, 200)

    # Viewer can read records
    res = requests.get(f"{BASE_URL}/api/records", headers=auth_header(viewer_token))
    check("GET /api/records — viewer can read → 200", res, 200)

    # ── Access control ────────────────────────────────────────────────────────
    res = requests.post(f"{BASE_URL}/api/records", json={
        "amount": 100, "type": "income", "category": "X", "date": "2024-01-01"
    }, headers=auth_header(viewer_token))
    check("POST /api/records — viewer → 403 (forbidden)", res, 403)

    res = requests.post(f"{BASE_URL}/api/records", json={
        "amount": 100, "type": "income", "category": "X", "date": "2024-01-01"
    }, headers=auth_header(analyst_token))
    check("POST /api/records — analyst → 403 (forbidden)", res, 403)

    if created_id:
        res = requests.delete(f"{BASE_URL}/api/records/{created_id}",
                              headers=auth_header(analyst_token))
        check("DELETE /api/records/{id} — analyst → 403 (forbidden)", res, 403)

    # Soft delete (admin)
    if created_id:
        res = requests.delete(f"{BASE_URL}/api/records/{created_id}",
                              headers=auth_header(admin_token))
        check("DELETE /api/records/{id} — admin → 200 (soft delete)", res, 200)

        # Confirm deleted record no longer shows in list
        res = requests.get(f"{BASE_URL}/api/records/{created_id}",
                           headers=auth_header(admin_token))
        check("GET /api/records/{id} — after soft delete → 404", res, 404)


def test_dashboard(admin_token, analyst_token, viewer_token):
    section("DASHBOARD MODULE  (Analyst + Admin only)")

    for label, token in [("admin", admin_token), ("analyst", analyst_token)]:
        res = requests.get(f"{BASE_URL}/api/dashboard/summary", headers=auth_header(token))
        check(f"GET /api/dashboard/summary — {label} → 200", res, 200)

        res = requests.get(f"{BASE_URL}/api/dashboard/by-category", headers=auth_header(token))
        check(f"GET /api/dashboard/by-category — {label} → 200", res, 200)

        res = requests.get(f"{BASE_URL}/api/dashboard/trends", headers=auth_header(token))
        check(f"GET /api/dashboard/trends — {label} → 200", res, 200)

        res = requests.get(f"{BASE_URL}/api/dashboard/recent", headers=auth_header(token))
        check(f"GET /api/dashboard/recent — {label} → 200", res, 200)

    # Viewer must be blocked from all dashboard endpoints
    for endpoint in ["summary", "by-category", "trends", "recent"]:
        res = requests.get(f"{BASE_URL}/api/dashboard/{endpoint}",
                           headers=auth_header(viewer_token))
        check(f"GET /api/dashboard/{endpoint} — viewer → 403 (forbidden)", res, 403)


def test_summary_values(admin_token):
    section("DASHBOARD SUMMARY — DATA INTEGRITY")

    res = requests.get(f"{BASE_URL}/api/dashboard/summary", headers=auth_header(admin_token))
    if res.status_code != 200:
        fail("Could not fetch summary for validation")
        return

    body = res.json()

    # success_response(data, message) → {"success":true, "message":..., "data":...}
    # Guard against swapped fields in case of serialization quirk
    data = body.get("data")
    if not isinstance(data, dict):
        data = body.get("message")   # fallback if fields are swapped

    if not isinstance(data, dict):
        fail(f"Cannot find summary dict in response. Full response: {body}")
        return

    income  = float(data.get("total_income", 0))
    expense = float(data.get("total_expense", 0))
    net     = float(data.get("net_balance", 0))

    expected_net = round(income - expense, 2)
    actual_net   = round(net, 2)

    if abs(expected_net - actual_net) < 0.01:
        ok(f"Net balance = income - expense  ({income} - {expense} = {net})")
    else:
        fail(f"Net balance mismatch: expected {expected_net}, got {actual_net}")

def main():
    print(f"\n{BOLD}{'═'*55}")
    print("  Finance API — Automated Test Suite")
    print(f"  Target: {BASE_URL}")
    print(f"{'═'*55}{RESET}")

    # Check server is up
    try:
        requests.get(f"{BASE_URL}/", timeout=3)
    except requests.exceptions.ConnectionError:
        print(f"\n{RED} Cannot reach {BASE_URL} — is the server running?{RESET}")
        print(f"   Run: {YELLOW}uvicorn app.main:app --reload{RESET}\n")
        sys.exit(1)

    admin_token, analyst_token, viewer_token = test_auth()

    if not all([admin_token, analyst_token, viewer_token]):
        print(f"\n{RED}Cannot continue — one or more logins failed.")
        print(f"Make sure you ran: python -m scripts.seed{RESET}\n")
        sys.exit(1)

    test_users(admin_token, viewer_token)
    test_records(admin_token, analyst_token, viewer_token)
    test_dashboard(admin_token, analyst_token, viewer_token)
    test_summary_values(admin_token)

    # ── Final report ──────────────────────────────────────────────────────────
    total = passed + failed
    print(f"\n{BOLD}{'═'*55}")
    print(f"  Results: {GREEN}{passed} passed{RESET}{BOLD}  |  {RED}{failed} failed{RESET}{BOLD}  |  {total} total")
    print(f"{'═'*55}{RESET}\n")

    if failed == 0:
        print(f"{GREEN}{BOLD} All tests passed! Ready to submit.{RESET}\n")
    else:
        print(f"{RED}{BOLD}  Fix the failing tests before submitting.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()