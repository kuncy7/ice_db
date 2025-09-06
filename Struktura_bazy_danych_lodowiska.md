# Struktura Bazy Danych - Centralny System Zarządzania Energią dla Lodowisk

**Wersja:** 1.0  
**Data:** 2025-01-27  
**Autor:** AI Assistant  
**Baza danych:** PostgreSQL  

## 1. Wprowadzenie

Niniejszy dokument opisuje szczegółową strukturę bazy danych dla Centralnego Systemu Zarządzania Energią dla Lodowisk. Baza została zaprojektowana z myślą o efektywnym przechowywaniu danych szeregów czasowych, obsłudze wielu lodowisk oraz zapewnieniu bezpieczeństwa i wydajności systemu.

## 2. Architektura Bazy Danych

### 2.1. Schematy
- **public** - główne tabele biznesowe
- **audit** - logi audytowe i bezpieczeństwa
- **timeseries** - dane szeregów czasowych (pomiary, prognozy)
- **ai_models** - modele AI i metryki

### 2.2. Typy Danych
- **UUID** - identyfikatory główne
- **TIMESTAMPTZ** - znaczniki czasowe z strefą czasową
- **JSONB** - dane konfiguracyjne i metadane
- **NUMERIC** - wartości pomiarowe z precyzją

## 3. Szczegółowa Struktura Tabel

### 3.1. Tabela: organizations (Organizacje/Klienci)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator organizacji |
| name | VARCHAR(255) | NOT NULL | - | Nazwa organizacji |
| type | VARCHAR(50) | NOT NULL | 'client' | Typ: 'client', 'partner', 'internal' |
| address | TEXT | NULL | - | Adres siedziby |
| contact_person | VARCHAR(255) | NULL | - | Osoba kontaktowa |
| contact_email | VARCHAR(255) | NULL | - | Email kontaktowy |
| contact_phone | VARCHAR(20) | NULL | - | Telefon kontaktowy |
| tax_id | VARCHAR(20) | NULL | - | NIP |
| status | VARCHAR(20) | NOT NULL | 'active' | Status: 'active', 'inactive', 'suspended' |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Data utworzenia |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | Data ostatniej aktualizacji |
| created_by | UUID | NULL | - | ID użytkownika tworzącego |
| updated_by | UUID | NULL | - | ID użytkownika aktualizującego |

**Indeksy:**
- PRIMARY KEY (id)
- UNIQUE (name)
- INDEX (status)
- INDEX (type)

### 3.2. Tabela: users (Użytkownicy)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator użytkownika |
| organization_id | UUID | NOT NULL | - | ID organizacji (FK) |
| username | VARCHAR(100) | NOT NULL | - | Nazwa użytkownika |
| email | VARCHAR(255) | NOT NULL | - | Adres email |
| password_hash | VARCHAR(255) | NOT NULL | - | Hash hasła |
| first_name | VARCHAR(100) | NOT NULL | - | Imię |
| last_name | VARCHAR(100) | NOT NULL | - | Nazwisko |
| role | VARCHAR(50) | NOT NULL | 'operator' | Rola: 'admin', 'operator', 'client' |
| status | VARCHAR(20) | NOT NULL | 'active' | Status: 'active', 'inactive', 'locked' |
| last_login | TIMESTAMPTZ | NULL | - | Ostatnie logowanie |
| failed_login_attempts | INTEGER | NOT NULL | 0 | Liczba nieudanych prób logowania |
| password_changed_at | TIMESTAMPTZ | NOT NULL | NOW() | Data zmiany hasła |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Data utworzenia |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | Data ostatniej aktualizacji |
| created_by | UUID | NULL | - | ID użytkownika tworzącego |
| updated_by | UUID | NULL | - | ID użytkownika aktualizującego |

**Indeksy:**
- PRIMARY KEY (id)
- UNIQUE (username)
- UNIQUE (email)
- FOREIGN KEY (organization_id) REFERENCES organizations(id)
- INDEX (role)
- INDEX (status)
- INDEX (organization_id)

