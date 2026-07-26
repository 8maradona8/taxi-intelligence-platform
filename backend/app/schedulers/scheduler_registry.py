from dataclasses import dataclass, replace

from app.application.interfaces import (
    SchedulerIdentity,
    SchedulerRuntime,
)


@dataclass(frozen=True)
class SchedulerRegistration:
    identity: SchedulerIdentity
    enabled: bool
    runtime: SchedulerRuntime | None = None

    @property
    def initialized(self) -> bool:
        return self.runtime is not None

    @property
    def running(self) -> bool:
        if self.runtime is None:
            return False

        return self.runtime.status.running


class SchedulerRegistry:
    def __init__(self) -> None:
        self._registrations: dict[
            str,
            SchedulerRegistration,
        ] = {}

    def register(
        self,
        *,
        identity: SchedulerIdentity,
        enabled: bool,
        runtime: SchedulerRuntime | None = None,
    ) -> SchedulerRegistration:
        if identity.key in self._registrations:
            raise ValueError(f"scheduler key is already registered: {identity.key}")

        registration = SchedulerRegistration(
            identity=identity,
            enabled=enabled,
            runtime=runtime,
        )

        self._registrations[identity.key] = registration

        return registration

    def attach_runtime(
        self,
        *,
        scheduler_key: str,
        runtime: SchedulerRuntime,
    ) -> SchedulerRegistration:
        registration = self.get(scheduler_key)

        updated = replace(
            registration,
            runtime=runtime,
        )

        self._registrations[registration.identity.key] = updated

        return updated

    def detach_runtime(
        self,
        scheduler_key: str,
    ) -> SchedulerRegistration:
        registration = self.get(scheduler_key)

        updated = replace(
            registration,
            runtime=None,
        )

        self._registrations[registration.identity.key] = updated

        return updated

    def get(
        self,
        scheduler_key: str,
    ) -> SchedulerRegistration:
        normalized_key = scheduler_key.strip().lower()

        try:
            return self._registrations[normalized_key]
        except KeyError as exc:
            raise KeyError(f"unknown scheduler key: {normalized_key}") from exc

    def get_runtime(
        self,
        scheduler_key: str,
    ) -> SchedulerRuntime | None:
        return self.get(scheduler_key).runtime

    def list_all(
        self,
    ) -> list[SchedulerRegistration]:
        return sorted(
            self._registrations.values(),
            key=lambda registration: registration.identity.key,
        )

    def __len__(self) -> int:
        return len(self._registrations)
