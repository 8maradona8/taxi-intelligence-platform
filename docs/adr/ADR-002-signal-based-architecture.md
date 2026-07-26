# ADR-002 — Use Signals as the Core Domain Concept

## Status

Accepted

## Context

TIP collects data from many sources:
flights, weather, traffic, events, trains, buses, and future sources.

Each source has different structure, but all of them influence taxi demand.

## Decision

All intelligence modules will generate unified signals.

A signal represents:

- source
- type
- zone
- impact score
- timestamp
- payload

## Consequences

Benefits:
- Demand Engine does not need to understand every source
- new modules can be added more easily
- scoring logic becomes centralized

Trade-offs:
- signal design must be carefully maintained
- raw source data may still need separate storage later