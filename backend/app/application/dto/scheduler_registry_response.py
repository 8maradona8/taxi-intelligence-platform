from dataclasses import dataclass

from app.schedulers import SchedulerRegistration


@dataclass(frozen=True)
class SchedulerRegistryItemResponse:
    key: str
    name: str
    enabled: bool
    initialized: bool
    running: bool

    @classmethod
    def from_registration(
        cls,
        registration: SchedulerRegistration,
    ) -> "SchedulerRegistryItemResponse":
        return cls(
            key=registration.identity.key,
            name=registration.identity.name,
            enabled=registration.enabled,
            initialized=registration.initialized,
            running=registration.running,
        )


@dataclass(frozen=True)
class SchedulerRegistryResponse:
    count: int
    schedulers: list[SchedulerRegistryItemResponse]

    @classmethod
    def from_registrations(
        cls,
        registrations: list[SchedulerRegistration],
    ) -> "SchedulerRegistryResponse":
        items = [
            SchedulerRegistryItemResponse.from_registration(registration)
            for registration in registrations
        ]

        return cls(
            count=len(items),
            schedulers=items,
        )
