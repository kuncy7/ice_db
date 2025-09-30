import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from pydantic import BaseModel

from app.deps import get_measurement_repo, get_ticket_repo, get_rink_repo, require_role
from app.repositories.measurement import MeasurementRepository
from app.repositories.service_ticket import ServiceTicketRepository
from app.repositories.ice_rink import IceRinkRepository
from app.schemas import StandardResponse
from app.errors import http_401, http_404

router = APIRouter(prefix="/api/ssp", tags=["ssp"])

# Schematy dla SSP
class SspDataRequest(BaseModel):
    ice_rink_id: uuid.UUID
    timestamp: datetime
    measurements: dict

class SspAlarmRequest(BaseModel):
    ice_rink_id: uuid.UUID
    alarm_type: str
    severity: str
    message: str
    timestamp: datetime
    parameters: Optional[dict] = None

class SspConnectionResponse(BaseModel):
    ice_rink_id: uuid.UUID
    ice_rink_name: str
    status: str
    last_communication: Optional[datetime] = None
    response_time: Optional[float] = None
    error_count_24h: int = 0

async def verify_ssp_api_key(ssp_api_key: str = Header(..., alias="X-SSP-API-Key")):
    """Verify SSP API key - simplified implementation"""
    # In production, this should check against database
    if not ssp_api_key or len(ssp_api_key) < 10:
        http_401("Invalid SSP API key")
    return ssp_api_key

@router.post("/data", response_model=StandardResponse[dict])
async def receive_ssp_data(
    data: SspDataRequest,
    ssp_api_key: str = Depends(verify_ssp_api_key),
    measurement_repo: MeasurementRepository = Depends(get_measurement_repo),
    rink_repo: IceRinkRepository = Depends(get_rink_repo)
):
    """Receive measurement data from SSP systems"""
    # Verify ice rink exists
    rink = await rink_repo.get_by_id(data.ice_rink_id)
    if not rink:
        http_404("Ice rink not found")
    
    # Create measurement record
    measurement_data = {
        "ice_rink_id": data.ice_rink_id,
        "timestamp": data.timestamp,
        "ice_temperature": data.measurements.get("ice_temperature", 0.0),
        "chiller_power": data.measurements.get("chiller_power", 0.0),
        "chiller_status": data.measurements.get("chiller_status", "unknown"),
        "ambient_temperature": data.measurements.get("ambient_temperature"),
        "humidity": data.measurements.get("humidity"),
        "energy_consumption": data.measurements.get("energy_consumption", 0.0),
        "data_source": "ssp",
        "quality_score": 1.0
    }
    
    await measurement_repo.create(measurement_data)
    
    return StandardResponse(
        data={
            "data_received": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

@router.post("/alarms", response_model=StandardResponse[dict])
async def receive_ssp_alarms(
    alarm: SspAlarmRequest,
    ssp_api_key: str = Depends(verify_ssp_api_key),
    ticket_repo: ServiceTicketRepository = Depends(get_ticket_repo),
    rink_repo: IceRinkRepository = Depends(get_rink_repo)
):
    """Receive alarm data from SSP systems"""
    # Verify ice rink exists
    rink = await rink_repo.get_by_id(alarm.ice_rink_id)
    if not rink:
        http_404("Ice rink not found")
    
    # Create service ticket
    ticket_data = {
        "ice_rink_id": alarm.ice_rink_id,
        "organization_id": rink.organization_id,
        "created_by_id": None,  # System generated
        "category": "ssp_alarm",
        "title": f"SSP Alarm: {alarm.alarm_type}",
        "description": alarm.message,
        "priority": "high" if alarm.severity == "critical" else "medium",
        "source": "ssp",
        "alarm_data": {
            "alarm_type": alarm.alarm_type,
            "severity": alarm.severity,
            "parameters": alarm.parameters or {}
        }
    }
    
    ticket = await ticket_repo.create(ticket_data)
    
    return StandardResponse(
        data={
            "ticket_created": True,
            "ticket_number": ticket.ticket_number
        }
    )

@router.get("/connections", response_model=StandardResponse[list])
async def get_ssp_connections(
    rink_repo: IceRinkRepository = Depends(get_rink_repo),
    _=Depends(require_role("admin", "operator"))
):
    """Get status of all SSP connections"""
    # Get all ice rinks with SSP configuration
    rinks = await rink_repo.get_all_with_ssp()
    
    connections = []
    for rink in rinks:
        connections.append(SspConnectionResponse(
            ice_rink_id=rink.id,
            ice_rink_name=rink.name,
            status=rink.ssp_status,
            last_communication=rink.last_communication,
            response_time=None,  # Would need to implement ping
            error_count_24h=0     # Would need to implement error tracking
        ))
    
    return StandardResponse(data=connections)