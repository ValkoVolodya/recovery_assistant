# Strava integration next

Strava should be added as an adapter layer that feeds the existing application service rather than introducing separate recovery logic.

## Planned flow

1. Store OAuth tokens per user.
2. Expose a webhook endpoint for Strava activity events.
3. Fetch activity details from Strava after webhook delivery.
4. Map the activity into `WorkoutInput`.
5. Call the shared `WorkoutService.log_workout(...)` application service.
6. Refresh expired access tokens before API calls.

## Data to add

- `strava_athlete_id`
- `strava_access_token`
- `strava_refresh_token`
- `strava_token_expires_at`

Those fields can live in a dedicated `strava_connections` table to keep Telegram identity separate from provider credentials.

## Adapter shape

The Strava side should translate provider payloads into internal DTOs:

```python
workout_input = WorkoutInput(
    duration_minutes=round(activity.moving_time_seconds / 60),
    kilojoules=round(activity.kilojoules),
    intensity=map_strava_intensity(activity),
)
await workout_service.log_workout(
    telegram_user_id=user.telegram_user_id,
    username=user.username,
    first_name=user.first_name,
    workout_input=workout_input,
)
```

## Token lifecycle

- On connect: exchange auth code for access and refresh tokens, then persist them.
- On webhook processing or backfill: check expiry and refresh if needed.
- On refresh: atomically replace access token, refresh token, and expiry timestamp.

## Why this structure holds

- Telegram stays profile-only.
- Strava becomes the workout input adapter.
- Recovery logic stays in `RecoveryRecommendationService`.
- Workout persistence stays in `WorkoutService`.
