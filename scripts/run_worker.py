import asyncio
from app.main import run_pipeline


async def main():
    await run_pipeline(limit=50, dry_run=False)


if __name__ == "__main__":
    asyncio.run(main())