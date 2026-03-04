"""
Synthetic event producer.

Periodically sends POST /tasks requests to the API to simulate real traffic.
Useful for load-testing and smoke-testing the full pipeline.
"""

import asyncio
import logging
import os

import httpx

logging.basicConfig(
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "http://api:8000")
INTERVAL = float(os.getenv("PRODUCER_INTERVAL", "5"))  # seconds between events
MAX_EVENTS = int(os.getenv("MAX_EVENTS", "0"))          # 0 = infinite


async def send_event(client: httpx.AsyncClient, event_num: int) -> None:
    try:
        response = await client.post(f"{API_URL}/tasks", timeout=10.0)
        data = response.json()
        logger.info("Event #%d sent — task_id=%s status=%s", event_num, data.get("id"), data.get("status"))
    except Exception as exc:
        logger.error("Event #%d failed: %s", event_num, exc)


async def main() -> None:
    logger.info("Producer starting — API=%s interval=%ss", API_URL, INTERVAL)

    # Wait for API to be ready
    async with httpx.AsyncClient() as client:
        for attempt in range(1, 13):
            try:
                r = await client.get(f"{API_URL}/tasks", timeout=5.0)
                if r.status_code < 500:
                    break
            except Exception:
                pass
            logger.info("Waiting for API (attempt %d/12)…", attempt)
            await asyncio.sleep(5)

    count = 0
    async with httpx.AsyncClient() as client:
        while True:
            count += 1
            await send_event(client, count)
            if MAX_EVENTS and count >= MAX_EVENTS:
                logger.info("Reached MAX_EVENTS=%d — stopping producer", MAX_EVENTS)
                break
            await asyncio.sleep(INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