### 3.3. Tabela: user_permissions (Uprawnienia Użytkowników)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator uprawnienia |
| user_id | UUID | NOT NULL | - | ID użytkownika (FK) |
| module | VARCHAR(100) | NOT NULL | - | Moduł systemu |
| permission | VARCHAR(50) | NOT NULL | - | Typ uprawnienia: 'read', 'write', 'admin' |
| granted_at | TIMESTAMPTZ | NOT NULL | NOW() | Data nadania uprawnienia |
| granted_by | UUID | NOT NULL | - | ID użytkownika nadającego |
| expires_at | TIMESTAMPTZ | NULL | - | Data wygaśnięcia (NULL = bezterminowo) |

**Indeksy:**
- PRIMARY KEY (id)
- FOREIGN KEY (user_id) REFERENCES users(id)
- FOREIGN KEY (granted_by) REFERENCES users(id)
- UNIQUE (user_id, module, permission)
- INDEX (module)

### 3.4. Tabela: ice_rinks (Lodowiska)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator lodowiska |
| organization_id | UUID | NOT NULL | - | ID organizacji właściciela (FK) |
| name | VARCHAR(255) | NOT NULL | - | Nazwa lodowiska |
| location | VARCHAR(500) | NOT NULL | - | Lokalizacja (adres) |
| latitude | NUMERIC(10,8) | NULL | - | Szerokość geograficzna |
| longitude | NUMERIC(11,8) | NULL | - | Długość geograficzna |
| dimensions | JSONB | NOT NULL | '{}' | Wymiary: {length, width, area} |
| type | VARCHAR(50) | NOT NULL | 'standard' | Typ: 'standard', 'olympic', 'training' |
| chiller_type | VARCHAR(100) | NOT NULL | - | Typ agregatu chłodniczego |
| max_power_consumption | NUMERIC(10,2) | NOT NULL | - | Maksymalna moc zasilania [kW] |
| ssp_endpoint | VARCHAR(500) | NULL | - | Endpoint API systemu SSP |
| ssp_api_key | VARCHAR(255) | NULL | - | Klucz API do SSP |
| ssp_status | VARCHAR(20) | NOT NULL | 'disconnected' | Status połączenia: 'connected', 'disconnected', 'error' |
| last_communication | TIMESTAMPTZ | NULL | - | Ostatnia udana komunikacja z SSP |
| status | VARCHAR(20) | NOT NULL | 'active' | Status: 'active', 'maintenance', 'inactive' |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Data utworzenia |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | Data ostatniej aktualizacji |
| created_by | UUID | NOT NULL | - | ID użytkownika tworzącego |
| updated_by | UUID | NULL | - | ID użytkownika aktualizującego |

**Indeksy:**
- PRIMARY KEY (id)
- FOREIGN KEY (organization_id) REFERENCES organizations(id)
- FOREIGN KEY (created_by) REFERENCES users(id)
- FOREIGN KEY (updated_by) REFERENCES users(id)
- INDEX (organization_id)
- INDEX (status)
- INDEX (ssp_status)
- INDEX (location)

### 3.5. Tabela: weather_providers (Dostawcy Danych Pogodowych)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator dostawcy |
| name | VARCHAR(100) | NOT NULL | - | Nazwa dostawcy (np. OpenWeatherMap) |
| api_endpoint | VARCHAR(500) | NOT NULL | - | Endpoint API |
| api_key | VARCHAR(255) | NOT NULL | - | Klucz API |
| status | VARCHAR(20) | NOT NULL | 'active' | Status: 'active', 'inactive', 'error' |
| rate_limit | INTEGER | NOT NULL | 1000 | Limit zapytań na minutę |
| last_used | TIMESTAMPTZ | NULL | - | Ostatnie użycie |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Data utworzenia |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | Data ostatniej aktualizacji |

**Indeksy:**
- PRIMARY KEY (id)
- UNIQUE (name)
- INDEX (status)

