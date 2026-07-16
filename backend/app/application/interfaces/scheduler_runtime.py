from typing import Protocol


class SchedulerRuntimeStatus(Protocol):
    name: str
    running: bool


class SchedulerRuntime(Protocol):
    @property
    def status(self) -> SchedulerRuntimeStatus: ...
