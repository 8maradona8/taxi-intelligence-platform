from sqlalchemy.ext.asyncio import AsyncSession

from app.models.zone import Zone
from app.repositories.zone_repository import ZoneRepository


class ZoneService:
    def __init__(self, session: AsyncSession) -> None:
        self.zone_repository = ZoneRepository(session)

    async def get_or_create_zone(
        self,
        *,
        name: str,
        city: str,
        country: str,
        latitude: float,
        longitude: float,
    ) -> Zone:
        zone = await self.zone_repository.get_by_name(name)

        if zone is not None:
            return zone

        return await self.zone_repository.create(
            name=name,
            city=city,
            country=country,
            latitude=latitude,
            longitude=longitude,
        )
