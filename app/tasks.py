import asyncio
import httpx
from datetime import datetime, timezone
from fastapi_utils.tasks import repeat_every
from app.db import SessionLocal
from app.repositories.ice_rink import IceRinkRepository
from app.repositories.weather_provider import WeatherProviderRepository
from app.repositories.weather_forecast import WeatherForecastRepository
from app.repositories.system_config import SystemConfigRepository
import logging

logger = logging.getLogger(__name__)

@repeat_every(seconds=60 * 60 * 3, wait_first=True)
async def fetch_weather_forecasts_task():
    logger.info("Running OpenWeatherMap forecast background task...")
    
    try:
        async with SessionLocal() as session:
            rink_repo = IceRinkRepository(session)
            provider_repo = WeatherProviderRepository(session)
            forecast_repo = WeatherForecastRepository(session)
            config_repo = SystemConfigRepository(session)
            
            provider = await provider_repo.get_active_provider()
            rinks, _ = await rink_repo.get_paginated_list(limit=1000)
            
            if not provider or provider.name != 'OpenWeatherMap' or not rinks:
                status_msg = "error: No active OpenWeatherMap provider or no rinks found."
                logger.warning(status_msg)
                await config_repo.set_config_value("weather_api_status", status_msg)
                return

            has_errors = False
            all_forecasts_to_save = []
            async with httpx.AsyncClient() as client:
                for rink in rinks:
                    if not rink.latitude or not rink.longitude:
                        continue
                    
                    url = provider.api_endpoint.format(lat=rink.latitude, lon=rink.longitude) + f"&appid={provider.api_key}"
                    
                    try:
                        response = await client.get(url, timeout=10)
                        response.raise_for_status()
                        
                        data = response.json()
                        forecast_list = data.get('list', [])
                        for item in forecast_list:
                            forecast_data = {
                                "ice_rink_id": rink.id,
                                "weather_provider_id": provider.id,
                                "forecast_time": datetime.fromtimestamp(item['dt'], tz=timezone.utc),
                                "temperature_min": item['main']['temp'],
                                "temperature_max": item['main']['temp'],
                                "humidity": item['main']['humidity'],
                            }
                            all_forecasts_to_save.append(forecast_data)
                        logger.info(f"Successfully fetched {len(forecast_list)} forecasts for rink '{rink.name}'.")

                    except Exception as e:
                        has_errors = True
                        logger.error(f"An error occurred for rink '{rink.name}': {e}")
                    
                    await asyncio.sleep(1)

            # --- KLUCZOWA POPRAWKA: Przywrócenie zapisu do bazy ---
            if all_forecasts_to_save:
                await forecast_repo.bulk_upsert(all_forecasts_to_save)
                logger.info(f"Successfully saved/updated {len(all_forecasts_to_save)} forecast records in DB.")
            
            if has_errors:
                await config_repo.set_config_value("weather_api_status", "degraded")
            else:
                await config_repo.set_config_value("weather_api_status", "ok")
                await config_repo.set_config_value("weather_api_last_success", str(datetime.now()))

    except Exception as e:
        logger.critical(f"CRITICAL ERROR in background task: {e}", exc_info=True)
        async with SessionLocal() as session:
            config_repo = SystemConfigRepository(session)
            await config_repo.set_config_value("weather_api_status", f"critical_error: {e}")

    logger.info("Weather forecast task finished.")
