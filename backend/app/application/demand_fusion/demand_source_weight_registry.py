from collections.abc import Iterable, Iterator

from app.domain.demand_fusion import DemandSourceWeight
from app.domain.enums import SignalSource


class DemandSourceWeightRegistry:
    """Immutable ordered registry of demand source weights."""

    def __init__(
        self,
        weights: Iterable[DemandSourceWeight] = (),
    ) -> None:
        registered_weights = tuple(weights)

        self._validate_unique_sources(registered_weights)

        self._weights = registered_weights
        self._weights_by_source = {
            source_weight.source: source_weight for source_weight in registered_weights
        }

    @property
    def weights(
        self,
    ) -> tuple[DemandSourceWeight, ...]:
        """Return source weights in registration order."""
        return self._weights

    @property
    def sources(
        self,
    ) -> tuple[SignalSource, ...]:
        """Return registered sources in registration order."""
        return tuple(source_weight.source for source_weight in self._weights)

    def register(
        self,
        source_weight: DemandSourceWeight,
    ) -> "DemandSourceWeightRegistry":
        """Return a new registry containing one source weight."""
        return DemandSourceWeightRegistry(
            (
                *self._weights,
                source_weight,
            )
        )

    def extend(
        self,
        weights: Iterable[DemandSourceWeight],
    ) -> "DemandSourceWeightRegistry":
        """Return a new registry containing all source weights."""
        return DemandSourceWeightRegistry(
            (
                *self._weights,
                *tuple(weights),
            )
        )

    def get(
        self,
        source: SignalSource,
    ) -> DemandSourceWeight | None:
        """Return the configured weight for a source."""
        return self._weights_by_source.get(source)

    def require(
        self,
        source: SignalSource,
    ) -> DemandSourceWeight:
        """Return a source weight or raise KeyError."""
        try:
            return self._weights_by_source[source]
        except KeyError as exc:
            raise KeyError(
                f"Demand source weight is not registered: {source.value}"
            ) from exc

    def __contains__(
        self,
        source: object,
    ) -> bool:
        return source in self._weights_by_source

    def __iter__(
        self,
    ) -> Iterator[DemandSourceWeight]:
        return iter(self._weights)

    def __len__(self) -> int:
        return len(self._weights)

    def __bool__(self) -> bool:
        return bool(self._weights)

    @staticmethod
    def _validate_unique_sources(
        weights: tuple[DemandSourceWeight, ...],
    ) -> None:
        seen_sources: set[SignalSource] = set()
        duplicate_sources: set[SignalSource] = set()

        for source_weight in weights:
            if source_weight.source in seen_sources:
                duplicate_sources.add(source_weight.source)

            seen_sources.add(source_weight.source)

        if duplicate_sources:
            duplicates = ", ".join(sorted(source.value for source in duplicate_sources))

            raise ValueError(f"Demand source weights must be unique: {duplicates}")
