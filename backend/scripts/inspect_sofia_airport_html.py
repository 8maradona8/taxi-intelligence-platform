import asyncio
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup

from app.infrastructure.clients import SofiaAirportWebsiteClient
from app.infrastructure.http import AsyncHttpClient


FIXTURE_PATH = Path(
    "tests/fixtures/airport/sofia_airport_arrivals.html"
)


async def main() -> None:
    async with AsyncHttpClient(
        base_url="https://sofia-airport.eu",
        timeout_seconds=20.0,
        max_retries=2,
        backoff_seconds=1.0,
        default_headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": (
                "Taxi-Intelligence-Platform/0.1.0 "
                "(development; public flight data reader)"
            ),
        },
    ) as http_client:
        airport_client = SofiaAirportWebsiteClient(
            http_client=http_client,
        )

        html = await airport_client.get_arrivals_html()

    FIXTURE_PATH.write_text(
        html,
        encoding="utf-8",
    )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    class_counter: Counter[str] = Counter()

    for element in soup.find_all(True):
        for class_name in element.get("class", []):
            class_counter[class_name] += 1

    print("Fixture saved:", FIXTURE_PATH)
    print("HTML length:", len(html))
    print()
    print("Most common CSS classes:")

    for class_name, count in class_counter.most_common(40):
        print(f"{count:>4}  {class_name}")

    print()
    print("Elements containing flight-like text:")

    keywords = (
        "terminal",
        "landed",
        "expected",
        "scheduled",
        "cancelled",
        "delayed",
    )

    matches = []

    for element in soup.find_all(
        ["article", "div", "li", "tr"],
    ):
        text = " ".join(
            element.get_text(
                " ",
                strip=True,
            ).split()
        )

        lowered_text = text.lower()

        if any(
            keyword in lowered_text
            for keyword in keywords
        ):
            if 20 <= len(text) <= 500:
                matches.append(element)

    for index, element in enumerate(
        matches[:10],
        start=1,
    ):
        print()
        print(f"--- Candidate {index} ---")
        print("Tag:", element.name)
        print("Classes:", element.get("class"))
        print(
            "Text:",
            " ".join(
                element.get_text(
                    " ",
                    strip=True,
                ).split()
            )[:500],
        )
        print("HTML:")
        print(str(element)[:1200])


if __name__ == "__main__":
    asyncio.run(main())