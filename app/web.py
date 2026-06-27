import logging

from aiogram.types import Update
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from app.runtime import AppRuntime

logger = logging.getLogger(__name__)


def create_app(runtime: AppRuntime) -> FastAPI:
    app = FastAPI(title="Recovery Assistant")
    app.state.runtime = runtime

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/telegram/webhook")
    async def telegram_webhook(request: Request) -> dict[str, str]:
        payload = await request.json()
        update = Update.model_validate(payload, context={"bot": runtime.telegram.bot})
        await runtime.telegram.dispatcher.feed_update(runtime.telegram.bot, update)
        return {"status": "ok"}

    @app.get("/strava/connect")
    async def strava_connect(telegram_user_id: int = Query(..., gt=0)) -> RedirectResponse:
        try:
            connect_url = runtime.strava_service.build_connect_url(telegram_user_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return RedirectResponse(connect_url)

    @app.get("/strava/oauth/callback", response_model=None)
    async def strava_oauth_callback(
        code: str | None = None,
        scope: str | None = None,
        state: str | None = None,
        error: str | None = None,
    ) -> RedirectResponse | dict[str, str]:
        if error is not None:
            raise HTTPException(status_code=400, detail=f"Strava OAuth error: {error}")
        if code is None or state is None:
            raise HTTPException(status_code=400, detail="Missing Strava OAuth code or state")
        try:
            telegram_user_id = int(state)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid Strava OAuth state") from exc

        _ = scope
        try:
            await runtime.strava_service.connect_athlete(code=code, telegram_user_id=telegram_user_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Strava connection failed: {exc}") from exc

        bot_username = runtime.settings.bot_username
        if bot_username:
            return RedirectResponse(f"https://t.me/{bot_username}", status_code=302)
        return {"status": "connected", "message": "Strava connected. You can return to Telegram."}

    @app.get("/strava/webhook")
    async def strava_webhook_verify(
        hub_mode: str = Query(..., alias="hub.mode"),
        hub_verify_token: str = Query(..., alias="hub.verify_token"),
        hub_challenge: str = Query(..., alias="hub.challenge"),
    ) -> dict[str, str]:
        try:
            return runtime.strava_service.verify_webhook(
                mode=hub_mode,
                token=hub_verify_token,
                challenge=hub_challenge,
            )
        except ValueError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.post("/strava/webhook")
    async def strava_webhook_ingest(request: Request, background_tasks: BackgroundTasks) -> dict[str, str]:
        payload = await request.json()
        logger.info("Accepted Strava webhook payload=%s", payload)
        background_tasks.add_task(runtime.strava_service.process_webhook_event, payload)
        return {"status": "accepted"}

    return app
