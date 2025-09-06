from app.main import app

def test_basic_routes_exist():
    paths = {getattr(r, "path", ""): getattr(r, "methods", set()) for r in app.router.routes}
    assert "/api/auth/login" in paths
    assert "/api/system/status" in paths
    assert any("/api/ice-rinks/{id}/measurements" in p for p in paths.keys())
