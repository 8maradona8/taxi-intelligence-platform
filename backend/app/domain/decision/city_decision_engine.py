from app.domain.decision.decision import Decision
from app.domain.decision.decision_engine import DecisionEngine
from app.domain.geography import City


class CityDecisionEngine:
    def __init__(self) -> None:
        self.decision_engine = DecisionEngine()

    def evaluate_city(self, city: City) -> list[Decision]:
        decisions: list[Decision] = []

        for zone in city.list_zones():
            if not zone.active_signals():
                continue

            decisions.append(
                self.decision_engine.evaluate_zone(zone)
            )

        return decisions