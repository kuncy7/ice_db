# Endpointy API - Centralny System Zarządzania Energią dla Lodowisk

**Wersja:** 1.0  
**Data:** 2025-01-27  
**Autor:** AI Assistant  
**Format:** REST API z autoryzacją JWT  

## 1. Wprowadzenie

Niniejszy dokument opisuje kompletny zestaw endpointów API dla Centralnego Systemu Zarządzania Energią dla Lodowisk. API zostało zaprojektowane zgodnie z zasadami REST i zapewnia bezpieczną komunikację z systemami SSP oraz interfejsami użytkownika.

## 2. Autoryzacja i Bezpieczeństwo

### 2.1. Uwierzytelnianie
- **Typ:** JWT (JSON Web Token)
- **Header:** `Authorization: Bearer <token>`
- **Czas życia tokenu:** 1 godzina (konfigurowalny)
- **Refresh token:** 30 dni

### 2.2. Role i Uprawnienia
- **admin:** Pełny dostęp do wszystkich endpointów
- **operator:** Dostęp do monitoringu, zgłoszeń, podstawowej konfiguracji
- **client:** Dostęp tylko do własnych lodowisk i zgłoszeń

### 2.3. Rate Limiting
- **Standardowe:** 1000 requestów/godzinę
- **API SSP:** 100 requestów/minutę
- **Pogodowe:** 60 requestów/minutę

## 3. Endpointy Autoryzacji

### 3.1. Logowanie
```
POST /api/auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}

Response:
{
  "success": true,
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "user": {
      "id": "uuid",
      "username": "string",
      "role": "string",
      "organization_id": "uuid"
    }
  }
}
```

### 3.2. Odświeżanie Tokenu
```
POST /api/auth/refresh
Authorization: Bearer <refresh_token>

Response:
{
  "success": true,
  "data": {
    "access_token": "string"
  }
}
```

### 3.3. Wylogowanie
```
POST /api/auth/logout
Authorization: Bearer <access_token>

Response:
{
  "success": true,
  "message": "Wylogowano pomyślnie"
}
```

## 4. Endpointy Organizacji

