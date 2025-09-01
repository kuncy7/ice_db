import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from sqlalchemy.sql import func

from app.database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False, server_default='client')
    address = Column(Text, nullable=True)
    contact_person = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    tax_id = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, server_default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)

    users = relationship("User", back_populates="organization", foreign_keys="User.organization_id")
    ice_rinks = relationship("IceRink", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, server_default='operator')
    status = Column(String(20), nullable=False, server_default='active')
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, nullable=False, server_default='0')
    password_changed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    organization = relationship("Organization", back_populates="users", foreign_keys=[organization_id])
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    created_ice_rinks = relationship("IceRink", back_populates="creator", foreign_keys="IceRink.created_by")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="sessions")


class IceRink(Base):
    __tablename__ = "ice_rinks"

    measurements = relationship("Measurement", back_populates="ice_rink", cascade="all, delete-orphan")
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    location = Column(String(500), nullable=False)
    latitude = Column(NUMERIC(10, 8), nullable=True)
    longitude = Column(NUMERIC(11, 8), nullable=True)
    dimensions = Column(JSON, nullable=False, default={})
    type = Column(String(50), nullable=False, server_default='standard')
    chiller_type = Column(String(100), nullable=False)
    max_power_consumption = Column(NUMERIC(10, 2), nullable=False)
    ssp_endpoint = Column(String(500), nullable=True)
    ssp_api_key = Column(String(255), nullable=True)
    ssp_status = Column(String(20), nullable=False, server_default='disconnected')
    last_communication = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, server_default='active')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    organization = relationship("Organization", back_populates="ice_rinks")
    creator = relationship("User", back_populates="created_ice_rinks", foreign_keys=[created_by])

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ice_rink_id = Column(UUID(as_uuid=True), ForeignKey("ice_rinks.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    ice_temperature = Column(NUMERIC(5, 2), nullable=False)
    chiller_power = Column(NUMERIC(10, 2), nullable=False)
    chiller_status = Column(String(50), nullable=False)
    ambient_temperature = Column(NUMERIC(5, 2), nullable=True)
    humidity = Column(NUMERIC(5, 2), nullable=True)
    energy_consumption = Column(NUMERIC(10, 2), nullable=False)
    data_source = Column(String(50), nullable=False, server_default='manual')
    quality_score = Column(NUMERIC(3, 2), nullable=False, server_default='1.00')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ice_rink = relationship("IceRink", back_populates="measurements")
