import asyncio

import uvicorn

from app.bot.runner import run_bot
from app.runtime import build_runtime
from app.web import create_app


async def run() -> None:
    runtime = build_runtime()
    app = create_app(runtime)
    config = uvicorn.Config(
        app,
        host=runtime.settings.app_host,
        port=runtime.settings.app_port,
        log_level="info",
    )
    server = uvicorn.Server(config)

    bot_task = asyncio.create_task(run_bot(runtime))
    web_task = asyncio.create_task(server.serve())

    try:
        done, pending = await asyncio.wait(
            {bot_task, web_task},
            return_when=asyncio.FIRST_EXCEPTION,
        )
        for task in done:
            exc = task.exception()
            if exc is not None:
                raise exc
    finally:
        server.should_exit = True
        for task in (bot_task, web_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(bot_task, web_task, return_exceptions=True)
        await runtime.engine.dispose()


def main() -> None:
    asyncio.run(run())
