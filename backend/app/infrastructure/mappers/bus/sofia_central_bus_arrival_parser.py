import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from bs4.element import Tag

from app.domain import BusArrival


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


class SofiaCentralBusArrivalParser:
    RESULT_TABLE_SELECTOR = (
        "#results_container table.result_table_odd, "
        "#results_container table.result_table_even"
    )

    VALID_FROM_PATTERN = re.compile(
        r"Валиден\s+от\s+(\d{4}-\d{2}-\d{2})",
        flags=re.IGNORECASE,
    )

    VALID_UNTIL_PATTERN = re.compile(
        r"Валиден\s+до\s+(\d{4}-\d{2}-\d{2})",
        flags=re.IGNORECASE,
    )

    VALIDITY_SUFFIX_PATTERN = re.compile(
        r"\s+Валиден(?:\s+от|\s+до).*$",
        flags=re.IGNORECASE,
    )

    ARRIVAL_TIME_PATTERN = re.compile(
        r"(?P<hour>\d{1,2}):(?P<minute>\d{2})",
    )

    ROLLOVER_GRACE_PERIOD = timedelta(hours=3)

    def parse_arrivals(
        self,
        html: str,
        *,
        observed_at: datetime | None = None,
    ) -> list[BusArrival]:
        observation_time = self._normalize_observed_at(observed_at)

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        arrivals: list[BusArrival] = []

        for table in soup.select(self.RESULT_TABLE_SELECTOR):
            arrival = self._parse_table(
                table,
                observed_at=observation_time,
            )

            if arrival is not None:
                arrivals.append(arrival)

        return arrivals

    def _parse_table(
        self,
        table: Tag,
        *,
        observed_at: datetime,
    ) -> BusArrival | None:
        rows = table.find_all(
            "tr",
            recursive=False,
        )

        if not rows:
            return None

        primary_cells = rows[0].find_all(
            "td",
            recursive=False,
        )

        if len(primary_cells) < 4:
            return None

        raw_route = self._clean(
            primary_cells[0].get_text(
                " ",
                strip=True,
            )
        )

        carrier = self._clean(
            primary_cells[1].get_text(
                " ",
                strip=True,
            )
        )

        operating_days_text = self._clean(
            primary_cells[2].get_text(
                " ",
                strip=True,
            )
        )

        arrival_time_text = self._clean(
            primary_cells[3].get_text(
                " ",
                strip=True,
            )
        )

        sector_text = ""

        if len(primary_cells) >= 5:
            sector_text = self._clean(
                primary_cells[4].get_text(
                    " ",
                    strip=True,
                )
            )

        route = self._extract_route(raw_route)
        full_route = self._extract_full_route(
            table,
            fallback=route,
        )
        origin = self._extract_origin(full_route)
        scheduled_arrival = self._parse_scheduled_arrival(
            arrival_time_text,
            observed_at=observed_at,
        )

        if not all(
            [
                route,
                full_route,
                origin,
                carrier,
                scheduled_arrival,
            ]
        ):
            return None

        return BusArrival(
            origin=origin,
            route=route,
            full_route=full_route,
            carrier=carrier,
            scheduled_arrival=scheduled_arrival,
            operating_days=self._parse_operating_days(operating_days_text),
            valid_from=self._extract_date(
                raw_route,
                pattern=self.VALID_FROM_PATTERN,
            ),
            valid_until=self._extract_date(
                raw_route,
                pattern=self.VALID_UNTIL_PATTERN,
            ),
            sector=self._normalize_sector(sector_text),
        )

    def _parse_scheduled_arrival(
        self,
        value: str,
        *,
        observed_at: datetime,
    ) -> datetime | None:
        match = self.ARRIVAL_TIME_PATTERN.search(value)

        if match is None:
            return None

        hour = int(match.group("hour"))
        minute = int(match.group("minute"))

        if hour > 23 or minute > 59:
            return None

        candidate = datetime.combine(
            observed_at.date(),
            time(
                hour=hour,
                minute=minute,
            ),
            tzinfo=SOFIA_TIMEZONE,
        )

        rollover_threshold = observed_at - self.ROLLOVER_GRACE_PERIOD

        if candidate < rollover_threshold:
            candidate += timedelta(days=1)

        return candidate

    @classmethod
    def _extract_route(
        cls,
        value: str,
    ) -> str:
        route = cls.VALIDITY_SUFFIX_PATTERN.sub(
            "",
            value,
        )

        return cls._clean(route)

    @classmethod
    def _extract_full_route(
        cls,
        table: Tag,
        *,
        fallback: str,
    ) -> str:
        full_route_element = table.select_one(".sr_full_route")

        if full_route_element is None:
            return fallback

        full_route = cls._clean(
            full_route_element.get_text(
                " ",
                strip=True,
            )
        )

        return full_route or fallback

    @classmethod
    def _extract_origin(
        cls,
        full_route: str,
    ) -> str:
        segments = [
            cls._clean(segment)
            for segment in full_route.split(" - ")
            if cls._clean(segment)
        ]

        if not segments:
            return ""

        return segments[0]

    @staticmethod
    def _parse_operating_days(
        value: str,
    ) -> tuple[str, ...]:
        return tuple(day.strip().lower() for day in value.split() if day.strip())

    @staticmethod
    def _normalize_sector(
        value: str,
    ) -> str | None:
        normalized = value.strip()

        if not normalized:
            return None

        normalized = re.sub(
            r"^Сектор\s*",
            "",
            normalized,
            flags=re.IGNORECASE,
        ).strip()

        return normalized or None

    @staticmethod
    def _extract_date(
        value: str,
        *,
        pattern: re.Pattern[str],
    ) -> date | None:
        match = pattern.search(value)

        if match is None:
            return None

        try:
            return date.fromisoformat(match.group(1))
        except ValueError:
            return None

    @staticmethod
    def _normalize_observed_at(
        value: datetime | None,
    ) -> datetime:
        if value is None:
            return datetime.now(SOFIA_TIMEZONE)

        if value.tzinfo is None:
            return value.replace(tzinfo=SOFIA_TIMEZONE)

        return value.astimezone(SOFIA_TIMEZONE)

    @staticmethod
    def _clean(
        value: object,
    ) -> str:
        if value is None:
            return ""

        return " ".join(str(value).split())
