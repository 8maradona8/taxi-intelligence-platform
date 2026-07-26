import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from bs4.element import Tag

from app.domain import TrainArrival, TrainStatus


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")

TIME_PATTERN = re.compile(r"\b([01]\d|2[0-3]):[0-5]\d\b")
TRAIN_LABEL_PATTERN = re.compile(r"^(?P<type_code>[^\d]+?)\s*(?P<number>\d+)$")


class SofiaRailwayArrivalParser:
    def parse_arrivals(
        self,
        html: str,
        *,
        service_date: date,
    ) -> list[TrainArrival]:
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        arrivals: list[TrainArrival] = []

        for item in soup.select(".timetableItem"):
            arrival = self._parse_item(
                item,
                service_date=service_date,
            )

            if arrival is not None:
                arrivals.append(arrival)

        return arrivals

    def _parse_item(
        self,
        item: Tag,
        *,
        service_date: date,
    ) -> TrainArrival | None:
        train_number = self._clean(item.get("data-train"))

        delay_minutes = self._parse_delay(item.get("data-delay"))

        if not train_number or delay_minutes is None:
            return None

        row = item.select_one(":scope > .row")

        if row is None:
            return None

        columns = row.find_all(
            "div",
            recursive=False,
        )

        if len(columns) < 2:
            return None

        time_column = columns[0]
        details_column = columns[1]

        times = TIME_PATTERN.findall(
            time_column.get_text(
                " ",
                strip=True,
            )
        )

        time_values = [
            match.group(0) if hasattr(match, "group") else match for match in times
        ]

        # re.findall() returns only the captured hour because
        # TIME_PATTERN contains a capturing group. Extract the
        # complete values directly instead.
        time_values = [
            match.group(0)
            for match in TIME_PATTERN.finditer(
                time_column.get_text(
                    " ",
                    strip=True,
                )
            )
        ]

        if not time_values:
            return None

        scheduled_arrival = self._parse_datetime(
            service_date=service_date,
            time_value=time_values[0],
        )

        if scheduled_arrival is None:
            return None

        expected_arrival: datetime | None = None

        if len(time_values) >= 2:
            expected_arrival = self._parse_datetime(
                service_date=service_date,
                time_value=time_values[1],
            )

            if expected_arrival is not None and expected_arrival < scheduled_arrival:
                expected_arrival += timedelta(days=1)

        origin_element = details_column.select_one("p strong")

        train_element = details_column.select_one("span[data-toggle='tooltip']")

        if origin_element is None or train_element is None:
            return None

        origin_station = origin_element.get_text(
            " ",
            strip=True,
        )

        train_label = train_element.get_text(
            " ",
            strip=True,
        ).replace("\xa0", " ")

        train_type_name = self._clean(train_element.get("title"))

        train_match = TRAIN_LABEL_PATTERN.match(train_label)

        if train_match is None:
            return None

        train_type_code = train_match.group("type_code").strip()

        visible_train_number = train_match.group("number").strip()

        if visible_train_number != train_number:
            return None

        platform = self._parse_platform(details_column)

        status = self._status_from_delay(delay_minutes)

        return TrainArrival(
            train_number=train_number,
            train_type_code=train_type_code,
            train_type_name=(train_type_name or train_type_code),
            origin_station=origin_station,
            scheduled_arrival=scheduled_arrival,
            expected_arrival=expected_arrival,
            delay_minutes=delay_minutes,
            platform=platform,
            status=status,
        )

    @staticmethod
    def _parse_delay(
        value: object,
    ) -> int | None:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _status_from_delay(
        delay_minutes: int,
    ) -> TrainStatus:
        if delay_minutes > 0:
            return TrainStatus.DELAYED

        if delay_minutes < 0:
            return TrainStatus.EARLY

        return TrainStatus.SCHEDULED

    @staticmethod
    def _parse_datetime(
        *,
        service_date: date,
        time_value: str,
    ) -> datetime | None:
        try:
            parsed_time = datetime.strptime(
                time_value,
                "%H:%M",
            ).time()
        except ValueError:
            return None

        return datetime.combine(
            service_date,
            parsed_time,
            tzinfo=SOFIA_TIMEZONE,
        )

    @staticmethod
    def _parse_platform(
        details_column: Tag,
    ) -> str | None:
        platform_element = details_column.select_one("[data-station-id]")

        if platform_element is None:
            return None

        platform = platform_element.get_text(
            " ",
            strip=True,
        )

        return platform or None

    @staticmethod
    def _clean(
        value: object,
    ) -> str:
        if value is None:
            return ""

        return str(value).strip()
