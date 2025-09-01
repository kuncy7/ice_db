---

# Centralny System Zarządzania Energią dla Lodowisk - Backend

Backend API dla Centralnego Systemu Zarządzania Energią dla Lodowisk. Aplikacja została zbudowana przy użyciu FastAPI i PostgreSQL. Zapewnia RESTful API do zarządzania organizacjami, użytkownikami oraz (w przyszłości) danymi operacyjnymi z lodowisk.

## Kluczowe Funkcjonalności

*   **Zarządzanie Organizacjami:** Pełne operacje CRUD dla organizacji.
*   **Zarządzanie Użytkownikami:** Pełne operacje CRUD dla użytkowników systemu.
*   **Uwierzytelnianie JWT:** Bezpieczny system logowania oparty na tokenach JWT.
*   **Stanowe Wylogowanie:** Mechanizm wylogowania po stronie serwera z unieważnianiem tokenów.
*   **Struktura Bazy Danych:** Schemat bazy, dane inicjalizacyjne i uprawnienia zarządzane przez dedykowany skrypt SQL.
*   **Automatyczna Dokumentacja:** Interaktywna dokumentacja API dostępna dzięki Swagger UI i ReDoc.

## Stos Technologiczny

*   **Backend:** [FastAPI](https://fastapi.tiangolo.com/), Python 3.12+
*   **Baza Danych:** [PostgreSQL](https://www.postgresql.org/) 16+
*   **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/)
*   **Uwierzytelnianie:** JWT ([python-jose](https://github.com/mpdavis/python-jose)), [Passlib](https://passlib.readthedocs.io/en/stable/) (do hashowania haseł)
*   **Walidacja Danych:** [Pydantic](https://docs.pydantic.dev/)
*   **Serwer ASGI:** [Uvicorn](https://www.uvicorn.org/)

## Uruchomienie Projektu

Poniższa instrukcja zakłada pracę w środowisku Ubuntu 24.04.

### 1. Wymagania Wstępne

Upewnij się, że masz zainstalowane niezbędne pakiety:
```bash
sudo apt update
sudo apt install postgresql python3.12 python3.12-venv python3-pip
```

### 2. Konfiguracja Bazy Danych

Te kroki należy wykonać tylko raz lub w celu zresetowania bazy danych.

1.  **Stwórz użytkownika i bazę danych w PostgreSQL:**
    ```bash
    # Zaloguj się do psql
    sudo -u postgres psql

    # Wewnątrz psql wykonaj poniższe polecenia
    CREATE USER ice WITH ENCRYPTED PASSWORD 'twoje_bezpieczne_haslo';
    CREATE DATABASE lodowiska_db;
    GRANT ALL PRIVILEGES ON DATABASE lodowiska_db TO ice;
    \q
    ```

2.  **Załaduj schemat bazy i dane inicjalizacyjne:**
    Upewnij się, że plik `setup_database.sql` znajduje się w głównym folderze projektu.
    ```bash
    cat setup_database.sql | sudo -u postgres psql -d lodowiska_db
    ```

3.  **Nadaj uprawnienia do obiektów w bazie:**
    ```bash
    sudo -u postgres psql -d lodowiska_db -c "GRANT USAGE ON SCHEMA public TO ice; GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ice; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO ice; GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ice;"
    ```

### 3. Konfiguracja Aplikacji

1.  **Sklonuj repozytorium (jeśli jeszcze tego nie zrobiłeś):**
    ```bash
    git clone https://gitlab.com/venco2/lodowiska/backend.git
    cd backend
    ```

2.  **Stwórz i aktywuj wirtualne środowisko:**
    ```bash
    python3.12 -m venv venv
    source venv/bin/activate
    ```

3.  **Zainstaluj zależności:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Stwórz plik konfiguracyjny `.env`:**
    Skopiuj plik przykładowy i uzupełnij go swoimi danymi.
    ```bash
    cp .env.example .env
    nano .env
    ```
    Uzupełnij `DATABASE_URL` hasłem, które ustawiłeś w kroku 2.1, oraz wygeneruj nowy `SECRET_KEY`.

### 4. Uruchomienie Serwera

Będąc w głównym katalogu projektu z aktywnym środowiskiem wirtualnym, wykonaj:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Aplikacja będzie dostępna pod adresem `http://localhost:8000` (lub adresem IP Twojego serwera).

### 5. Wdrożenie jako Usługa Systemowa

Aplikacja jest przygotowana do uruchomienia jako stała usługa systemowa `systemd` w środowisku produkcyjnym. Taki sposób wdrożenia zapewnia automatyczny start aplikacji po restarcie serwera oraz jej automatyczne ponowne uruchomienie w przypadku awarii.

Szczegółowa, krok-po-kroku instrukcja wdrożenia znajduje się w pliku:
**[`deploy/DEPLOY.md`](deploy/DEPLOY.md)**

## Dokumentacja API

Po uruchomieniu serwera, interaktywna dokumentacja jest dostępna pod następującymi adresami:
*   **Swagger UI:** `http://localhost:8000/docs`
*   **ReDoc:** `http://localhost:8000/redoc`

Domyślny użytkownik to `admin` z hasłem `admin123`. Pamiętaj, aby zalogować się przez endpoint `/api/auth/login`, a następnie użyć przycisku `Authorize` w prawym górnym rogu, aby autoryzować zapytania w Swagger UI.

## Struktura Projektu

```
.
├── app/                  # Główny kod aplikacji
│   ├── core/             # Konfiguracja, logika bezpieczeństwa
│   ├── endpoints/        # Routers (logika poszczególnych endpointów)
│   ├── models/           # Modele SQLAlchemy i ich inicjalizacja
│   └── schemas.py        # Schematy Pydantic (walidacja danych API)
├── requirements.txt      # Zależności Python
├── setup_database.sql    # Skrypt do inicjalizacji bazy danych
└── README.md             # Ten plik
```
