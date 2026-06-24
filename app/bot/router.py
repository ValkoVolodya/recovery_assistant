from aiogram import Router

from app.bot.handlers import profile_router, start_router, strava_router, workout_router


def build_router() -> Router:
    router = Router()
    router.include_router(start_router)
    router.include_router(profile_router)
    router.include_router(strava_router)
    router.include_router(workout_router)
    return router