### 3.6. Tabela: weather_forecasts (Prognozy Pogodowe)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator prognozy |
| ice_rink_id | UUID | NOT NULL | - | ID lodowiska (FK) |
| weather_provider_id | UUID | NOT NULL | - | ID dostawcy pogodowego (FK) |
| forecast_time | TIMESTAMPTZ | NOT NULL | - | Czas prognozy |
| temperature_min | NUMERIC(5,2) | NOT NULL | - | Temperatura minimalna [°C] |
| temperature_max | NUMERIC(5,2) | NOT NULL | - | Temperatura maksymalna [°C] |
| humidity | NUMERIC(5,2) | NULL | - | Wilgotność względna [%] |
| solar_radiation | NUMERIC(8,2) | NULL | - | Nasłonecznienie [W/m²] |
| wind_speed | NUMERIC(5,2) | NULL | - | Prędkość wiatru [m/s] |
| precipitation_probability | NUMERIC(5,2) | NULL | - | Prawdopodobieństwo opadów [%] |
| data_quality | VARCHAR(20) | NOT NULL | 'good' | Jakość danych: 'good', 'medium', 'poor' |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Data utworzenia |

**Indeksy:**
- PRIMARY KEY (id)
- FOREIGN KEY (ice_rink_id) REFERENCES ice_rinks(id)
- FOREIGN KEY (weather_provider_id) REFERENCES weather_providers(id)
- INDEX (ice_rink_id, forecast_time)
- INDEX (forecast_time)

### 3.7. Tabela: measurements (Pomiary z Lodowisk)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator pomiaru |
| ice_rink_id | UUID | NOT NULL | - | ID lodowiska (FK) |
| timestamp | TIMESTAMPTZ | NOT NULL | - | Czas pomiaru |
| ice_temperature | NUMERIC(5,2) | NOT NULL | - | Temperatura lodu [°C] |
| chiller_power | NUMERIC(10,2) | NOT NULL | - | Pobór mocy chillera [kW] |
| chiller_status | VARCHAR(50) | NOT NULL | - | Status chillera |
| ambient_temperature | NUMERIC(5,2) | NULL | - | Temperatura otoczenia [°C] |
| humidity | NUMERIC(5,2) | NULL | - | Wilgotność otoczenia [%] |
| energy_consumption | NUMERIC(10,2) | NOT NULL | - | Zużycie energii [kWh] |
| data_source | VARCHAR(50) | NOT NULL | 'ssp' | Źródło: 'ssp', 'manual', 'calculated' |
| quality_score | NUMERIC(3,2) | NOT NULL | 1.00 | Jakość danych (0.00-1.00) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Data utworzenia |

**Indeksy:**
- PRIMARY KEY (id)
- FOREIGN KEY (ice_rink_id) REFERENCES ice_rinks(id)
- UNIQUE (ice_rink_id, timestamp)
- INDEX (ice_rink_id, timestamp)
- INDEX (timestamp)
- INDEX (data_source)

### 3.8. Tabela: ai_models (Modele AI)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator modelu |
| name | VARCHAR(255) | NOT NULL | - | Nazwa modelu |
| version | VARCHAR(50) | NOT NULL | - | Wersja modelu |
| type | VARCHAR(100) | NOT NULL | - | Typ: 'consumption_prediction', 'optimization' |
| status | VARCHAR(20) | NOT NULL | 'training' | Status: 'training', 'active', 'archived', 'error' |
| model_file_path | VARCHAR(500) | NULL | - | Ścieżka do pliku modelu |
| hyperparameters | JSONB | NOT NULL | '{}' | Hiperparametry modelu |
| training_data_range | JSONB | NOT NULL | '{}' | Zakres danych treningowych |
| performance_metrics | JSONB | NOT NULL | '{}' | Metryki wydajności |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Data utworzenia |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | Data ostatniej aktualizacji |
| created_by | UUID | NOT NULL | - | ID użytkownika tworzącego |
| deployed_at | TIMESTAMPTZ | NULL | - | Data wdrożenia |

