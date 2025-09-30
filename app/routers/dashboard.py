import uuid
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.deps import get_rink_repo, get_ticket_repo, get_measurement_repo, require_role_with_org_check
from app.repositories.ice_rink import IceRinkRepository
from app.repositories.service_ticket import ServiceTicketRepository
from app.repositories.measurement import MeasurementRepository
from app.schemas import StandardResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

class KpiResponse(BaseModel):
    total_ice_rinks: int
    active_ice_rinks: int
    connected_ice_rinks: int
    active_tickets: int
    critical_tickets: int
    avg_ice_temperature: Optional[float] = None
    total_energy_consumption: Optional[float] = None
    energy_savings: Optional[float] = None
    savings_percentage: Optional[float] = None

class MapIceRinkResponse(BaseModel):
    id: uuid.UUID
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str
    ssp_status: str
    current_temperature: Optional[float] = None
    alerts: list = []

@router.get("/kpi", response_model=StandardResponse[KpiResponse])
async def get_dashboard_kpi(
    organization_id: Optional[uuid.UUID] = Query(None),
    time_range: str = Query("7d", regex="^(1d|7d|30d|90d)$"),
    user_payload: dict = Depends(require_role_with_org_check("admin", "operator", "client")),
    rink_repo: IceRinkRepository = Depends(get_rink_repo),
    ticket_repo: ServiceTicketRepository = Depends(get_ticket_repo),
    measurement_repo: MeasurementRepository = Depends(get_measurement_repo)
):
    """Get dashboard KPI data"""
    # Determine organization filter
    if user_payload.get("role") == "client":
        org_id = uuid.UUID(user_payload.get("organization_id"))
    else:
        org_id = organization_id
    
    # Get basic counts
    filters = {"organization_id": org_id} if org_id else {}
    rinks, total_rinks = await rink_repo.get_paginated_list(filters=filters)
    
    active_rinks = len([r for r in rinks if r.status == "active"])
    connected_rinks = len([r for r in rinks if r.ssp_status == "connected"])
    
    # Get ticket counts
    tickets, total_tickets = await ticket_repo.get_paginated_list()
    active_tickets = len([t for t in tickets if t.status in ["new", "assigned", "in_progress"]])
    critical_tickets = len([t for t in tickets if t.priority == "critical" and t.status != "closed"])
    
    # Calculate time range
    days = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}[time_range]
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get measurement data for calculations
    avg_temp = None
    total_energy = None
    
    if rinks:
        # Get latest measurements for average temperature
        latest_measurements = []
        for rink in rinks:
            measurement = await measurement_repo.get_latest_for_rink(rink.id)
            if measurement:
                latest_measurements.append(measurement.ice_temperature)
        
        if latest_measurements:
            avg_temp = sum(latest_measurements) / len(latest_measurements)
        
        # Get energy consumption data
        energy_measurements = []
        for rink in rinks:
            measurements, _ = await measurement_repo.get_measurements_for_rink(
                rink.id, start_date=start_date, limit=1000
            )
            for m in measurements:
                if m.energy_consumption:
                    energy_measurements.append(m.energy_consumption)
        
        if energy_measurements:
            total_energy = sum(energy_measurements)
    
    return StandardResponse(
        data=KpiResponse(
            total_ice_rinks=total_rinks,
            active_ice_rinks=active_rinks,
            connected_ice_rinks=connected_rinks,
            active_tickets=active_tickets,
            critical_tickets=critical_tickets,
            avg_ice_temperature=avg_temp,
            total_energy_consumption=total_energy,
            energy_savings=0.0,  # Would need AI calculations
            savings_percentage=0.0  # Would need AI calculations
        )
    )

@router.get("/map", response_model=StandardResponse[list])
async def get_dashboard_map(
    organization_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None),
    user_payload: dict = Depends(require_role_with_org_check("admin", "operator", "client")),
    rink_repo: IceRinkRepository = Depends(get_rink_repo),
    measurement_repo: MeasurementRepository = Depends(get_measurement_repo)
):
    """Get ice rinks data for map display"""
    # Determine organization filter
    if user_payload.get("role") == "client":
        org_id = uuid.UUID(user_payload.get("organization_id"))
    else:
        org_id = organization_id
    
    filters = {"organization_id": org_id} if org_id else {}
    if status_filter:
        filters["status"] = status_filter
    
    rinks, _ = await rink_repo.get_paginated_list(filters=filters)
    
    map_data = []
    for rink in rinks:
        # Get current temperature
        current_temp = None
        measurement = await measurement_repo.get_latest_for_rink(rink.id)
        if measurement:
            current_temp = measurement.ice_temperature
        
        map_data.append(MapIceRinkResponse(
            id=rink.id,
            name=rink.name,
            latitude=rink.latitude,
            longitude=rink.longitude,
            status=rink.status,
            ssp_status=rink.ssp_status,
            current_temperature=current_temp,
            alerts=[]  # Would need to implement alert system
        ))
    
    return StandardResponse(data=map_data)