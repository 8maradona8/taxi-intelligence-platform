import asyncio

from app.infrastructure.http import (
    AsyncHttpClient,
    HttpClientError,
)


async def main() -> None:
    try:
        async with AsyncHttpClient(
            base_url="https://jsonplaceholder.typicode.com",
            timeout_seconds=15.0,
            max_retries=2,
            backoff_seconds=0.5,
        ) as client:
            data = await client.get_json("/todos/1")

            print("HTTP request successful")
            print("Response:", data)

    except HttpClientError as exc:
        print(f"HTTP client test failed: {exc}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
