import os
import uuid
import requests

BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")


def _login(username, password):
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        allow_redirects=True,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    # login endpoint zwraca płaskie pola (nie w "data")
    return data["access_token"], data.get("refresh_token", "")


def _auth_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


def _extract_list(resp_json, key=None):
    """
    Akceptuje 2 formaty:
    - {"success": true, "data": {"items": [...], "page":..., "limit":..., "total":...}}
    - {"success": true, "data": {"users":[...]} }  (fallback)
    """
    data = resp_json.get("data", {})
    if key and isinstance(data, dict) and key in data:
        return data[key] or []
    if isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            return data["items"]
        # fallback na główny klucz listy (jeśli kiedyś się zmieni)
        for k, v in data.items():
            if isinstance(v, list):
                return v
    if isinstance(resp_json, list):
        return resp_json
    return []


def _get_any_org_id(access_token):
    r = requests.get(
        f"{BASE_URL}/api/organizations?limit=1",
        headers=_auth_headers(access_token),
        allow_redirects=True,
    )
    assert r.status_code == 200, r.text
    orgs = _extract_list(r.json(), key="items")
    assert orgs, "Brak organizacji w systemie – dodaj jedną przed testem"
    return orgs[0]["id"]


def _ensure_users(access_token, count=5):
    """
    Upewnia się, że mamy przynajmniej `count` użytkowników (tworzy kilku nowych).
    """
    org_id = _get_any_org_id(access_token)
    created = 0
    for _ in range(count):
        uname = f"pg_{uuid.uuid4().hex[:8]}"
        payload = {
            "username": uname,
            "email": f"{uname}@example.com",
            "first_name": "Page",
            "last_name": "Tester",
            "role": "viewer",
            "is_active": True,
            "password": "pg123456",
            "organization_id": org_id,
        }
        r = requests.post(
            f"{BASE_URL}/api/users",
            headers=_auth_headers(access_token),
            json=payload,
            allow_redirects=True,
        )
        # jeśli duplikat (skrajnie mało prawdopodobny) – pomiń
        if r.status_code in (200, 201, 409):
            created += 1
        else:
            # inne błędy nie powinny wystąpić
            assert r.status_code in (200, 201, 409), r.text
    return created


def test_users_pagination_envelope_and_limits():
    admin_access, _ = _login(ADMIN_USER, ADMIN_PASS)

    # Zapewnij materiał testowy (kilka userów, aby mieć co stronicować)
    _ensure_users(admin_access, count=5)

    # Strona 1 / limit 2
    r1 = requests.get(
        f"{BASE_URL}/api/users?page=1&limit=2",
        headers=_auth_headers(admin_access),
        allow_redirects=True,
    )
    assert r1.status_code == 200, r1.text
    j1 = r1.json()
    assert j1.get("success") is True
    d1 = j1.get("data", {})
    assert isinstance(d1, dict)
    assert set(d1.keys()) >= {"items", "page", "limit", "total"}
    assert d1["page"] == 1
    assert d1["limit"] == 2
    assert isinstance(d1["items"], list)
    assert len(d1["items"]) <= 2
    total = d1["total"]
    assert isinstance(total, int) and total >= len(d1["items"])

    # Strona 2 / limit 2
    r2 = requests.get(
        f"{BASE_URL}/api/users?page=2&limit=2",
        headers=_auth_headers(admin_access),
        allow_redirects=True,
    )
    assert r2.status_code == 200, r2.text
    j2 = r2.json()
    assert j2.get("success") is True
    d2 = j2.get("data", {})
    assert set(d2.keys()) >= {"items", "page", "limit", "total"}
    assert d2["page"] == 2
    assert d2["limit"] == 2
    assert isinstance(d2["items"], list)
    assert len(d2["items"]) <= 2
    assert d2["total"] == total  # total powinno być spójne między stronami

    # Jeżeli total > 0, to sumarycznie items na kolejnych stronach powinny pokrywać się z total (przynajmniej częściowo)
    # Sprawdzamy, że elementy ze strony 1 i 2 nie są identyczne (gdy total >= 3)
    if total >= 3 and d1["items"] and d2["items"]:
        ids1 = {u["id"] for u in d1["items"] if "id" in u}
        ids2 = {u["id"] for u in d2["items"] if "id" in u}
        # mogą się sporadycznie pokryć (np. gdy total < 3), ale zwykle powinny być różne
        assert ids1 != ids2 or total < 3

    # Limit graniczny
    r3 = requests.get(
        f"{BASE_URL}/api/users?page=1&limit=200",
        headers=_auth_headers(admin_access),
        allow_redirects=True,
    )
    assert r3.status_code == 200, r3.text
    j3 = r3.json()
    assert j3.get("success") is True
    d3 = j3.get("data", {})
    assert d3["page"] == 1
    assert d3["limit"] == 200
    assert isinstance(d3["items"], list)
    assert len(d3["items"]) <= 200
    assert isinstance(d3["total"], int) and d3["total"] >= len(d3["items"])
