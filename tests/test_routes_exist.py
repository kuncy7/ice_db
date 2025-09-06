from app.main import create_app # Zmiana tutaj

app = create_app() # Tworzymy w pełni skonfigurowaną aplikację

def test_basic_routes_exist():
    paths = {route.path for route in app.routes}

    assert "/api/auth/login" in paths
    assert "/api/system/status" in paths
    assert "/api/ice-rinks/{rink_id}/measurements" in paths
