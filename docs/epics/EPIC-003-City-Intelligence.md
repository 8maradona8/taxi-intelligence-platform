# EPIC-003 — City Intelligence

## Goal

Build the domain foundation that allows TIP to understand a city as a living intelligence model made of regions, cities, zones, signals, demand scores, decisions, and recommendations.

## Product Objective

Move from single-zone intelligence to full city-level intelligence.

## Core Concept

TIP will model the city as a digital twin.

External sources do not directly drive decisions. They update the internal city model.

## Main Domain Objects

- Region
- City
- Zone
- SignalEvent
- DemandScore
- Decision
- Recommendation

## Planned Tasks

### TIP-301 — Region Domain Model

Create Region as a container for multiple cities.

### TIP-302 — City Domain Model

Create City as a container for zones.

### TIP-303 — Zone Registry

Allow cities to register, find, and list zones.

### TIP-304 — Multi-Zone Signal Pipeline

Process signals across multiple zones.

### TIP-305 — City Decision Engine

Evaluate all zones in a city.

### TIP-306 — Ranking Engine

Rank zones by opportunity.

## Definition of Done

EPIC-003 is done when TIP can:

- model a city with multiple zones
- process signals across zones
- calculate demand per zone
- generate decisions per zone
- rank zones by opportunity