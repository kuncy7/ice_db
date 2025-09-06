import uuid
from sqlalchemy import (Column, String, ForeignKey, DateTime, func, JSON,
                          Numeric, Boolean, Text, Integer)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False, default='client')
    address = Column(String)
    contact_person = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    tax_id = Column(String(20))
    status = Column(String(20), nullable=False, default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    users = relationship("User", back_populates="organization")
    ice_rinks = relationship("IceRink", back_populates="organization")

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    username = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(50), nullable=False, default='operator')
    status = Column(String(20), nullable=False, default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    organization = relationship("Organization", back_populates="users")

class IceRink(Base):
    __tablename__ = "ice_rinks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    name = Column(String(255), nullable=False)
    location = Column(String(500), nullable=False)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    dimensions = Column(JSON, nullable=False, default={})
    type = Column(String(50), nullable=False, default='standard')
    chiller_type = Column(String(100), nullable=False)
    max_power_consumption = Column(Numeric(10, 2), nullable=False)
    ssp_endpoint = Column(String(500))
    ssp_api_key = Column(String(255))
    ssp_status = Column(String(20), nullable=False, default='disconnected')
    last_communication = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    organization = relationship("Organization", back_populates="ice_rinks")
    measurements = relationship("Measurement", back_populates="ice_rink", cascade="all, delete-orphan")
    weather_forecasts = relationship("WeatherForecast", back_populates="ice_rink", cascade="all, delete-orphan")

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ice_rink_id = Column(UUID(as_uuid=True), ForeignKey('ice_rinks.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    ice_temperature = Column(Numeric(5, 2), nullable=False)
    chiller_power = Column(Numeric(10, 2), nullable=False)
    chiller_status = Column(String(50), nullable=False)
    ambient_temperature = Column(Numeric(5, 2))
    humidity = Column(Numeric(5, 2))
    energy_consumption = Column(Numeric(10, 2), nullable=False)
    data_source = Column(String(50), nullable=False, default='ssp')
    quality_score = Column(Numeric(3, 2), nullable=False, default=1.00)
    
    ice_rink = relationship("IceRink", back_populates="measurements")

# NOWA, KOMPLETNA KLASA
class WeatherProvider(Base):
    __tablename__ = "weather_providers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    api_endpoint = Column(String(500), nullable=False)
    api_key = Column(String(255))
    status = Column(String(20), nullable=False, default='active')
    rate_limit = Column(Integer, nullable=False, default=1000)
    last_used = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    forecasts = relationship("WeatherForecast", back_populates="provider")

# ZAKTUALIZOWANA KLASA
class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ice_rink_id = Column(UUID(as_uuid=True), ForeignKey('ice_rinks.id'), nullable=False)
    weather_provider_id = Column(UUID(as_uuid=True), ForeignKey('weather_providers.id'))
    forecast_time = Column(DateTime(timezone=True), nullable=False, index=True)
    temperature_min = Column(Numeric(5, 2), nullable=False)
    temperature_max = Column(Numeric(5, 2), nullable=False)
    humidity = Column(Numeric(5, 2))
    solar_radiation = Column(Numeric(8, 2))
    wind_speed = Column(Numeric(5, 2))
    precipitation_probability = Column(Numeric(5, 2))
    
    ice_rink = relationship("IceRink", back_populates="weather_forecasts")
    provider = relationship("WeatherProvider", back_populates="forecasts")

class ServiceTicket(Base):
    __tablename__ = "service_tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(String(50), unique=True, index=True)
    ice_rink_id = Column(UUID(as_uuid=True), ForeignKey('ice_rinks.id'), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False)
    created_by_id = Column("created_by", UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    assigned_to_id = Column("assigned_to", UUID(as_uuid=True), ForeignKey('users.id'))
    
    priority = Column(String(20), nullable=False, default='medium')
    status = Column(String(20), nullable=False, default='new', index=True)
    category = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    source = Column(String(20), nullable=False, default='manual')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    ice_rink = relationship("IceRink")
    organization = relationship("Organization")
    created_by = relationship("User", foreign_keys=[created_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan")

class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey('service_tickets.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    comment = Column(Text, nullable=False)
    is_internal = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("ServiceTicket", back_populates="comments")
    user = relationship("User")

class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(String(100), nullable=False, index=True)
    is_encrypted = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by_id = Column("updated_by", UUID(as_uuid=True), ForeignKey('users.id'))

    # Relacja do użytkownika, który ostatnio modyfikował wpis
    updated_by = relationship("User", foreign_keys=[updated_by_id])

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True) # To będzie JTI z tokena
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    user = relationship("User")
