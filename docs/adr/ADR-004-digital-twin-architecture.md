# ADR-004 — Digital Twin Architecture

## Status

Accepted

## Context

TIP collects data from many external sources: airports, weather, traffic, events, and transport.

If each source directly drives decisions, the system becomes tightly coupled and difficult to scale.

## Decision

TIP will use a Digital Twin architecture.

The platform will maintain an internal model of the city:

Region -> City -> Zone -> Signals -> Demand -> Decisions -> Recommendations

External collectors update this internal model.

Decision engines operate only on the internal model, not directly on external APIs.

## Consequences

Benefits:

- better separation between data collection and decision-making
- easier support for multiple cities
- easier testing of decision logic
- future support for simulation and forecasting
- future support for ML models

Trade-offs:

- requires more careful domain modeling
- requires a clear signal-to-zone mapping strategy
- adds an abstraction layer before visible product features