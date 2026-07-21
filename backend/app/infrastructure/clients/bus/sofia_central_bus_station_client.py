from app.infrastructure.http import AsyncHttpClient


class SofiaCentralBusStationClient:
    """Downloads public arrivals from Sofia Central Bus Station."""

    ARRIVALS_PATH = "/"
    ALLOWED_HORIZON_HOURS = {
        1,
        2,
        4,
        8,
        12,
    }

    def __init__(
        self,
        http_client: AsyncHttpClient,
    ) -> None:
        self._http_client = http_client

    async def get_arrivals_html(
        self,
        *,
        hours: int = 2,
    ) -> str:
        if hours not in self.ALLOWED_HORIZON_HOURS:
            allowed_values = ", ".join(
                str(value) for value in sorted(self.ALLOWED_HORIZON_HOURS)
            )

            raise ValueError(f"hours must be one of: {allowed_values}")

        return await self._http_client.get_text(
            self.ARRIVALS_PATH,
            params={
                "mod": "06a943c59f33a34bb5924aaf72cd2995",
                "t": hours,
                "d": "c",
            },
        )
