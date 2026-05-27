"""Classifier worker – minimal stub so the container starts."""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def main() -> None:
    log.info("classifier worker starting (stub – waiting for implementation)")
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
