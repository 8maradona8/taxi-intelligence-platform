# Sprint 1.1 — Database and First Vertical Slice

## Goal

Create the first working data pipeline from collector to PostgreSQL.

## Completed

- PostgreSQL and Redis infrastructure
- Alembic setup
- Zone model
- Signal model
- ZoneRepository
- SignalRepository
- ZoneService
- SignalService
- AirportService
- AirportCollector connected to PostgreSQL

## Demonstration

AirportCollector creates a real airport activity signal in PostgreSQL.

## Result

First working vertical slice:

AirportCollector -> AirportService -> Repositories -> PostgreSQL

## Lessons Learned

- Async SQLAlchemy requires asyncpg URL format
- Alembic async setup requires greenlet
- Early health checks helped detect configuration issues quickly