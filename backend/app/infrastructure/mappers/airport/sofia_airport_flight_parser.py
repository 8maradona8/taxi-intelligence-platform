import json
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from bs4.element import Tag

from app.domain.flight import Flight
from app.domain.flight_status import FlightStatus


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


class SofiaAirportFlightParser:
    STATUS_MAP = {
        "scheduled": FlightStatus.SCHEDULED,
        "expected": FlightStatus.EXPECTED,
        "landed": FlightStatus.LANDED,
        "delayed": FlightStatus.DELAYED,
        "cancelled": FlightStatus.CANCELLED,
        "canceled": FlightStatus.CANCELLED,
        "diverted": FlightStatus.DIVERTED,
    }

    def parse_arrivals(self, html: str) -> list[Flight]:
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        flights: list[Flight] = []

        for row in soup.select("tr[data-flight]"):
            flight = self._parse_row(row)

            if flight is not None:
                flights.append(flight)

        return flights

    def _parse_row(self, row: Tag) -> Flight | None:
        raw_flight = row.get("data-flight")

        if not isinstance(raw_flight, str):
            return None

        try:
            flight_data = json.loads(raw_flight)
        except json.JSONDecodeError:
            return None

        if flight_data.get("ad") != "A":
            return None

        flight_number = self._clean(flight_data.get("f"))
        origin_city = self._clean(flight_data.get("an"))
        origin_iata = self._clean(flight_data.get("dest"))
        flight_date = self._clean(flight_data.get("d"))
        scheduled_time = self._clean(flight_data.get("t"))

        if not all(
            [
                flight_number,
                origin_city,
                flight_date,
                scheduled_time,
            ]
        ):
            return None

        scheduled_arrival = self._parse_datetime(
            flight_date,
            scheduled_time,
        )

        if scheduled_arrival is None:
            return None

        status_text = self._clean(flight_data.get("st_en")).lower()

        if not status_text:
            status = FlightStatus.SCHEDULED
        else:
            status = self.STATUS_MAP.get(
                status_text,
                FlightStatus.UNKNOWN,
            )

        operational_time = self._clean(flight_data.get("est"))

        estimated_arrival: datetime | None = None
        actual_arrival: datetime | None = None

        if operational_time:
            operational_datetime = self._parse_datetime(
                flight_date,
                operational_time,
            )

            if status == FlightStatus.LANDED:
                actual_arrival = operational_datetime
            else:
                estimated_arrival = operational_datetime

        airline = self._parse_airline(row)

        return Flight(
            flight_number=flight_number,
            origin_city=origin_city.title(),
            origin_iata=origin_iata or None,
            scheduled_arrival=scheduled_arrival,
            status=status,
            airline=airline,
            terminal=self._normalize_terminal(self._clean(flight_data.get("ter"))),
            estimated_arrival=estimated_arrival,
            actual_arrival=actual_arrival,
        )

    def _parse_airline(self, row: Tag) -> str | None:
        raw_airline = row.get("data-airline")

        if not isinstance(raw_airline, str):
            return None

        try:
            airline_data = json.loads(raw_airline)
        except json.JSONDecodeError:
            return None

        airline_name = self._clean(airline_data.get("name"))

        return airline_name or None

    @staticmethod
    def _parse_datetime(
        date_value: str,
        time_value: str,
    ) -> datetime | None:
        try:
            parsed = datetime.strptime(
                f"{date_value} {time_value}",
                "%d/%m/%Y %H:%M",
            )
        except ValueError:
            return None

        return parsed.replace(
            tzinfo=SOFIA_TIMEZONE,
        )

    @staticmethod
    def _normalize_terminal(
        terminal: str,
    ) -> str | None:
        if not terminal:
            return None

        normalized = terminal.upper()

        if normalized == "T1":
            return "Terminal 1"

        if normalized == "T2":
            return "Terminal 2"

        return terminal

    @staticmethod
    def _clean(value: object) -> str:
        if value is None:
            return ""

        return str(value).strip()