### 4.1. Lista Organizacji
```
GET /api/organizations
Authorization: Bearer <token>
Query params: page, limit, status, type

Response:
{
  "success": true,
  "data": {
    "organizations": [...],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

### 4.2. Szczegóły Organizacji
```
GET /api/organizations/{id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "string",
    "type": "string",
    "address": "string",
    "contact_person": "string",
    "contact_email": "string",
    "contact_phone": "string",
    "tax_id": "string",
    "status": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

### 4.3. Tworzenie Organizacji
```
POST /api/organizations
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "string",
  "type": "string",
  "address": "string",
  "contact_person": "string",
  "contact_email": "string",
  "contact_phone": "string",
  "tax_id": "string"
}
```

## 5. Endpointy Użytkowników

### 5.1. Lista Użytkowników
```
GET /api/users
Authorization: Bearer <token>
Query params: page, limit, role, status, organization_id

Response:
{
  "success": true,
  "data": {
    "users": [...],
    "pagination": {...}
  }
}
```

### 5.2. Tworzenie Użytkownika
```
POST /api/users
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "string",
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "string",
  "organization_id": "uuid"
}
```

### 5.3. Aktualizacja Użytkownika
```
PUT /api/users/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "string",
  "last_name": "string",
  "role": "string",
  "status": "string"
}
```

### 5.4. Zmiana Hasła
```
PUT /api/users/{id}/password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "string",
  "new_password": "string"
}
```

## 6. Endpointy Lodowisk

### 6.1. Lista Lodowisk
```
GET /api/ice-rinks
Authorization: Bearer <token>
Query params: page, limit, organization_id, status, ssp_status, location

Response:
{
  "success": true,
  "data": {
    "ice_rinks": [...],
    "pagination": {...}
  }
}
```

### 6.2. Szczegóły Lodowiska
```
GET /api/ice-rinks/{id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "string",
    "location": "string",
    "latitude": "decimal",
    "longitude": "decimal",
    "dimensions": "json",
    "type": "string",
    "chiller_type": "string",
    "max_power_consumption": "decimal",
    "ssp_status": "string",
    "last_communication": "datetime",
    "status": "string",
    "measurements": [...],
    "weather_forecasts": [...]
  }
}
```

### 6.3. Tworzenie Lodowiska
```
POST /api/ice-rinks
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "string",
  "location": "string",
  "latitude": "decimal",
  "longitude": "decimal",
  "dimensions": "json",
  "type": "string",
  "chiller_type": "string",
  "max_power_consumption": "decimal",
  "ssp_endpoint": "string",
  "ssp_api_key": "string"
}
```

### 6.4. Test Połączenia SSP
```
POST /api/ice-rinks/{id}/test-connection
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "status": "string",
    "response_time": "decimal",
    "last_communication": "datetime",
    "error_message": "string"
  }
}
```

## 7. Endpointy Pomiary i Dane

### 7.1. Pomiary z Lodowiska
```
GET /api/ice-rinks/{id}/measurements
Authorization: Bearer <token>
Query params: start_date, end_date, data_source, limit

Response:
{
  "success": true,
  "data": {
    "measurements": [
      {
        "id": "uuid",
        "timestamp": "datetime",
        "ice_temperature": "decimal",
        "chiller_power": "decimal",
        "chiller_status": "string",
        "ambient_temperature": "decimal",
        "humidity": "decimal",
        "energy_consumption": "decimal",
        "data_source": "string",
        "quality_score": "decimal"
      }
    ]
  }
}
```

### 7.2. Ostatnie Pomiary
```
GET /api/ice-rinks/{id}/measurements/latest
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "measurement": {...}
  }
}
```

### 7.3. Eksport Pomiary
```
GET /api/ice-rinks/{id}/measurements/export
Authorization: Bearer <token>
Query params: start_date, end_date, format (csv, json, xlsx)

Response: File download
```

## 8. Endpointy Prognoz Pogodowych

### 8.1. Lista Dostawców Pogodowych
```
GET /api/weather/providers
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "providers": [
      {
        "id": "uuid",
        "name": "string",
        "status": "string",
        "rate_limit": "integer",
        "last_used": "datetime"
      }
    ]
  }
}
```

### 8.2. Konfiguracja Dostawcy
```
PUT /api/weather/providers/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "api_key": "string",
  "status": "string"
}
```

### 8.3. Prognozy dla Lodowiska
```
GET /api/ice-rinks/{id}/weather-forecasts
Authorization: Bearer <token>
Query params: days (1-7), include_current

Response:
{
  "success": true,
  "data": {
    "forecasts": [
      {
        "forecast_time": "datetime",
        "temperature_min": "decimal",
        "temperature_max": "decimal",
        "humidity": "decimal",
        "solar_radiation": "decimal",
        "wind_speed": "decimal",
        "precipitation_probability": "decimal",
        "data_quality": "string"
      }
    ]
  }
}
```

## 9. Endpointy Zgłoszeń Serwisowych

### 9.1. Lista Zgłoszeń
```
GET /api/service-tickets
Authorization: Bearer <token>
Query params: page, limit, status, priority, ice_rink_id, assigned_to

Response:
{
  "success": true,
  "data": {
    "tickets": [...],
    "pagination": {...}
  }
}
```

### 9.2. Szczegóły Zgłoszenia
```
GET /api/service-tickets/{id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "id": "uuid",
    "ticket_number": "string",
    "ice_rink": {...},
    "organization": {...},
    "created_by": {...},
    "assigned_to": {...},
    "priority": "string",
    "status": "string",
    "category": "string",
    "title": "string",
    "description": "string",
    "source": "string",
    "alarm_data": "json",
    "sla_target": "datetime",
    "resolved_at": "datetime",
    "closed_at": "datetime",
    "comments": [...],
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

### 9.3. Tworzenie Zgłoszenia
```
POST /api/service-tickets
Authorization: Bearer <token>
Content-Type: application/json

{
  "ice_rink_id": "uuid",
  "category": "string",
  "title": "string",
  "description": "string",
  "priority": "string"
}
```

### 9.4. Aktualizacja Statusu
```
PUT /api/service-tickets/{id}/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "string",
  "comment": "string"
}
```

### 9.5. Przypisanie Zgłoszenia
```
PUT /api/service-tickets/{id}/assign
Authorization: Bearer <token>
Content-Type: application/json

{
  "assigned_to": "uuid"
}
```

### 9.6. Dodanie Komentarza
```
POST /api/service-tickets/{id}/comments
Authorization: Bearer <token>
Content-Type: application/json

{
  "comment": "string",
  "is_internal": "boolean"
}
```

## 10. Endpointy AI i Analizy

### 10.1. Lista Modeli AI
```
GET /api/ai/models
Authorization: Bearer <token>
Query params: type, status

