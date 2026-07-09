from abc import ABC, abstractmethod
from typing import Any


class BaseCollector(ABC):
    """
    Base interface for all external data collectors.

    Every intelligence module must implement:
    - collect()
    - process()
    - save()
    """

    @abstractmethod
    async def collect(self) -> Any:
        """
        Fetch raw data from external source.
        """

    @abstractmethod
    async def process(self, data: Any) -> Any:
        """
        Transform raw data into domain objects.
        """

    @abstractmethod
    async def save(self, data: Any) -> Any:
        """
        Persist processed data.
        """

    async def run(self) -> Any:
        """
        Standard collector execution pipeline.
        """

        raw_data = await self.collect()
        processed_data = await self.process(raw_data)

        return await self.save(processed_data)