**Indeksy:**
- PRIMARY KEY (id)
- FOREIGN KEY (created_by) REFERENCES users(id)
- UNIQUE (name, version)
- INDEX (status)
- INDEX (type)

### 3.9. Tabela: theoretical_consumption (Teoretyczne Zużycie Energii)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator |
| ice_rink_id | UUID | NOT NULL | - | ID lodowiska (FK) |
| ai_model_id | UUID | NOT NULL | - | ID modelu AI (FK) |
| timestamp | TIMESTAMPTZ | NOT NULL | - | Czas prognozy |
| theoretical_consumption | NUMERIC(10,2) | NOT NULL | - | Teoretyczne zużycie [kWh] |
| confidence_score | NUMERIC(3,2) | NOT NULL | - | Poziom pewności (0.00-1.00) |
| input_parameters | JSONB | NOT NULL | '{}' | Parametry wejściowe |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Data utworzenia |

**Indeksy:**
- PRIMARY KEY (id)
- FOREIGN KEY (ice_rink_id) REFERENCES ice_rinks(id)
- FOREIGN KEY (ai_model_id) REFERENCES ai_models(id)
- UNIQUE (ice_rink_id, timestamp)
- INDEX (ice_rink_id, timestamp)
- INDEX (ai_model_id)

### 3.10. Tabela: service_tickets (Zgłoszenia Serwisowe)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator zgłoszenia |
| ticket_number | VARCHAR(50) | NOT NULL | - | Numer zgłoszenia |
| ice_rink_id | UUID | NOT NULL | - | ID lodowiska (FK) |
| organization_id | UUID | NOT NULL | - | ID organizacji (FK) |
| created_by | UUID | NOT NULL | - | ID użytkownika tworzącego |
| assigned_to | UUID | NULL | - | ID użytkownika przypisanego |
| priority | VARCHAR(20) | NOT NULL | 'medium' | Priorytet: 'low', 'medium', 'high', 'critical' |
| status | VARCHAR(20) | NOT NULL | 'new' | Status: 'new', 'assigned', 'in_progress', 'resolved', 'closed' |
| category | VARCHAR(100) | NOT NULL | - | Kategoria problemu |
| title | VARCHAR(255) | NOT NULL | - | Tytuł zgłoszenia |
| description | TEXT | NOT NULL | - | Opis problemu |
| source | VARCHAR(20) | NOT NULL | 'manual' | Źródło: 'manual', 'automatic', 'system' |
| alarm_data | JSONB | NULL | '{}' | Dane alarmu (jeśli automatyczne) |
| sla_target | TIMESTAMPTZ | NULL | - | Cel SLA |
| resolved_at | TIMESTAMPTZ | NULL | - | Data rozwiązania |
| closed_at | TIMESTAMPTZ | NULL | - | Data zamknięcia |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Data utworzenia |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | Data ostatniej aktualizacji |

**Indeksy:**
- PRIMARY KEY (id)
- UNIQUE (ticket_number)
- FOREIGN KEY (ice_rink_id) REFERENCES ice_rinks(id)
- FOREIGN KEY (organization_id) REFERENCES organizations(id)
- FOREIGN KEY (created_by) REFERENCES users(id)
- FOREIGN KEY (assigned_to) REFERENCES users(id)
- INDEX (status)
- INDEX (priority)
- INDEX (ice_rink_id)
- INDEX (assigned_to)
- INDEX (created_at)

### 3.11. Tabela: ticket_comments (Komentarze do Zgłoszeń)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator komentarza |
| ticket_id | UUID | NOT NULL | - | ID zgłoszenia (FK) |
| user_id | UUID | NOT NULL | - | ID użytkownika (FK) |
| comment | TEXT | NOT NULL | - | Treść komentarza |
| is_internal | BOOLEAN | NOT NULL | false | Czy komentarz wewnętrzny |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Data utworzenia |

**Indeksy:**
- PRIMARY KEY (id)
- FOREIGN KEY (ticket_id) REFERENCES service_tickets(id)
- FOREIGN KEY (user_id) REFERENCES users(id)
- INDEX (ticket_id)
- INDEX (created_at)