Response:
{
  "success": true,
  "data": {
    "models": [
      {
        "id": "uuid",
        "name": "string",
        "version": "string",
        "type": "string",
        "status": "string",
        "performance_metrics": "json",
        "deployed_at": "datetime"
      }
    ]
  }
}
```

### 10.2. Szczegóły Modelu
```
GET /api/ai/models/{id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "model": {...},
    "training_history": [...],
    "performance_charts": {...}
  }
}
```

### 10.3. Trening Modelu
```
POST /api/ai/models/{id}/train
Authorization: Bearer <token>
Content-Type: application/json

{
  "training_data_range": "json",
  "hyperparameters": "json"
}

Response:
{
  "success": true,
  "data": {
    "training_id": "uuid",
    "status": "string",
    "estimated_duration": "integer"
  }
}
```

### 10.4. Status Treningu
```
GET /api/ai/training/{training_id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "status": "string",
    "progress": "decimal",
    "current_epoch": "integer",
    "total_epochs": "integer",
    "metrics": "json"
  }
}
```

### 10.5. Deployment Modelu
```
POST /api/ai/models/{id}/deploy
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "deployment_id": "uuid",
    "status": "string",
    "deployed_at": "datetime"
  }
}
```

### 10.6. Analiza Oszczędności
```
GET /api/ai/energy-savings
Authorization: Bearer <token>
Query params: ice_rink_id, start_date, end_date, group_by

Response:
{
  "success": true,
  "data": {
    "summary": {
      "total_energy_saved": "decimal",
      "total_cost_saved": "decimal",
      "average_savings_percentage": "decimal"
    },
    "details": [
      {
        "date": "date",
        "actual_consumption": "decimal",
        "theoretical_consumption": "decimal",
        "energy_saved": "decimal",
        "savings_percentage": "decimal"
      }
    ]
  }
}
```

## 11. Endpointy Dashboard i Raporty

### 11.1. Dashboard KPI
```
GET /api/dashboard/kpi
Authorization: Bearer <token>
Query params: organization_id, time_range

Response:
{
  "success": true,
  "data": {
    "total_ice_rinks": "integer",
    "active_ice_rinks": "integer",
    "connected_ice_rinks": "integer",
    "active_tickets": "integer",
    "critical_tickets": "integer",
    "avg_ice_temperature": "decimal",
    "total_energy_consumption": "decimal",
    "energy_savings": "decimal",
    "savings_percentage": "decimal"
  }
}
```

### 11.2. Mapa Lodowisk
```
GET /api/dashboard/map
Authorization: Bearer <token>
Query params: organization_id, status_filter

Response:
{
  "success": true,
  "data": {
    "ice_rinks": [
      {
        "id": "uuid",
        "name": "string",
        "latitude": "decimal",
        "longitude": "decimal",
        "status": "string",
        "ssp_status": "string",
        "current_temperature": "decimal",
        "alerts": [...]
      }
    ]
  }
}
```

### 11.3. Generowanie Raportu
```
POST /api/reports/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "report_type": "string",
  "format": "string",
  "parameters": "json",
  "email_notification": "boolean"
}

Response:
{
  "success": true,
  "data": {
    "report_id": "uuid",
    "status": "string",
    "estimated_completion": "datetime"
  }
}
```

### 11.4. Status Raportu
```
GET /api/reports/{report_id}
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "status": "string",
    "download_url": "string",
    "created_at": "datetime",
    "completed_at": "datetime"
  }
}
```

## 12. Endpointy Systemowe

### 12.1. Status Systemu
```
GET /api/system/status
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "system_status": "string",
    "database_status": "string",
    "ssp_connections": "integer",
    "weather_api_status": "string",
    "ai_models_status": "string",
    "last_backup": "datetime",
    "uptime": "string"
  }
}
```

### 12.2. Konfiguracja Systemu
```
GET /api/system/config
Authorization: Bearer <token>
Query params: category

Response:
{
  "success": true,
  "data": {
    "config": [
      {
        "key": "string",
        "value": "string",
        "description": "string",
        "category": "string",
        "is_encrypted": "boolean"
      }
    ]
  }
}
```

### 12.3. Aktualizacja Konfiguracji
```
PUT /api/system/config/{key}
Authorization: Bearer <token>
Content-Type: application/json

{
  "value": "string"
}
```

### 12.4. Logi Systemu
```
GET /api/system/logs
Authorization: Bearer <token>
Query params: level, module, start_date, end_date, limit

