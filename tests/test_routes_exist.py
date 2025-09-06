from app.main import create_app

# Tworzymy w pełni skonfigurowaną instancję aplikacji, tak jak robi to Uvicorn
app = create_app()

def test_basic_routes_exist():
    # Pobierz listę wszystkich zarejestrowanych ścieżek w aplikacji
    paths = {route.path for route in app.routes}

    # --- KROK DIAGNOSTYCZNY ---
    # Ta linia wydrukuje w logu GitLab CI/CD wszystkie ścieżki, które widzi pytest
    print("Discovered paths:", paths)
    
    # Lista kluczowych endpointów, które MUSZĄ istnieć
    expected_paths = [
        "/api/auth/login",
        "/api/system/status",
        "/api/organizations",
        "/api/users",
        "/api/ice-rinks",
        "/api/service-tickets",
        "/api/weather/providers",
        "/api/ice-rinks/{rink_id}/measurements",
        "/api/ice-rinks/{rink_id}/weather-forecasts",
    ]

    # Sprawdź, czy każdy z oczekiwanych endpointów istnieje
    for expected_path in expected_paths:
        assert expected_path in paths, f"ERROR: Expected path '{expected_path}' was not found in the application routes!"
