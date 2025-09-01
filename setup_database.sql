-- =====================================================
-- Struktura Bazy Danych - Centralny System Zarządzania Energią dla Lodowisk
-- Wersja: 1.0 (Finalna z dynamicznym UUID)
-- Data: 2025-01-27
-- Baza danych: PostgreSQL 14+
-- =====================================================

-- Włączenie rozszerzenia dla UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Włączenie rozszerzenia dla szyfrowania
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- 1. TWORZENIE SCHEMATÓW
-- =====================================================
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS timeseries;
CREATE SCHEMA IF NOT EXISTS ai_models;

-- =====================================================
-- 2. FUNKCJE POMOCNICZE
-- =====================================================

-- Funkcja do automatycznej aktualizacji updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Funkcja do generowania numeru zgłoszenia
CREATE OR REPLACE FUNCTION generate_ticket_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ticket_number := 'TICKET-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || 
                        LPAD(CAST(nextval('ticket_sequence') AS TEXT), 4, '0');
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Sekwencja dla numerów zgłoszeń
CREATE SEQUENCE IF NOT EXISTS ticket_sequence START 1;

-- =====================================================
-- 3. TWORZENIE TABEL
-- =====================================================

-- 3.1. Tabela: organizations (Organizacje/Klienci)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL DEFAULT 'client' CHECK (type IN ('client', 'partner', 'internal')),
    address TEXT,
    contact_person VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    tax_id VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

-- 3.2. Tabela: users (Użytkownicy)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'operator' CHECK (role IN ('admin', 'operator', 'client')),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'locked')),
    last_login TIMESTAMPTZ,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    password_changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- 3.3. Tabela: user_permissions (Uprawnienia Użytkowników)
CREATE TABLE user_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    module VARCHAR(100) NOT NULL,
    permission VARCHAR(50) NOT NULL CHECK (permission IN ('read', 'write', 'admin')),
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    granted_by UUID NOT NULL REFERENCES users(id),
    expires_at TIMESTAMPTZ,
    UNIQUE(user_id, module, permission)
);

-- 3.4. Tabela: ice_rinks (Lodowiska)
CREATE TABLE ice_rinks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(500) NOT NULL,
    latitude NUMERIC(10,8),
    longitude NUMERIC(11,8),
    dimensions JSONB NOT NULL DEFAULT '{}',
    type VARCHAR(50) NOT NULL DEFAULT 'standard' CHECK (type IN ('standard', 'olympic', 'training')),
    chiller_type VARCHAR(100) NOT NULL,
    max_power_consumption NUMERIC(10,2) NOT NULL,
    ssp_endpoint VARCHAR(500),
    ssp_api_key VARCHAR(255),
    ssp_status VARCHAR(20) NOT NULL DEFAULT 'disconnected' CHECK (ssp_status IN ('connected', 'disconnected', 'error')),
    last_communication TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'maintenance', 'inactive')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    UNIQUE(organization_id, name)
);

-- 3.5. Tabela: weather_providers (Dostawcy Danych Pogodowych)
CREATE TABLE weather_providers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    api_endpoint VARCHAR(500) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'error')),
    rate_limit INTEGER NOT NULL DEFAULT 1000,
    last_used TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3.6. Tabela: weather_forecasts (Prognozy Pogodowe)
CREATE TABLE weather_forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ice_rink_id UUID NOT NULL REFERENCES ice_rinks(id) ON DELETE CASCADE,
    weather_provider_id UUID NOT NULL REFERENCES weather_providers(id) ON DELETE RESTRICT,
    forecast_time TIMESTAMPTZ NOT NULL,
    temperature_min NUMERIC(5,2) NOT NULL,
    temperature_max NUMERIC(5,2) NOT NULL,
    humidity NUMERIC(5,2),
    solar_radiation NUMERIC(8,2),
    wind_speed NUMERIC(5,2),
    precipitation_probability NUMERIC(5,2),
    data_quality VARCHAR(20) NOT NULL DEFAULT 'good' CHECK (data_quality IN ('good', 'medium', 'poor')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3.7. Tabela: measurements (Pomiary z Lodowisk)
CREATE TABLE measurements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ice_rink_id UUID NOT NULL REFERENCES ice_rinks(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    ice_temperature NUMERIC(5,2) NOT NULL,
    chiller_power NUMERIC(10,2) NOT NULL,
    chiller_status VARCHAR(50) NOT NULL,
    ambient_temperature NUMERIC(5,2),
    humidity NUMERIC(5,2),
    energy_consumption NUMERIC(10,2) NOT NULL,
    data_source VARCHAR(50) NOT NULL DEFAULT 'ssp' CHECK (data_source IN ('ssp', 'manual', 'calculated')),
    quality_score NUMERIC(3,2) NOT NULL DEFAULT 1.00 CHECK (quality_score BETWEEN 0.00 AND 1.00),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(ice_rink_id, timestamp)
);

-- 3.8. Tabela: ai_models (Modele AI)
CREATE TABLE ai_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    type VARCHAR(100) NOT NULL CHECK (type IN ('consumption_prediction', 'optimization')),
    status VARCHAR(20) NOT NULL DEFAULT 'training' CHECK (status IN ('training', 'active', 'archived', 'error')),
    model_file_path VARCHAR(500),
    hyperparameters JSONB NOT NULL DEFAULT '{}',
    training_data_range JSONB NOT NULL DEFAULT '{}',
    performance_metrics JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL REFERENCES users(id),
    deployed_at TIMESTAMPTZ,
    UNIQUE(name, version)
);

