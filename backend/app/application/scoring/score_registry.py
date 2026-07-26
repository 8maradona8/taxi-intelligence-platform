from collections.abc import Iterable, Iterator

from app.application.scoring.contributor import (
    ScoreContributor,
)


class ScoreRegistry:
    """Immutable ordered registry of score contributors."""

    def __init__(
        self,
        contributors: Iterable[ScoreContributor] = (),
    ) -> None:
        registered_contributors = tuple(contributors)

        self._validate_unique_names(registered_contributors)

        self._contributors = registered_contributors
        self._contributors_by_name = {
            contributor.name: contributor for contributor in registered_contributors
        }

    @property
    def contributors(
        self,
    ) -> tuple[ScoreContributor, ...]:
        """Return contributors in registration order."""
        return self._contributors

    @property
    def names(self) -> tuple[str, ...]:
        """Return contributor names in registration order."""
        return tuple(contributor.name for contributor in self._contributors)

    def register(
        self,
        contributor: ScoreContributor,
    ) -> "ScoreRegistry":
        """Return a new registry containing the contributor."""
        return ScoreRegistry(
            (
                *self._contributors,
                contributor,
            )
        )

    def extend(
        self,
        contributors: Iterable[ScoreContributor],
    ) -> "ScoreRegistry":
        """Return a new registry containing all contributors."""
        return ScoreRegistry(
            (
                *self._contributors,
                *tuple(contributors),
            )
        )

    def get(
        self,
        name: str,
    ) -> ScoreContributor | None:
        """Return a contributor by name, if registered."""
        return self._contributors_by_name.get(name)

    def require(
        self,
        name: str,
    ) -> ScoreContributor:
        """Return a contributor or raise KeyError."""
        try:
            return self._contributors_by_name[name]
        except KeyError as exc:
            raise KeyError(f"Score contributor is not registered: {name}") from exc

    def __contains__(
        self,
        name: object,
    ) -> bool:
        return name in self._contributors_by_name

    def __iter__(
        self,
    ) -> Iterator[ScoreContributor]:
        return iter(self._contributors)

    def __len__(self) -> int:
        return len(self._contributors)

    def __bool__(self) -> bool:
        return bool(self._contributors)

    @staticmethod
    def _validate_unique_names(
        contributors: tuple[ScoreContributor, ...],
    ) -> None:
        seen_names: set[str] = set()
        duplicate_names: set[str] = set()

        for contributor in contributors:
            if contributor.name in seen_names:
                duplicate_names.add(contributor.name)

            seen_names.add(contributor.name)

        if duplicate_names:
            duplicates = ", ".join(sorted(duplicate_names))

            raise ValueError(f"Score contributor names must be unique: {duplicates}")