### 3.12. Tabela: audit_logs (Logi Audytowe)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator logu |
| timestamp | TIMESTAMPTZ | NOT NULL | NOW() | Czas zdarzenia |
| user_id | UUID | NULL | - | ID użytkownika (może być NULL dla systemu) |
| action | VARCHAR(100) | NOT NULL | - | Akcja (np. 'login', 'create', 'update', 'delete') |
| module | VARCHAR(100) | NOT NULL | - | Moduł systemu |
| resource_type | VARCHAR(100) | NULL | - | Typ zasobu |
| resource_id | UUID | NULL | - | ID zasobu |
| ip_address | INET | NULL | - | Adres IP |
| user_agent | TEXT | NULL | - | User Agent przeglądarki |
| details | JSONB | NOT NULL | '{}' | Szczegóły zdarzenia |
| result | VARCHAR(20) | NOT NULL | 'success' | Rezultat: 'success', 'failure', 'error' |
| error_message | TEXT | NULL | - | Komunikat błędu (jeśli wystąpił) |

**Indeksy:**
- PRIMARY KEY (id)
- FOREIGN KEY (user_id) REFERENCES users(id)
- INDEX (timestamp)
- INDEX (user_id)
- INDEX (action)
- INDEX (module)
- INDEX (resource_type, resource_id)

### 3.13. Tabela: notifications (Powiadomienia)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator powiadomienia |
| user_id | UUID | NULL | - | ID użytkownika (NULL = systemowe) |
| organization_id | UUID | NULL | - | ID organizacji |
| type | VARCHAR(50) | NOT NULL | - | Typ: 'email', 'sms', 'webhook', 'in_app' |
| title | VARCHAR(255) | NOT NULL | - | Tytuł powiadomienia |
| message | TEXT | NOT NULL | - | Treść powiadomienia |
| status | VARCHAR(20) | NOT NULL | 'pending' | Status: 'pending', 'sent', 'failed', 'read' |
| sent_at | TIMESTAMPTZ | NULL | - | Czas wysłania |
| read_at | TIMESTAMPTZ | NULL | - | Czas przeczytania |
| retry_count | INTEGER | NOT NULL | 0 | Liczba prób wysłania |
| error_message | TEXT | NULL | - | Komunikat błędu |
| metadata | JSONB | NOT NULL | '{}' | Metadane (adres email, numer telefonu, etc.) |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | Data utworzenia |

**Indeksy:**
- PRIMARY KEY (id)
- FOREIGN KEY (user_id) REFERENCES users(id)
- FOREIGN KEY (organization_id) REFERENCES organizations(id)
- INDEX (user_id)
- INDEX (organization_id)
- INDEX (status)
- INDEX (type)
- INDEX (created_at)

### 3.14. Tabela: system_config (Konfiguracja Systemu)

| Pole | Typ | Nullable | Domyślna | Opis |
|------|-----|----------|----------|------|
| id | UUID | NOT NULL | gen_random_uuid() | Unikalny identyfikator konfiguracji |
| key | VARCHAR(255) | NOT NULL | - | Klucz konfiguracji |
| value | TEXT | NOT NULL | - | Wartość konfiguracji |
| description | TEXT | NULL | - | Opis parametru |
| category | VARCHAR(100) | NOT NULL | - | Kategoria: 'general', 'security', 'ai', 'weather' |
| is_encrypted | BOOLEAN | NOT NULL | false | Czy wartość jest zaszyfrowana |
| updated_at | TIMESTAMPTZ | NOT NULL | NOW() | Data ostatniej aktualizacji |
| updated_by | UUID | NOT NULL | - | ID użytkownika aktualizującego |

**Indeksy:**
- PRIMARY KEY (id)
- UNIQUE (key)
- INDEX (category)
- FOREIGN KEY (updated_by) REFERENCES users(id)

## 4. Relacje i Ograniczenia

