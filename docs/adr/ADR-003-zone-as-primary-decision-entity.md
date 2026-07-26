# ADR-003 — Zone as the Primary Decision Entity

## Status

Accepted

## Context

TIP receives signals from multiple intelligence modules:
airport, weather, traffic, events, and transport.

The driver does not make decisions based on raw signals. The driver makes decisions based on zones.

## Decision

Zone is the primary decision entity in TIP.

Signals are inputs.

Zone is the context.

Decision is the output.

## Consequences

Benefits:
- DecisionEngine evaluates zone state instead of raw source data
- signals from different modules can be combined naturally
- future dashboard can display city state by zone
- recommendations become easier to explain

Trade-offs:
- zone modeling must be carefully maintained
- signal-to-zone mapping becomes a critical part of the platform