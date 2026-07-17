from app.infrastructure.http import AsyncHttpClient


class BdzLiveBoardClient:
    """Downloads public railway arrivals from the official BDZ live board."""

    SOFIA_ARRIVALS_PATH = "/bg/sofia/arrivals"

    def __init__(
        self,
        http_client: AsyncHttpClient,
    ) -> None:
        self._http_client = http_client

    async def get_sofia_arrivals_html(self) -> str:
        return await self._http_client.get_text(
            self.SOFIA_ARRIVALS_PATH,
        )
