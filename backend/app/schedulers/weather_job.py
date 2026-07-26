from app.application.scoring.weather import (
    WeatherScoreService,
)
from app.core.settings import settings
from app.database.session import AsyncSessionLocal
from app.domain.events import SignalEvent
from app.infrastructure.clients import (
    MetNorwayWeatherClient,
)
from app.infrastructure.collectors import (
    SofiaWeatherCollector,
)
from app.infrastructure.http import AsyncHttpClient
from app.infrastructure.mappers import (
    MetNorwayForecastParser,
    WeatherSignalMapper,
)
from app.repositories import (
    SignalRepository,
    ZoneRepository,
)
from app.services.weather_signal_persistence_service import (
    WeatherSignalPersistenceService,
)
from app.services.weather_signal_service import (
    WeatherSignalService,
)


async def collect_and_persist_weather_signal() -> SignalEvent:
    async with AsyncHttpClient(
        base_url="https://api.met.no",
        timeout_seconds=20.0,
        max_retries=2,
        backoff_seconds=1.0,
        default_headers={
            "Accept": "application/json",
        },
    ) as http_client:
        collector = SofiaWeatherCollector(
            client=MetNorwayWeatherClient(
                http_client=http_client,
                user_agent=settings.weather_user_agent,
            ),
            parser=MetNorwayForecastParser(),
        )

        async with AsyncSessionLocal() as session:
            persistence_service = WeatherSignalPersistenceService(
                zone_repository=ZoneRepository(session),
                signal_repository=SignalRepository(session),
            )

            service = WeatherSignalService(
                collector=collector,
                signal_mapper=WeatherSignalMapper(
                    score_service=WeatherScoreService(),
                ),
                persistence_service=persistence_service,
            )

            return await service.create_weather_signal()