-- 3.9. Tabela: theoretical_consumption (Teoretyczne Zużycie Energii)
CREATE TABLE theoretical_consumption (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ice_rink_id UUID NOT NULL REFERENCES ice_rinks(id) ON DELETE CASCADE,
    ai_model_id UUID NOT NULL REFERENCES ai_models(id) ON DELETE RESTRICT,
    timestamp TIMESTAMPTZ NOT NULL,
    theoretical_consumption NUMERIC(10,2) NOT NULL,
    confidence_score NUMERIC(3,2) NOT NULL CHECK (confidence_score BETWEEN 0.00 AND 1.00),
    input_parameters JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(ice_rink_id, timestamp)
);

-- 3.10. Tabela: service_tickets (Zgłoszenia Serwisowe)
CREATE TABLE service_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_number VARCHAR(50) UNIQUE,
    ice_rink_id UUID NOT NULL REFERENCES ice_rinks(id) ON DELETE RESTRICT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    created_by UUID NOT NULL REFERENCES users(id),
    assigned_to UUID REFERENCES users(id),
    priority VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'assigned', 'in_progress', 'resolved', 'closed')),
    category VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    source VARCHAR(20) NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'automatic', 'system')),
    alarm_data JSONB DEFAULT '{}',
    sla_target TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3.11. Tabela: ticket_comments (Komentarze do Zgłoszeń)
CREATE TABLE ticket_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES service_tickets(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    comment TEXT NOT NULL,
    is_internal BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3.12. Tabela: audit_logs (Logi Audytowe) - w schemacie audit
CREATE TABLE audit.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    module VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    details JSONB NOT NULL DEFAULT '{}',
    result VARCHAR(20) NOT NULL DEFAULT 'success' CHECK (result IN ('success', 'failure', 'error')),
    error_message TEXT
);

-- 3.13. Tabela: notifications (Powiadomienia)
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    type VARCHAR(50) NOT NULL CHECK (type IN ('email', 'sms', 'webhook', 'in_app')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'read')),
    sent_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3.14. Tabela: system_config (Konfiguracja Systemu)
CREATE TABLE system_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) NOT NULL UNIQUE,
    value TEXT NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL CHECK (category IN ('general', 'security', 'ai', 'weather')),
    is_encrypted BOOLEAN NOT NULL DEFAULT false,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID NOT NULL REFERENCES users(id)
);

-- 3.15. Tabela: user_sessions (Aktywne sesje użytkowników)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY, -- Będzie to JTI z tokenu JWT
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true
);

