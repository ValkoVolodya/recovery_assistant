import asyncio
import logging

import uvicorn

from app.bot.runner import run_bot
from app.logging_config import configure_logging
from app.runtime import build_runtime
from app.web import create_app

logger = logging.getLogger(__name__)


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
    strava_webhook_task = asyncio.create_task(runtime.strava_service.ensure_webhook_subscription_with_retry())

    try:
        done, pending = await asyncio.wait(
            {bot_task, web_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in done:
            exc = task.exception()
            if exc is not None:
                raise exc
        if bot_task in done:
            raise RuntimeError("Telegram polling stopped unexpectedly")
        if web_task in done:
            raise RuntimeError("Web server stopped unexpectedly")
    finally:
        logger.info("Shutting down application runtime")
        server.should_exit = True
        for task in (bot_task, web_task, strava_webhook_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(bot_task, web_task, strava_webhook_task, return_exceptions=True)
        await runtime.engine.dispose()


def main() -> None:
    configure_logging()
    asyncio.run(run())
