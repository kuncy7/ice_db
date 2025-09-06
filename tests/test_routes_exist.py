from app.main import create_app

app = create_app()

def test_basic_routes_exist():
    paths = {route.path for route in app.routes}

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

    for expected_path in expected_paths:
        assert expected_path in paths, f"ERROR: Expected path '{expected_path}' was not found!"
