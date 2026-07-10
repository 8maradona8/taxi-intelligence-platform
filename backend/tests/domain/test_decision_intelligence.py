import pytest

from app.domain.decision import (
    CityDecisionEngine,
    DemandLevel,
    OpportunityEngine,
    RecommendationEngine,
)
from app.domain.geography import City
from app.domain.pipelines import SignalPipeline
from app.domain.events import SignalEvent


def test_pipeline_calculates_demand_for_multiple_zones(
    sofia_city: City,
    city_signals: list[SignalEvent],
) -> None:
    processed_zones = SignalPipeline().process_city(
        city=sofia_city,
        signals=city_signals,
    )

    assert len(processed_zones) == 2

    airport = sofia_city.get_zone("Sofia Airport")
    ndk = sofia_city.get_zone("NDK")

    assert airport is not None
    assert ndk is not None

    assert airport.total_impact_score() == 120.0
    assert airport.average_confidence() == pytest.approx(0.925)
    assert airport.demand_score().level == DemandLevel.VERY_HIGH

    assert ndk.total_impact_score() == 95.0
    assert ndk.average_confidence() == pytest.approx(0.88)
    assert ndk.demand_score().level == DemandLevel.HIGH


def test_opportunity_engine_ranks_airport_first(
    sofia_city: City,
    city_signals: list[SignalEvent],
) -> None:
    SignalPipeline().process_city(
        city=sofia_city,
        signals=city_signals,
    )

    decisions = CityDecisionEngine().evaluate_city(sofia_city)
    opportunities = OpportunityEngine().rank(decisions)

    assert len(opportunities) == 2

    assert opportunities[0].zone_name == "Sofia Airport"
    assert opportunities[0].score == 148.5

    assert opportunities[1].zone_name == "NDK"
    assert opportunities[1].score == 117.6


def test_recommendation_engine_selects_best_opportunity(
    sofia_city: City,
    city_signals: list[SignalEvent],
) -> None:
    SignalPipeline().process_city(
        city=sofia_city,
        signals=city_signals,
    )

    decisions = CityDecisionEngine().evaluate_city(sofia_city)
    opportunities = OpportunityEngine().rank(decisions)

    recommendation = RecommendationEngine().recommend_best(opportunities)

    assert recommendation is not None
    assert recommendation.zone_name == "Sofia Airport"
    assert recommendation.summary == "MOVE to Sofia Airport"
    assert recommendation.confidence_percent == 92
    assert recommendation.reason_count == 2
