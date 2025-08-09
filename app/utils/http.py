from contextlib import asynccontextmanager
import aiohttp
from typing import AsyncIterator


@asynccontextmanager
async def aiohttp_session() -> AsyncIterator[aiohttp.ClientSession]:
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        yield session