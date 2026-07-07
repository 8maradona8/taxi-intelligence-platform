from abc import ABC, abstractmethod


class BaseCollector(ABC):
    """
    Base interface for all external data collectors.

    Every intelligence module must implement:
    - collect()
    - process()
    - save()
    """

    @abstractmethod
    async def collect(self):
        """
        Fetch raw data from external source.
        """
        pass

    @abstractmethod
    async def process(self, data):
        """
        Transform raw data into domain objects.
        """
        pass

    @abstractmethod
    async def save(self, data):
        """
        Persist processed data.
        """
        pass

    async def run(self):
        """
        Standard collector pipeline.
        """

        raw_data = await self.collect()

        processed_data = await self.process(
            raw_data
        )

        await self.save(
            processed_data
        )