Response:
{
  "success": true,
  "data": {
    "logs": [...],
    "pagination": {...}
  }
}
```

## 13. Endpointy Powiadomień

### 13.1. Lista Powiadomień
```
GET /api/notifications
Authorization: Bearer <token>
Query params: status, type, page, limit

Response:
{
  "success": true,
  "data": {
    "notifications": [...],
    "pagination": {...}
  }
}
```

### 13.2. Oznaczenie jako Przeczytane
```
PUT /api/notifications/{id}/read
Authorization: Bearer <token>

Response:
{
  "success": true,
  "message": "Powiadomienie oznaczone jako przeczytane"
}
```

### 13.3. Konfiguracja Powiadomień
```
GET /api/notifications/config
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "email_enabled": "boolean",
    "sms_enabled": "boolean",
    "webhook_enabled": "boolean",
    "notification_types": [...]
  }
}
```

## 14. Endpointy Integracji SSP

### 14.1. Odbieranie Danych z SSP
```
POST /api/ssp/data
Content-Type: application/json
X-SSP-API-Key: <ssp_api_key>

{
  "ice_rink_id": "uuid",
  "timestamp": "datetime",
  "measurements": {
    "ice_temperature": "decimal",
    "chiller_power": "decimal",
    "chiller_status": "string",
    "ambient_temperature": "decimal",
    "humidity": "decimal",
    "energy_consumption": "decimal"
  }
}

Response:
{
  "success": true,
  "data_received": "boolean",
  "timestamp": "datetime"
}
```

### 14.2. Odbieranie Alarmów z SSP
```
POST /api/ssp/alarms
Content-Type: application/json
X-SSP-API-Key: <ssp_api_key>

{
  "ice_rink_id": "uuid",
  "alarm_type": "string",
  "severity": "string",
  "message": "string",
  "timestamp": "datetime",
  "parameters": "json"
}

Response:
{
  "success": true,
  "ticket_created": "boolean",
  "ticket_number": "string"
}
```

### 14.3. Status Połączeń SSP
```
GET /api/ssp/connections
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": {
    "connections": [
      {
        "ice_rink_id": "uuid",
        "ice_rink_name": "string",
        "status": "string",
        "last_communication": "datetime",
        "response_time": "decimal",
        "error_count_24h": "integer"
      }
    ]
  }
}
```

## 15. Obsługa Błędów

### 15.1. Standardowe Kody Błędów
- **400 Bad Request** - Nieprawidłowe dane wejściowe
- **401 Unauthorized** - Brak lub nieprawidłowy token
- **403 Forbidden** - Brak uprawnień
- **404 Not Found** - Zasób nie istnieje
- **422 Unprocessable Entity** - Błąd walidacji
- **429 Too Many Requests** - Przekroczono limit zapytań
- **500 Internal Server Error** - Błąd serwera

### 15.2. Format Błędu
```json
{
  "success": false,
  "error": {
    "code": "string",
    "message": "string",
    "details": "json",
    "timestamp": "datetime"
  }
}
```

## 16. Dokumentacja i Testowanie

### 16.1. Swagger/OpenAPI
- **URL:** `/api/docs`
- **Format:** Swagger UI
- **Autoryzacja:** Wymagana dla testowania endpointów

### 16.2. Postman Collection
- **URL:** `/api/postman-collection.json`
- **Zawartość:** Kompletna kolekcja Postman z przykładami

### 16.3. Testowanie
- **Environment:** Development, Staging, Production
- **Mock Data:** Dostępne w środowisku development
- **Rate Limiting:** Wyłączone w development

## 17. Wersjonowanie API

### 17.1. Strategia Wersjonowania
- **URL Versioning:** `/api/v1/`, `/api/v2/`
- **Header Versioning:** `Accept: application/vnd.api.v1+json`
- **Backward Compatibility:** Minimum 12 miesięcy

### 17.2. Deprecation Policy
- **Warning Header:** `Deprecation: <date>`
- **Sunset Header:** `Sunset: <date>`
- **Documentation:** Aktualizowana z każdą wersją

## 18. Monitoring i Metryki

### 18.1. Endpointy Metryk
```
GET /api/metrics/health
GET /api/metrics/performance
GET /api/metrics/usage
```

### 18.2. Logi Dostępu
- Wszystkie requesty logowane
- Format: Common Log Format + custom fields
- Rotacja: Codziennie, retencja: 30 dni

### 18.3. Alerty
- **Response Time:** > 2s
- **Error Rate:** > 5%
- **Availability:** < 99.9%
- **SSP Connection:** Brak komunikacji > 5 min
