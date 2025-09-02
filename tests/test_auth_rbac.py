import os, uuid, requests, pytest

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")

def _login(username, password):
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": username, "password": password},
        allow_redirects=True,
    )
    assert r.status_code == 200, r.text
    js = r.json()
    assert "access_token" in js and "refresh_token" in js
    return js["access_token"], js["refresh_token"]

def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

def _extract_list(resp_json, *, primary=None, fallbacks=("items", "ice_rinks", "organizations")):
    """
    Obsłuż formaty:
      - lista: [...]
      - koperta: {"data": [...]}
      - koperta: {"data": {"items": [...]}}
      - koperta: {"data": {"ice_rinks": [...]}} / {"data": {"organizations": [...]}}
    Priorytet: primary -> items -> ice_rinks -> organizations -> (gdy data listą) -> []
    """
    if isinstance(resp_json, list):
        return resp_json

    if isinstance(resp_json, dict):
        data = resp_json.get("data", resp_json)
        # 1) Spróbuj klucza primary (jeśli podany)
        if primary and isinstance(data, dict) and primary in data and isinstance(data[primary], list):
            return data[primary]
        # 2) Standard 'items'
        if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
            return data["items"]
        # 3) Fallbacki nazwowe
        if isinstance(data, dict):
            for k in fallbacks:
                if k in data and isinstance(data[k], list):
                    return data[k]
        # 4) Gdy data jest listą
        if isinstance(data, list):
            return data

    return []

def _get_any_org_id(access_token):
    r = requests.get(
        f"{BASE_URL}/api/organizations?limit=1",
        headers=_auth_headers(access_token),
        allow_redirects=True,
    )
    assert r.status_code == 200, r.text
    orgs = _extract_list(r.json(), primary="organizations")
    assert orgs, "Brak organizacji w systemie – dodaj jedną przed testem"
    return orgs[0]["id"]

def _get_any_rink_id(access_token):
    r = requests.get(
        f"{BASE_URL}/api/ice-rinks?limit=1",
        headers=_auth_headers(access_token),
        allow_redirects=True,
    )
    assert r.status_code == 200, r.text
    rinks = _extract_list(r.json(), primary="ice_rinks")
    assert rinks, "Brak lodowisk – dodaj jedno przed testem"
    return rinks[0]["id"]

def test_login_and_refresh():
    access, refresh = _login(ADMIN_USER, ADMIN_PASS)
    r = requests.get(f"{BASE_URL}/api/ice-rinks", headers=_auth_headers(access), allow_redirects=True)
    assert r.status_code == 200
    r = requests.post(f"{BASE_URL}/api/auth/refresh", headers=_auth_headers(refresh), allow_redirects=True)
    assert r.status_code == 200, r.text
    js = r.json()
    assert js.get("success") is True
    assert "access_token" in js["data"]

def test_rbac_users_list_admin_only():
    admin_access, _ = _login(ADMIN_USER, ADMIN_PASS)

    # zapewnij organization_id
    org_id = _get_any_org_id(admin_access)

    uname = f"op_{uuid.uuid4().hex[:8]}"
    payload = {
        "username": uname,
        "email": f"{uname}@example.com",
        "first_name": "Op",
        "last_name": "Erator",
        "role": "operator",
        "is_active": True,
        "password": "op123456",
        "organization_id": org_id,
    }
    r = requests.post(f"{BASE_URL}/api/users", headers=_auth_headers(admin_access), json=payload, allow_redirects=True)
    assert r.status_code in (200, 201), r.text

    op_access, _ = _login(uname, "op123456")
    r = requests.get(f"{BASE_URL}/api/users", headers=_auth_headers(op_access), allow_redirects=True)
    assert r.status_code in (403, 404)

def test_rbac_measurement_create_requires_operator_or_admin():
    admin_access, _ = _login(ADMIN_USER, ADMIN_PASS)

    rink_id = _get_any_rink_id(admin_access)

    # utwórz viewer'a (z org_id)
    org_id = _get_any_org_id(admin_access)
    uname = f"view_{uuid.uuid4().hex[:8]}"
    payload = {
        "username": uname,
        "email": f"{uname}@example.com",
        "first_name": "View",
        "last_name": "Er",
        "role": "viewer",
        "is_active": True,
        "password": "vw123456",
        "organization_id": org_id,
    }
    r = requests.post(f"{BASE_URL}/api/users", headers=_auth_headers(admin_access), json=payload, allow_redirects=True)
    assert r.status_code in (200, 201), r.text

    viewer_access, _ = _login(uname, "vw123456")

    meas = {
        "timestamp": "2025-01-01T00:00:00Z",
        "ice_temperature": -5.0,
        "chiller_power": 100.0,
        "chiller_status": "on",
        "ambient_temperature": 10.0,
        "humidity": 50.0,
        "energy_consumption": 1.2,
        "data_source": "manual",
        "quality_score": 1.0
    }
    r = requests.post(f"{BASE_URL}/api/ice-rinks/{rink_id}/measurements", headers=_auth_headers(viewer_access), json=meas, allow_redirects=True)
    assert r.status_code in (403, 404)

    r = requests.post(f"{BASE_URL}/api/ice-rinks/{rink_id}/measurements", headers=_auth_headers(admin_access), json=meas, allow_redirects=True)
    assert r.status_code in (200, 201), r.text
