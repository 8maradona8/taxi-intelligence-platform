from dataclasses import dataclass, field

from app.domain.events import SignalEvent
from app.domain.geography.coordinates import Coordinates


@dataclass
class Zone:
    name: str
    city: str
    country: str
    coordinates: Coordinates
    radius_meters: int = 1000
    signals: list[SignalEvent] = field(default_factory=list)

    def add_signal(self, signal: SignalEvent) -> None:
        if signal.is_expired:
            return

        self.signals.append(signal)

    def active_signals(self) -> list[SignalEvent]:
        return [signal for signal in self.signals if not signal.is_expired]

    def total_impact_score(self) -> float:
        return sum(signal.impact_score.value for signal in self.active_signals())

    def average_confidence(self) -> float:
        active_signals = self.active_signals()

        if not active_signals:
            return 0.0

        return sum(signal.confidence.value for signal in active_signals) / len(
            active_signals
        )

    def demand_score(self):
        from app.domain.decision import DemandScore

        reasons = [
            f"{signal.source.value}:{signal.signal_type.value} impact={signal.impact_score.value}"
            for signal in self.active_signals()
        ]

        return DemandScore.from_zone_metrics(
            total_impact=self.total_impact_score(),
            average_confidence=self.average_confidence(),
            reasons=reasons,
        )