### 4.1. Klucze Obce
- `users.organization_id` → `organizations.id`
- `ice_rinks.organization_id` → `organizations.id`
- `measurements.ice_rink_id` → `ice_rinks.id`
- `weather_forecasts.ice_rink_id` → `ice_rinks.id`
- `service_tickets.ice_rink_id` → `ice_rinks.id`
- `ai_models.created_by` → `users.id`

### 4.2. Ograniczenia Unikalności
- `users.username` - unikalna nazwa użytkownika
- `users.email` - unikalny adres email
- `ice_rinks.name` w ramach organizacji
- `service_tickets.ticket_number` - unikalny numer zgłoszenia

### 4.3. Ograniczenia Domenowe
- `users.role` IN ('admin', 'operator', 'client')
- `ice_rinks.status` IN ('active', 'maintenance', 'inactive')
- `service_tickets.priority` IN ('low', 'medium', 'high', 'critical')
- `measurements.quality_score` BETWEEN 0.00 AND 1.00

## 5. Indeksy Wydajnościowe

### 5.1. Indeksy dla Zapytań Częstych
- `measurements(ice_rink_id, timestamp)` - pomiary dla lodowiska w czasie
- `weather_forecasts(ice_rink_id, forecast_time)` - prognozy dla lodowiska
- `service_tickets(status, priority)` - zgłoszenia według statusu i priorytetu
- `audit_logs(timestamp, user_id)` - logi użytkownika w czasie

### 5.2. Indeksy Częściowe
- `measurements(ice_rink_id, timestamp) WHERE data_source = 'ssp'`
- `service_tickets(assigned_to, status) WHERE status IN ('new', 'assigned')`

## 6. Polityki Retencji Danych

### 6.1. Dane Operacyjne
- **Pomiary (measurements)**: 2 lata (kompresja po 6 miesiącach)
- **Prognozy pogodowe**: 1 rok
- **Logi audytowe**: 5 lat
- **Zgłoszenia serwisowe**: 10 lat

### 6.2. Dane Archiwalne
- Dane starsze niż 2 lata przenoszone do cold storage
- Automatyczne czyszczenie zgodnie z polityką retencji
- Backup pełny: codziennie, backup przyrostowy: co godzinę

## 7. Bezpieczeństwo i Szyfrowanie

### 7.1. Szyfrowanie
- Hasła użytkowników: bcrypt z saltem
- Klucze API: szyfrowane AES-256
- Dane wrażliwe: szyfrowane w spoczynku

### 7.2. Kontrola Dostępu
- RBAC (Role-Based Access Control)
- Poziomy uprawnień: odczyt, zapis, administracja
- Sesje użytkowników z timeout

### 7.3. Audyt
- Logowanie wszystkich operacji CRUD
- Śledzenie zmian konfiguracji
- Monitorowanie prób nieautoryzowanego dostępu

## 8. Optymalizacja Wydajności

### 8.1. Partycjonowanie
- Tabela `measurements` partycjonowana według miesięcy
- Tabela `audit_logs` partycjonowana według miesięcy
- Automatyczne tworzenie nowych partycji

### 8.2. Kompresja
- Dane historyczne kompresowane po 6 miesiącach
- Użycie kompresji TOAST dla dużych pól JSONB
- Optymalizacja zapytań z użyciem EXPLAIN ANALYZE

### 8.3. Cache
- Redis dla często używanych danych
- Cache metryk KPI na 5 minut
- Cache prognoz pogodowych na 15 minut

## 9. Monitorowanie i Konserwacja

### 9.1. Metryki Bazy Danych
- Rozmiar tabel i indeksów
- Liczba połączeń aktywnych
- Czas wykonywania zapytań
- Wykorzystanie przestrzeni dyskowej

### 9.2. Zadania Konserwacyjne
- Analiza statystyk: codziennie o 2:00
- Vacuum: codziennie o 3:00
- Reindex: co tydzień w niedzielę o 4:00
- Backup: codziennie o 1:00

### 9.3. Alerty
- Wykorzystanie dysku > 80%
- Czas odpowiedzi > 1s
- Liczba błędów > 100/h
- Brak połączenia z SSP > 5 minut
