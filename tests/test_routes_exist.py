from app.main import app

def test_basic_routes_exist():
    # Pobierz listę wszystkich zarejestrowanych ścieżek w aplikacji
    paths = {route.path for route in app.routes}

    # Sprawdź, czy kluczowe endpointy istnieją
    assert "/api/auth/login" in paths
    assert "/api/system/status" in paths
    assert "/api/ice-rinks/{rink_id}/measurements" in paths
