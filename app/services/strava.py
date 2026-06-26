from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging
from urllib.parse import urlencode

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.domain.enums import Intensity
from app.dto.workout import WorkoutInput
from app.repositories.strava_connections import StravaConnectionRepository
from app.repositories.users import UserRepository
from app.repositories.workouts import WorkoutRepository
from app.services.app_services import WorkoutService

STRAVA_OAUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"
ACCESS_TOKEN_REFRESH_BUFFER = timedelta(minutes=5)

logger = logging.getLogger(__name__)


@dataclass
class StravaWebhookEvent:
    aspect_type: str
    event_time: int
    object_id: int
    object_type: str
    owner_id: int
    subscription_id: int
    updates: dict[str, str] | None = None


class StravaClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def is_configured(self) -> bool:
        return all(
            [
                self._settings.app_base_url,
                self._settings.strava_client_id,
                self._settings.strava_client_secret,
                self._settings.strava_redirect_uri,
                self._settings.strava_verify_token,
            ]
        )

    def build_connect_url(self, telegram_user_id: int) -> str:
        self._assert_configured()
        query = urlencode(
            {
                "client_id": self._settings.strava_client_id,
                "redirect_uri": self._settings.strava_redirect_uri,
                "response_type": "code",
                "approval_prompt": "force",
                "scope": "activity:read,activity:read_all",
                "state": str(telegram_user_id),
            }
        )
        return f"{STRAVA_OAUTH_URL}?{query}"

    async def exchange_code(self, code: str) -> dict:
        self._assert_configured()
        payload = {
            "client_id": self._settings.strava_client_id,
            "client_secret": self._settings.strava_client_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(STRAVA_TOKEN_URL, data=payload)
            response.raise_for_status()
            return response.json()

    async def refresh_access_token(self, refresh_token: str) -> dict:
        self._assert_configured()
        payload = {
            "client_id": self._settings.strava_client_id,
            "client_secret": self._settings.strava_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(STRAVA_TOKEN_URL, data=payload)
            response.raise_for_status()
            return response.json()

    async def get_activity(self, access_token: str, activity_id: int) -> dict:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{STRAVA_API_BASE_URL}/activities/{activity_id}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    def _assert_configured(self) -> None:
        if not self.is_configured():
            raise RuntimeError("Strava configuration is incomplete")


class StravaService:
    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession],
        workout_service: WorkoutService,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._workout_service = workout_service
        self._client = StravaClient(settings)

    def is_configured(self) -> bool:
        return self._client.is_configured()

    def build_connect_url(self, telegram_user_id: int) -> str:
        return self._client.build_connect_url(telegram_user_id)

    async def connect_athlete(self, code: str, telegram_user_id: int) -> None:
        logger.info("Exchanging Strava OAuth code for telegram_user_id=%s", telegram_user_id)
        token_payload = await self._client.exchange_code(code)
        athlete = token_payload.get("athlete") or {}
        athlete_id = athlete.get("id")
        if athlete_id is None:
            raise RuntimeError("Strava token exchange did not return athlete id")

        expires_at = datetime.fromtimestamp(token_payload["expires_at"], tz=UTC)

        async with self._session_factory() as session:
            user_repo = UserRepository(session)
            connection_repo = StravaConnectionRepository(session)
            user = await user_repo.get_by_telegram_user_id(telegram_user_id)
            if user is None:
                raise LookupError("Telegram user not found for Strava connection")

            await connection_repo.upsert_connection(
                user_id=user.id,
                athlete_id=int(athlete_id),
                access_token=token_payload["access_token"],
                refresh_token=token_payload["refresh_token"],
                expires_at=expires_at,
            )
            await session.commit()
            logger.info(
                "Stored Strava connection for telegram_user_id=%s athlete_id=%s expires_at=%s",
                telegram_user_id,
                athlete_id,
                expires_at.isoformat(),
            )

    async def process_webhook_event(self, payload: dict) -> None:
        try:
            event = self._parse_event(payload)
            logger.info(
                "Received Strava webhook object_type=%s aspect_type=%s owner_id=%s object_id=%s",
                event.object_type,
                event.aspect_type,
                event.owner_id,
                event.object_id,
            )
            if event.object_type != "activity" or event.aspect_type != "create":
                logger.info("Ignoring unsupported Strava webhook event payload=%s", payload)
                return

            async with self._session_factory() as session:
                connection_repo = StravaConnectionRepository(session)
                workout_repo = WorkoutRepository(session)
                user_repo = UserRepository(session)

                existing_workout = await workout_repo.get_by_provider_activity_id(event.object_id)
                if existing_workout is not None:
                    logger.info("Skipping duplicate Strava activity object_id=%s", event.object_id)
                    return

                connection = await connection_repo.get_by_athlete_id(event.owner_id)
                if connection is None:
                    logger.warning("No Strava connection found for athlete_id=%s", event.owner_id)
                    return

                access_token, connection = await self._ensure_fresh_access_token(connection_repo, connection, session)
                try:
                    activity = await self._client.get_activity(access_token, event.object_id)
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code not in {401, 403}:
                        raise
                    logger.warning(
                        "Strava activity fetch unauthorized for athlete_id=%s object_id=%s, forcing token refresh",
                        event.owner_id,
                        event.object_id,
                    )
                    access_token, connection = await self._refresh_connection_tokens(
                        connection_repo,
                        connection,
                        session,
                    )
                    activity = await self._client.get_activity(access_token, event.object_id)

                user = await user_repo.get_by_id(connection.user_id)
                if user is None:
                    logger.warning("User not found for Strava connection user_id=%s", connection.user_id)
                    return

                workout_input = self._map_activity_to_workout(activity)
                await self._workout_service.log_workout(
                    telegram_user_id=user.telegram_user_id,
                    username=user.username,
                    first_name=user.first_name,
                    workout_input=workout_input,
                    provider_activity_id=event.object_id,
                )
                logger.info(
                    "Stored workout from Strava athlete_id=%s object_id=%s telegram_user_id=%s",
                    event.owner_id,
                    event.object_id,
                    user.telegram_user_id,
                )
        except Exception:
            logger.exception("Failed to process Strava webhook payload=%s", payload)
            raise

    def verify_webhook(self, mode: str, token: str, challenge: str) -> dict[str, str]:
        expected_token = self._settings.strava_verify_token
        if mode != "subscribe" or expected_token is None or token != expected_token:
            raise ValueError("Invalid Strava webhook verification request")
        return {"hub.challenge": challenge}

    async def _ensure_fresh_access_token(
        self,
        connection_repo: StravaConnectionRepository,
        connection,
        session: AsyncSession,
    ) -> tuple[str, object]:
        refresh_deadline = datetime.now(tz=UTC) + ACCESS_TOKEN_REFRESH_BUFFER
        if connection.expires_at <= refresh_deadline:
            logger.info(
                "Refreshing Strava access token for athlete_id=%s expires_at=%s",
                connection.strava_athlete_id,
                connection.expires_at.isoformat(),
            )
            return await self._refresh_connection_tokens(connection_repo, connection, session)
        return connection.access_token, connection

    async def _refresh_connection_tokens(
        self,
        connection_repo: StravaConnectionRepository,
        connection,
        session: AsyncSession,
    ) -> tuple[str, object]:
        token_payload = await self._client.refresh_access_token(connection.refresh_token)
        connection = await connection_repo.upsert_connection(
            user_id=connection.user_id,
            athlete_id=connection.strava_athlete_id,
            access_token=token_payload["access_token"],
            refresh_token=token_payload["refresh_token"],
            expires_at=datetime.fromtimestamp(token_payload["expires_at"], tz=UTC),
        )
        await session.commit()
        logger.info(
            "Refreshed Strava token for athlete_id=%s new_expires_at=%s",
            connection.strava_athlete_id,
            connection.expires_at.isoformat(),
        )
        return connection.access_token, connection

    def _map_activity_to_workout(self, activity: dict) -> WorkoutInput:
        moving_time_seconds = int(activity.get("moving_time") or 0)
        duration_minutes = max(1, round(moving_time_seconds / 60))
        kilojoules = max(1, round(float(activity.get("kilojoules") or 0)))
        intensity = self._map_intensity(activity, duration_minutes, kilojoules)
        return WorkoutInput(
            duration_minutes=duration_minutes,
            kilojoules=kilojoules,
            intensity=intensity,
        )

    def _map_intensity(self, activity: dict, duration_minutes: int, kilojoules: int) -> Intensity:
        average_watts = activity.get("average_watts")
        if average_watts is not None:
            watts = float(average_watts)
            if watts < 160:
                return Intensity.EASY
            if watts < 230:
                return Intensity.MODERATE
            return Intensity.HARD

        load_per_minute = kilojoules / max(duration_minutes, 1)
        if load_per_minute < 8:
            return Intensity.EASY
        if load_per_minute < 12:
            return Intensity.MODERATE
        return Intensity.HARD

    def _parse_event(self, payload: dict) -> StravaWebhookEvent:
        return StravaWebhookEvent(
            aspect_type=str(payload["aspect_type"]),
            event_time=int(payload["event_time"]),
            object_id=int(payload["object_id"]),
            object_type=str(payload["object_type"]),
            owner_id=int(payload["owner_id"]),
            subscription_id=int(payload["subscription_id"]),
            updates=payload.get("updates"),
        )
