import pytest

from app.application.demand_fusion import (
    DemandSourceWeightRegistry,
)
from app.domain.demand_fusion import (
    DemandSourceWeight,
)
from app.domain.enums import SignalSource


def test_registry_preserves_registration_order() -> None:
    airport = DemandSourceWeight(
        source=SignalSource.AIRPORT,
        weight=3.0,
    )
    weather = DemandSourceWeight(
        source=SignalSource.WEATHER,
        weight=1.0,
    )

    registry = DemandSourceWeightRegistry(
        (
            airport,
            weather,
        )
    )

    assert registry.weights == (
        airport,
        weather,
    )
    assert registry.sources == (
        SignalSource.AIRPORT,
        SignalSource.WEATHER,
    )


def test_registry_is_immutable_when_registering() -> None:
    airport = DemandSourceWeight(
        source=SignalSource.AIRPORT,
        weight=3.0,
    )
    weather = DemandSourceWeight(
        source=SignalSource.WEATHER,
        weight=1.0,
    )

    original = DemandSourceWeightRegistry((airport,))
    updated = original.register(weather)

    assert original.sources == (SignalSource.AIRPORT,)
    assert updated.sources == (
        SignalSource.AIRPORT,
        SignalSource.WEATHER,
    )


def test_registry_requires_registered_source() -> None:
    registry = DemandSourceWeightRegistry(
        (
            DemandSourceWeight(
                source=SignalSource.AIRPORT,
                weight=3.0,
            ),
        )
    )

    with pytest.raises(
        KeyError,
        match=("Demand source weight is not registered: weather"),
    ):
        registry.require(SignalSource.WEATHER)


def test_registry_rejects_duplicate_sources() -> None:
    with pytest.raises(
        ValueError,
        match=("Demand source weights must be unique: airport"),
    ):
        DemandSourceWeightRegistry(
            (
                DemandSourceWeight(
                    source=SignalSource.AIRPORT,
                    weight=3.0,
                ),
                DemandSourceWeight(
                    source=SignalSource.AIRPORT,
                    weight=2.0,
                ),
            )
        )


def test_registry_supports_collection_protocols() -> None:
    airport = DemandSourceWeight(
        source=SignalSource.AIRPORT,
        weight=3.0,
    )
    registry = DemandSourceWeightRegistry((airport,))

    assert len(registry) == 1
    assert registry
    assert SignalSource.AIRPORT in registry
    assert SignalSource.WEATHER not in registry
    assert tuple(registry) == (airport,)
