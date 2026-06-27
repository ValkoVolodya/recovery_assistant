import asyncio
import logging

import uvicorn

from app.bot.runner import close_bot, ensure_telegram_webhook_with_retry
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

    web_task = asyncio.create_task(server.serve())
    telegram_webhook_task = asyncio.create_task(ensure_telegram_webhook_with_retry(runtime.telegram, runtime))
    strava_webhook_task = asyncio.create_task(runtime.strava_service.ensure_webhook_subscription_with_retry())

    try:
        await web_task
        if not server.should_exit:
            raise RuntimeError("Web server stopped unexpectedly")
    finally:
        logger.info("Shutting down application runtime")
        server.should_exit = True
        for task in (web_task, telegram_webhook_task, strava_webhook_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(web_task, telegram_webhook_task, strava_webhook_task, return_exceptions=True)
        await close_bot(runtime.telegram)
        await runtime.engine.dispose()


def main() -> None:
    configure_logging()
    asyncio.run(run())
