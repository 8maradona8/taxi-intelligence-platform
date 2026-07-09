# Engineering Standards

## Branches

- main: stable version
- develop: active development
- feature/*: future feature branches

## Commit Style

Use task-prefixed conventional commits:

TIP-105 feat(service): add airport signal service layer

## Architecture Rules

- Collectors collect data.
- Services contain business logic.
- Repositories handle database access.
- Models define persistence structure.
- Demand Engine consumes signals, not raw source data.

## Definition of Done

A task is done when:

- code works locally
- relevant test or runner passes
- commit is created
- documentation is updated when needed
- architecture remains clean