-- =====================================================
-- 4. TWORZENIE INDEKSÓW
-- =====================================================
CREATE INDEX idx_organizations_status ON organizations(status);
CREATE INDEX idx_organizations_type ON organizations(type);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_user_permissions_module ON user_permissions(module);
CREATE INDEX idx_ice_rinks_organization_id ON ice_rinks(organization_id);
CREATE INDEX idx_ice_rinks_status ON ice_rinks(status);
CREATE INDEX idx_ice_rinks_ssp_status ON ice_rinks(ssp_status);
CREATE INDEX idx_ice_rinks_location ON ice_rinks(location);
CREATE INDEX idx_weather_providers_status ON weather_providers(status);
CREATE INDEX idx_weather_forecasts_ice_rink_time ON weather_forecasts(ice_rink_id, forecast_time);
CREATE INDEX idx_weather_forecasts_time ON weather_forecasts(forecast_time);
CREATE INDEX idx_measurements_ice_rink_time ON measurements(ice_rink_id, timestamp);
CREATE INDEX idx_measurements_timestamp ON measurements(timestamp);
CREATE INDEX idx_measurements_data_source ON measurements(data_source);
CREATE INDEX idx_ai_models_status ON ai_models(status);
CREATE INDEX idx_ai_models_type ON ai_models(type);
CREATE INDEX idx_theoretical_consumption_ice_rink_time ON theoretical_consumption(ice_rink_id, timestamp);
CREATE INDEX idx_theoretical_consumption_ai_model ON theoretical_consumption(ai_model_id);
CREATE INDEX idx_service_tickets_status ON service_tickets(status);
CREATE INDEX idx_service_tickets_priority ON service_tickets(priority);
CREATE INDEX idx_service_tickets_ice_rink_id ON service_tickets(ice_rink_id);
CREATE INDEX idx_service_tickets_assigned_to ON service_tickets(assigned_to);
CREATE INDEX idx_service_tickets_created_at ON service_tickets(created_at);
CREATE INDEX idx_ticket_comments_ticket_id ON ticket_comments(ticket_id);
CREATE INDEX idx_ticket_comments_created_at ON ticket_comments(created_at);
CREATE INDEX idx_audit_logs_timestamp ON audit.audit_logs(timestamp);
CREATE INDEX idx_audit_logs_user_id ON audit.audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit.audit_logs(action);
CREATE INDEX idx_audit_logs_module ON audit.audit_logs(module);
CREATE INDEX idx_audit_logs_resource ON audit.audit_logs(resource_type, resource_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_organization_id ON notifications(organization_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_system_config_category ON system_config(category);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);

-- =====================================================
-- 5. TWORZENIE TRIGGERÓW
-- =====================================================
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ice_rinks_updated_at BEFORE UPDATE ON ice_rinks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_weather_providers_updated_at BEFORE UPDATE ON weather_providers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ai_models_updated_at BEFORE UPDATE ON ai_models FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_service_tickets_updated_at BEFORE UPDATE ON service_tickets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_config_updated_at BEFORE UPDATE ON system_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER generate_ticket_number_trigger BEFORE INSERT ON service_tickets FOR EACH ROW EXECUTE FUNCTION generate_ticket_number();

-- =====================================================
-- 6. TWORZENIE WIDOKÓW
-- =====================================================
CREATE VIEW dashboard_kpi AS SELECT COUNT(DISTINCT ir.id) as total_ice_rinks, COUNT(DISTINCT CASE WHEN ir.status = 'active' THEN ir.id END) as active_ice_rinks, COUNT(DISTINCT CASE WHEN ir.ssp_status = 'connected' THEN ir.id END) as connected_ice_rinks, COUNT(DISTINCT CASE WHEN st.status IN ('new', 'assigned', 'in_progress') THEN st.id END) as active_tickets, COUNT(DISTINCT CASE WHEN st.priority = 'critical' THEN st.id END) as critical_tickets, AVG(m.ice_temperature) as avg_ice_temperature, SUM(m.energy_consumption) as total_energy_consumption FROM ice_rinks ir LEFT JOIN measurements m ON ir.id = m.ice_rink_id AND m.timestamp >= NOW() - INTERVAL '24 hours' LEFT JOIN service_tickets st ON ir.id = st.ice_rink_id AND st.status NOT IN ('resolved', 'closed') WHERE ir.status != 'inactive';
CREATE VIEW energy_savings AS SELECT ir.id as ice_rink_id, ir.name as ice_rink_name, ir.organization_id, m.timestamp, m.energy_consumption as actual_consumption, tc.theoretical_consumption, (tc.theoretical_consumption - m.energy_consumption) as energy_saved, CASE WHEN tc.theoretical_consumption > 0 THEN ((tc.theoretical_consumption - m.energy_consumption) / tc.theoretical_consumption * 100) ELSE 0 END as savings_percentage FROM measurements m JOIN ice_rinks ir ON m.ice_rink_id = ir.id LEFT JOIN theoretical_consumption tc ON m.ice_rink_id = tc.ice_rink_id AND m.timestamp = tc.timestamp WHERE m.timestamp >= NOW() - INTERVAL '30 days';

-- =====================================================
-- 7. DANE INICJALIZACYJNE
-- =====================================================
WITH ins_org AS (
    INSERT INTO organizations (name, type, status)
    VALUES ('System Administration', 'internal', 'active')
    RETURNING id
),
ins_admin AS (
    INSERT INTO users (organization_id, username, email, password_hash, first_name, last_name, role, status)
    SELECT id, 'admin', 'admin@system.com', crypt('admin123', gen_salt('bf')), 'System', 'Administrator', 'admin', 'active'
    FROM ins_org
    RETURNING id
)
INSERT INTO system_config (key, value, description, category, updated_by)
SELECT v.key, v.value, v.description, v.category, a.id
FROM (
    VALUES
        ('system.name', 'Centralny System Zarządzania Energią dla Lodowisk', 'Nazwa systemu', 'general'),
        ('system.version', '1.0.0', 'Wersja systemu', 'general'),
        ('security.session_timeout', '3600', 'Timeout sesji w sekundach', 'security'),
        ('ai.model_retraining_interval', '168', 'Interwał retrenowania modeli AI w godzinach', 'ai'),
        ('weather.update_interval', '900', 'Interwał aktualizacji prognoz pogodowych w sekundach', 'weather')
) AS v(key, value, description, category)
CROSS JOIN (SELECT id FROM ins_admin) a;

INSERT INTO weather_providers (name, api_endpoint, api_key, status, rate_limit) VALUES
('OpenWeatherMap', 'https://api.openweathermap.org/data/2.5', 'DEMO_KEY', 'inactive', 1000),
('AccuWeather', 'https://dataservice.accuweather.com', 'DEMO_KEY', 'inactive', 500),
('WeatherAPI.com', 'https://api.weatherapi.com/v1', 'DEMO_KEY', 'inactive', 1000);

-- =====================================================
-- 8. UPRAWNIENIA
-- =====================================================
GRANT USAGE ON SCHEMA audit TO PUBLIC;
GRANT ALL ON ALL TABLES IN SCHEMA audit TO PUBLIC;
GRANT ALL ON ALL SEQUENCES IN SCHEMA audit TO PUBLIC;
GRANT USAGE ON SCHEMA timeseries TO PUBLIC;
GRANT ALL ON ALL TABLES IN SCHEMA timeseries TO PUBLIC;
GRANT ALL ON ALL SEQUENCES IN SCHEMA timeseries TO PUBLIC;
GRANT USAGE ON SCHEMA ai_models TO PUBLIC;
GRANT ALL ON ALL TABLES IN SCHEMA ai_models TO PUBLIC;
GRANT ALL ON ALL SEQUENCES IN SCHEMA ai_models TO PUBLIC;

-- =====================================================
-- 9. KOMENTARZE DO TABEL
-- =====================================================
COMMENT ON TABLE organizations IS 'Tabela organizacji i klientów systemu';
COMMENT ON TABLE users IS 'Tabela użytkowników systemu z różnymi rolami';
COMMENT ON TABLE user_permissions IS 'Tabela uprawnień użytkowników do modułów systemu';
COMMENT ON TABLE ice_rinks IS 'Tabela lodowisk monitorowanych przez system';
COMMENT ON TABLE weather_providers IS 'Tabela dostawców danych pogodowych';
COMMENT ON TABLE weather_forecasts IS 'Tabela prognoz pogodowych dla lodowisk';
COMMENT ON TABLE measurements IS 'Tabela pomiarów z lodowisk (dane szeregów czasowych)';
COMMENT ON TABLE ai_models IS 'Tabela modeli AI i ich metryk';
COMMENT ON TABLE theoretical_consumption IS 'Tabela teoretycznego zużycia energii obliczonego przez AI';
COMMENT ON TABLE service_tickets IS 'Tabela zgłoszeń serwisowych';
COMMENT ON TABLE ticket_comments IS 'Tabela komentarzy do zgłoszeń serwisowych';
COMMENT ON TABLE audit.audit_logs IS 'Tabela logów audytowych systemu';
COMMENT ON TABLE notifications IS 'Tabela powiadomień systemowych';
COMMENT ON TABLE system_config IS 'Tabela konfiguracji systemu';
COMMENT ON TABLE user_sessions IS 'Tabela do śledzenia aktywnych sesji (tokenów JWT) dla mechanizmu wylogowania.';

-- =====================================================
-- 10. POLITYKI RETENCJI (PRZYKŁADY)
-- =====================================================
-- Przykład funkcji do czyszczenia starych danych (do implementacji w cron)
-- CREATE OR REPLACE FUNCTION cleanup_old_data()
-- RETURNS void AS $$
-- BEGIN
--     -- Usuwanie pomiarów starszych niż 2 lata
--     DELETE FROM measurements WHERE timestamp < NOW() - INTERVAL '2 years';
--     
--     -- Usuwanie prognoz pogodowych starszych niż 1 rok
--     DELETE FROM weather_forecasts WHERE forecast_time < NOW() - INTERVAL '1 year';
--     
--     -- Usuwanie logów audytowych starszych niż 5 lat
--     DELETE FROM audit.audit_logs WHERE timestamp < NOW() - INTERVAL '5 years';
-- END;
-- $$ LANGUAGE plpgsql;

-- =====================================================
-- KONIEC SKRYPTU
-- =====================================================
