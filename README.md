# Centralny System Zarządzania Energią dla Lodowisk - Backend API

[![Wersja](https://img.shields.io/badge/wersja-1.0--refactor-blue.svg)](https://gitlab.com/venco2/lodowiska/backend)
[![Pipeline Status](https://gitlab.com/venco2/lodowiska/backend/badges/main/pipeline.svg)](https://gitlab.com/venco2/lodowiska/backend/-/pipelines)
[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

Backend API dla systemu monitorującego i optymalizującego zużycie energii na obiektach typu lodowisko.

## Opis Projektu

System został zaprojektowany w celu centralizacji danych z wielu lodowisk, agregacji pomiarów zużycia energii, danych pogodowych oraz parametrów pracy agregatów. Głównym celem jest wykorzystanie zebranych danych do trenowania modeli AI, które będą w stanie przewidywać i optymalizować zużycie energii, co przełoży się na realne oszczędności finansowe dla operatorów obiektów.

Aplikacja została zbudowana w oparciu o nowoczesne, asynchroniczne technologie i najlepsze praktyki programistyczne, zapewniając wysoką wydajność i skalowalność.

---
## Główne Funkcjonalności

* ✅ **Zarządzanie Zasobami:** Pełna obsługa CRUD dla Organizacji, Użytkowników i Lodowisk.
* ✅ **Uwierzytelnianie JWT:** Bezpieczny system logowania oparty na tokenach JWT (access + refresh) z obsługą ról.
* ✅ **Moduł Zgłoszeń Serwisowych:** Kompletny system do tworzenia, zarządzania i komentowania zgłoszeń (ticketing).
* ✅ **Moduł Prognoz Pogody:** Zarządzanie dostawcami pogody oraz API do odpytywania o prognozy.
* ✅ **Automatyczne Pobieranie Danych:** Zadanie w tle, które cyklicznie pobiera i zapisuje prognozy pogody dla wszystkich lodowisk.
* 🚧 **Integracja z SSP:** Odbieranie danych pomiarowych i alarmów z zewnętrznych systemów.
* 🔜 **Testy Automatyczne:** Pokrycie kodu testami jednostkowymi i integracyjnymi.
* 🔜 **AI i Analityka:** Trenowanie i wdrażanie modeli predykcyjnych.
* 🔜 **Raporty i Dashboardy:** Agregacja danych i prezentacja wskaźników KPI.

---
## Architektura Aplikacji

Aplikacja oparta jest o nowoczesną architekturę warstwową, która zapewnia separację odpowiedzialności, wysoką czytelność i łatwość w utrzymaniu oraz testowaniu kodu.

`Klient API ↔ Router (FastAPI) ↔ Repozytorium ↔ Model (ORM) ↔ Baza Danych`

* **Routery (`routers/`):** Odpowiedzialne za obsługę żądań HTTP, walidację danych wejściowych i formatowanie odpowiedzi.
* **Repozytoria (`repositories/`):** Warstwa abstrakcji dostępu do danych. Cała logika zapytań do bazy danych jest zamknięta tutaj.
* **Modele (`models.py`):** Definicje tabel bazy danych w postaci klas SQLAlchemy ORM.
* **Schematy (`schemas.py`):** Modele Pydantic służące do walidacji i serializacji danych.

---
## Stos Technologiczny

* **Backend:** Python 3.12+, [FastAPI](https://fastapi.tiangolo.com/)
* **Baza Danych:** PostgreSQL 14+
* **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (w pełni asynchroniczny)
* **Walidacja Danych:** [Pydantic V2](https://docs.pydantic.dev/latest/)
* **Zadania w Tle:** [fastapi-utils](https://fastapi-utils.david-montes.com/user-guide/repeated-tasks/)
* **Serwer ASGI:** [Uvicorn](https://www.uvicorn.org/) z [uvloop](https://github.com/MagicStack/uvloop)
* **Uwierzytelnianie:** JWT ([PyJWT](https://pyjwt.readthedocs.io/en/stable/)), [Passlib](https://passlib.readthedocs.io/en/stable/)

---
## Uruchomienie Lokalnego Środowiska

### 1. Wymagania Wstępne
* Python 3.12+
* Działająca instancja PostgreSQL
* Git

### 2. Konfiguracja Bazy Danych
Zaloguj się do `psql` i stwórz dedykowanego użytkownika oraz bazę danych.
```sql
CREATE USER ice WITH ENCRYPTED PASSWORD 'twoje_bezpieczne_haslo';
CREATE DATABASE ice_db OWNER ice;
```

### 3. Konfiguracja Aplikacji

1.  **Sklonuj repozytorium:**
    ```bash
    git clone [https://gitlab.com/venco2/lodowiska/backend.git](https://gitlab.com/venco2/lodowiska/backend.git)
    cd backend
    ```

2.  **Stwórz i aktywuj wirtualne środowisko:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Zainstaluj zależności:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Skonfiguruj zmienne środowiskowe:**
    Skopiuj plik `.env.example` do `.env` i uzupełnij go hasłem do bazy danych.
    ```bash
    cp .env.example .env
    nano .env
    ```
    **Zawartość pliku `.env`:**
    ```dotenv
    DATABASE_URL="postgresql+asyncpg://ice:twoje_bezpieczne_haslo@localhost:5432/ice_db"
    JWT_SECRET="zmien_mnie_na_dlugi_losowy_ciag_znakow"
    JWT_ALGORITHM="HS256"
    JWT_EXPIRES_MIN=60
    REFRESH_EXPIRES_DAYS=30
    ```

5.  **Zainicjuj bazę danych:**
    Wykonaj skrypt `setup_database.sql`, aby utworzyć wszystkie tabele, indeksy i dane startowe.
    ```bash
    psql -U ice -d ice_db -f setup_database.sql
    ```

### 4. Uruchomienie Serwera
Będąc w głównym katalogu projektu z aktywnym środowiskiem wirtualnym, wykonaj:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Flaga `--reload` zapewnia automatyczne przeładowanie serwera po każdej zmianie w kodzie.

---
## Dokumentacja i Użycie API

Po uruchomieniu serwera, interaktywna dokumentacja API (Swagger UI) jest dostępna pod adresem:
* **http://localhost:8000/api/docs**

Domyślny użytkownik to `admin` z hasłem `admin123`.

### Przykładowe zapytanie (logowanie i odczyt danych)
```bash
# Zaloguj się i zapisz token do zmiennej $TOKEN
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
-H "Content-Type: application/json" \
-d '{"username": "admin", "password": "admin123"}' \
| jq -r .data.access_token)

# Użyj tokena do pobrania danych o sobie
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me
```

## Struktura Projektu
```
.
├── app/
│   ├── db.py           # Konfiguracja połączenia z bazą danych
│   ├── deps.py         # Zależności FastAPI (autoryzacja, wstrzykiwanie repozytoriów)
│   ├── main.py         # Główny plik aplikacji FastAPI
│   ├── models.py       # Modele SQLAlchemy ORM (definicje tabel)
│   ├── repositories/   # Warstwa dostępu do danych (logika zapytań SQL)
│   ├── routers/        # Endpointy API (logika HTTP)
│   ├── schemas.py      # Schematy Pydantic (walidacja danych)
│   ├── security.py     # Funkcje związane z JWT i hashowaniem haseł
│   └── tasks.py        # Zadania działające w tle
├── setup_database.sql  # Skrypt inicjalizujący bazę danych
├── .env.example        # Przykładowy plik konfiguracyjny
├── .gitignore          # Pliki ignorowane przez Git
├── requirements.txt    # Zależności Python
└── README.md           # Ten plik
```
