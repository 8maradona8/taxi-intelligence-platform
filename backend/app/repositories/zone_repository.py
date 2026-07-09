from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.zone import Zone


class ZoneRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_name(self, name: str) -> Zone | None:
        result = await self.session.execute(
            select(Zone).where(Zone.name == name)
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        name: str,
        city: str,
        country: str,
        latitude: float,
        longitude: float,
    ) -> Zone:
        zone = Zone(
            name=name,
            city=city,
            country=country,
            latitude=latitude,
            longitude=longitude,
        )

        self.session.add(zone)
        await self.session.commit()
        await self.session.refresh(zone)

        return zone