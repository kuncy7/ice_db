# Ice DB API – FastAPI + PostgreSQL

Backend do zarządzania organizacjami, użytkownikami i lodowiskami.

## Dev

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Swagger: `http://localhost:8000/api/docs`

## Wdrożenie

Zobacz `deploy/DEPLOY.md` i plik `deploy/ice-db-api.service`.

## Testy / Lint

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check .
```

## Skrypty curl

W `scripts/curl/` znajdują się przykłady: `login.sh`, `create_org.sh`, `create_user.sh`, `test_connection.sh`, `export_xlsx.sh`.
