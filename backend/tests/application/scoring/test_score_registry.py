from app.application.scoring import ScoreRegistry
from app.domain.scoring import (
    ScoreContext,
    ScoreContribution,
    ScoreReason,
)


class StaticContributor:
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def evaluate(
        self,
        context: ScoreContext,
    ) -> ScoreContribution:
        del context

        return ScoreContribution(
            contributor=self.name,
            score=50.0,
            weight=1.0,
            confidence=1.0,
            reason=ScoreReason(
                code=f"{self.name}_reason",
                description=(f"{self.name} scoring contribution"),
                contribution=50.0,
            ),
        )


def test_registry_is_empty_by_default() -> None:
    registry = ScoreRegistry()

    assert registry.contributors == ()
    assert registry.names == ()
    assert len(registry) == 0
    assert not registry


def test_registry_preserves_registration_order() -> None:
    weather = StaticContributor("weather")
    airport = StaticContributor("airport")

    registry = ScoreRegistry(
        (
            weather,
            airport,
        )
    )

    assert registry.contributors == (
        weather,
        airport,
    )
    assert registry.names == (
        "weather",
        "airport",
    )
    assert tuple(registry) == (
        weather,
        airport,
    )


def test_register_returns_new_registry() -> None:
    original = ScoreRegistry()
    weather = StaticContributor("weather")

    updated = original.register(weather)

    assert original.contributors == ()
    assert updated.contributors == (weather,)
    assert updated is not original


def test_extend_returns_new_registry() -> None:
    weather = StaticContributor("weather")
    airport = StaticContributor("airport")
    traffic = StaticContributor("traffic")

    original = ScoreRegistry((weather,))

    updated = original.extend(
        (
            airport,
            traffic,
        )
    )

    assert original.names == ("weather",)
    assert updated.names == (
        "weather",
        "airport",
        "traffic",
    )


def test_registry_gets_contributor_by_name() -> None:
    weather = StaticContributor("weather")
    registry = ScoreRegistry((weather,))

    assert registry.get("weather") is weather
    assert registry.get("airport") is None


def test_registry_requires_existing_contributor() -> None:
    weather = StaticContributor("weather")
    registry = ScoreRegistry((weather,))

    assert registry.require("weather") is weather


def test_registry_require_rejects_unknown_name() -> None:
    registry = ScoreRegistry()

    try:
        registry.require("weather")
    except KeyError as exc:
        assert exc.args == ("Score contributor is not registered: weather",)
    else:
        raise AssertionError("Expected registry.require() to raise KeyError")


def test_registry_supports_name_membership() -> None:
    registry = ScoreRegistry((StaticContributor("weather"),))

    assert "weather" in registry
    assert "airport" not in registry


def test_registry_rejects_duplicate_names() -> None:
    first = StaticContributor("weather")
    second = StaticContributor("weather")

    try:
        ScoreRegistry(
            (
                first,
                second,
            )
        )
    except ValueError as exc:
        assert str(exc) == ("Score contributor names must be unique: weather")
    else:
        raise AssertionError("Expected duplicate contributor rejection")


def test_extend_rejects_duplicate_existing_name() -> None:
    registry = ScoreRegistry((StaticContributor("weather"),))

    try:
        registry.extend(
            (
                StaticContributor("airport"),
                StaticContributor("weather"),
            )
        )
    except ValueError as exc:
        assert str(exc) == ("Score contributor names must be unique: weather")
    else:
        raise AssertionError("Expected duplicate contributor rejection")
