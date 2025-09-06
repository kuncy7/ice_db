import uuid
import io
import csv
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

from app.deps import require_role, get_measurement_repo, get_rink_repo
from app.repositories.measurement import MeasurementRepository
from app.repositories.ice_rink import IceRinkRepository
from app.schemas import MeasurementResponse

router = APIRouter(prefix="/api/ice-rinks/{rink_id}/measurements", tags=["measurements"])

# ... endpointy list_measurements i get_latest_measurement bez zmian (skopiuj je z poprzedniej poprawnej wersji) ...

@router.get("/export")
async def export_measurements(
    rink_id: uuid.UUID,
    format: str = Query("csv", enum=["csv", "json", "xlsx"]),
    limit: int = 1000,
    measurement_repo: MeasurementRepository = Depends(get_measurement_repo),
    rink_repo: IceRinkRepository = Depends(get_rink_repo),
    _=Depends(require_role("admin", "operator", "client"))
):
    # Pobieramy obiekt lodowiska, żeby mieć jego nazwę
    rink = await rink_repo.get_by_id(rink_id)
    if not rink:
        raise HTTPException(status_code=404, detail="Ice rink not found")

    # Pobieramy pomiary (razem z dołączonymi danymi lodowiska)
    measurements, _ = await measurement_repo.get_measurements_for_rink(rink_id=rink_id, limit=limit)
    
    if not measurements:
        return {"message": "No data to export for this ice rink."}

    # Przygotowujemy dane do eksportu, podmieniając ID na nazwę
    data_to_export = []
    for m in measurements:
        data = MeasurementResponse.model_validate(m).model_dump()
        data['ice_rink_name'] = m.ice_rink.name  # Dodajemy nazwę lodowiska
        del data['id']                         # Usuwamy techniczne ID pomiaru
        del data['ice_rink_id']                # Usuwamy techniczne ID lodowiska
        data_to_export.append(data)

    if format == "json":
        return data_to_export

    # Przygotowanie nagłówków w odpowiedniej kolejności
    headers = ['ice_rink_name'] + [key for key in data_to_export[0].keys() if key != 'ice_rink_name']

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data_to_export)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                                 headers={"Content-Disposition": f"attachment; filename={rink.name}_measurements.csv"})

    elif format == "xlsx":
        wb = Workbook()
        ws = wb.active
        ws.title = "Measurements"
        ws.append(headers)

        for row_data in data_to_export:
            row_values = [row_data.get(header) for header in headers]
            # Konwersja strefy czasowej
            for i, value in enumerate(row_values):
                if isinstance(value, datetime) and value.tzinfo:
                    row_values[i] = value.astimezone(timezone.utc).replace(tzinfo=None)
            ws.append(row_values)

        # Poprawny sposób zapisu do pamięci
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{rink.name}_measurements.xlsx"'}
        )
