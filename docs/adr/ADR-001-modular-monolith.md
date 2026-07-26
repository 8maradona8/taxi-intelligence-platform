# ADR-001 — Use Modular Monolith Architecture

## Status

Accepted

## Context

Taxi Intelligence Platform will contain multiple intelligence domains:
airport, transport, events, traffic, weather, demand, and dashboard.

Starting with microservices would add operational complexity too early.

## Decision

We will use a modular monolith.

Each domain will live in its own module under:

backend/app/modules/

## Consequences

Benefits:
- simple deployment
- clear domain boundaries
- easier local development
- future migration to microservices remains possible

Trade-offs:
- all modules share one runtime
- discipline is required to keep modules independent