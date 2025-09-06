import asyncio
import httpx
from datetime import datetime, timezone
from fastapi_utils.tasks import repeat_every
from app.db import SessionLocal
from app.repositories.ice_rink import IceRinkRepository
from app.repositories.weather_provider import WeatherProviderRepository
from app.repositories.weather_forecast import WeatherForecastRepository

@repeat_every(seconds=60 * 60 * 3, wait_first=True) # Uruchom co 3 godziny
async def fetch_weather_forecasts_task():
    print(f"[{datetime.now()}] Running OpenWeatherMap forecast background task...")
    
    async with SessionLocal() as session:
        rink_repo = IceRinkRepository(session)
        provider_repo = WeatherProviderRepository(session)
        forecast_repo = WeatherForecastRepository(session)
        
        provider = await provider_repo.get_active_provider()
        rinks, _ = await rink_repo.get_paginated_list(limit=1000) # Pobierz wszystkie lodowiska
        
        if not provider or provider.name != 'OpenWeatherMap':
            print("Active provider is not OpenWeatherMap. Skipping task.")
            return
        if not rinks:
            print("No rinks found. Skipping task.")
            return

        all_forecasts_to_save = []
        async with httpx.AsyncClient() as client:
            for rink in rinks:
                if not rink.latitude or not rink.longitude:
                    print(f"Skipping rink '{rink.name}' due to missing coordinates.")
                    continue
                
                # Budowanie URL z endpointu, koordynatów i klucza API
                url = provider.api_endpoint.format(lat=rink.latitude, lon=rink.longitude)
                url += f"&appid={provider.api_key}"
                
                try:
                    response = await client.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Parsowanie odpowiedzi z OpenWeatherMap (/forecast)
                    forecast_list = data.get('list', [])
                    for item in forecast_list:
                        forecast_data = {
                            "ice_rink_id": rink.id,
                            "weather_provider_id": provider.id,
                            "forecast_time": datetime.fromtimestamp(item['dt'], tz=timezone.utc),
                            "temperature_min": item['main']['temp'],
                            "temperature_max": item['main']['temp'], # Endpoint /forecast podaje jedną temp.
                            "humidity": item['main']['humidity'],
                        }
                        all_forecasts_to_save.append(forecast_data)
                    print(f"Successfully fetched {len(forecast_list)} forecasts for rink '{rink.name}'.")

                except httpx.HTTPError as e:
                    print(f"HTTP error for rink '{rink.name}': {e}")
                except Exception as e:
                    print(f"An error occurred for rink '{rink.name}': {e}")
                
                await asyncio.sleep(1) # Przerwa 1 sekundy między zapytaniami, aby nie przekroczyć limitu API

        if all_forecasts_to_save:
            await forecast_repo.bulk_upsert(all_forecasts_to_save)
            print(f"Successfully saved/updated {len(all_forecasts_to_save)} forecast records in DB.")
