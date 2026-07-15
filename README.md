# Recovery Assistant

Minimal Telegram bot in Python for cycling recovery recommendations.

Telegram manages the user profile. Workouts can be imported from Strava via OAuth and webhook ingestion.

## Stack

- Python 3.12+
- aiogram 3
- SQLAlchemy 2 async
- PostgreSQL
- Alembic
- FastAPI
- httpx
- uvicorn
- pydantic-settings

## Project tree

```text
.
├── .env.example
├── Dockerfile
├── alembic.ini
├── alembic
│   ├── env.py
│   ├── script.py.mako
│   └── versions
│       └── 0001_initial.py
├── docker-compose.yml
├── app
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── bot
│   │   ├── __init__.py
│   │   ├── fsm.py
│   │   ├── messages.py
│   │   ├── router.py
│   │   ├── runner.py
│   │   └── handlers
│   │       ├── __init__.py
│   │       ├── profile.py
│   │       ├── start.py
│   │       ├── strava.py
│   │       └── workout.py
│   ├── db
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── models.py
│   │   └── session.py
│   ├── domain
│   │   ├── __init__.py
│   │   └── enums.py
│   ├── dto
│   │   ├── __init__.py
│   │   ├── recovery.py
│   │   └── workout.py
│   ├── repositories
│   │   ├── __init__.py
│   │   ├── strava_connections.py
│   │   ├── users.py
│   │   └── workouts.py
│   └── services
│       ├── __init__.py
│       ├── app_services.py
│       ├── recommendations.py
│       └── strava.py
├── docs
│   └── strava-next.md
├── main.py
├── pyproject.toml
├── render.yaml
├── requirements.txt
└── uv.lock
```

## Setup

```bash
uv sync
cp .env.example .env
```

`uv` is the source of truth for dependency management in this project:

- `pyproject.toml` declares direct dependencies
- `uv.lock` pins the full resolved graph
- `requirements.txt` is export-only for Docker builds

Common `uv` commands:

```bash
uv sync
uv sync --group dev
uv run alembic upgrade head
uv run python main.py
uv run ruff check
```

When you change dependencies:

```bash
uv add fastapi
uv add --group dev ruff
uv lock
UV_CACHE_DIR=.uv-cache uv export \
  --format requirements.txt \
  --frozen \
  --no-emit-project \
  --no-hashes \
  --output-file requirements.txt
```

Do not hand-edit `requirements.txt`; regenerate it from `uv.lock`.

Set these values in `.env`:

```bash
BOT_TOKEN=your-telegram-bot-token
BOT_USERNAME=your_telegram_bot_username
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/recovery_assistant
APP_BASE_URL=https://your-public-app-url.example
APP_HOST=0.0.0.0
APP_PORT=8000
STRAVA_CLIENT_ID=12345
STRAVA_CLIENT_SECRET=your-strava-client-secret
STRAVA_VERIFY_TOKEN=your-random-verify-token
STRAVA_REDIRECT_URI=https://your-public-app-url.example/strava/oauth/callback
```

Run migrations:

```bash
uv run alembic upgrade head
```

Run the app:

```bash
uv run python main.py
```

This starts the FastAPI server and configures Telegram via webhook.
If `PORT` is set by the platform, the app uses it automatically.

## Render

This repo includes [render.yaml](/Users/v.valko/ws/recovery_assistant/render.yaml:1) for a one-service Render deploy with:

- one Docker web service
- one managed Postgres database
- health check on `/health`
- `DATABASE_URL` wired from the Render Postgres instance

Before deploying on Render:

1. Push the repo with `render.yaml`.
2. Create the stack from Blueprint or sync the YAML in Render.
3. Set these env vars in Render:
   - `BOT_TOKEN`
   - `BOT_USERNAME`
   - `APP_BASE_URL`
   - `STRAVA_CLIENT_ID`
   - `STRAVA_CLIENT_SECRET`
   - `STRAVA_VERIFY_TOKEN`
   - `STRAVA_REDIRECT_URI`
4. Keep `APP_HOST=0.0.0.0`.
5. Let Render provide the port via `APP_PORT=10000` from `render.yaml`.
6. After the first deploy, update Strava callback settings to the actual Render URL.
7. If `BOT_USERNAME` is set, successful Strava OAuth redirects back to `https://t.me/<bot_username>`.

Notes for Render:

- the app already exposes `GET /health` for Render health checks
- this deployment shape is intended for a single instance MVP
- Telegram and Strava both use webhooks, so `APP_BASE_URL` must be a public `https` URL

## Docker

You can run the app and PostgreSQL locally through Docker Compose.

1. Create `.env` from `.env.example` and fill in the required values.
2. Keep `APP_BASE_URL` and `STRAVA_REDIRECT_URI` pointed to your public tunnel URL, not `localhost`.
3. Export Docker requirements from the lockfile if dependencies changed:

```bash
UV_CACHE_DIR=.uv-cache uv export \
  --format requirements.txt \
  --frozen \
  --no-emit-project \
  --no-hashes \
  --output-file requirements.txt
```

4. Start everything:

```bash
docker compose up --build
```

The app container runs `alembic upgrade head` automatically before starting.
It also waits for the database host to become reachable before running migrations.

Useful commands:

```bash
docker compose up -d --build
docker compose logs -f app
docker compose down
docker compose down -v
```

In Docker, PostgreSQL runs in the `db` service and the app uses:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/recovery_assistant
```

## Commands

- `/start`
- `/profile`
- `/set_weight`
- `/set_ftp`
- `/connect_strava`
- `/disconnect_strava`
- `/last_workout`

## HTTP endpoints

- `GET /health`
- `POST /telegram/webhook`
- `GET /strava/connect?telegram_user_id=<id>`
- `GET /strava/oauth/callback`
- `GET /strava/webhook`
- `POST /strava/webhook`

## Strava setup checklist

1. Create a Strava API app.
2. Set the callback domain to the public host used by `APP_BASE_URL`.
3. Set the OAuth redirect URI to `STRAVA_REDIRECT_URI`.
4. Expose the local app publicly, for example through `ngrok`.
5. Run `/connect_strava` in Telegram and authorize your Strava account.
6. Deploy or restart the app so it can register the Strava webhook subscription automatically.
7. Record a test ride and verify it appears in `/last_workout`.

## Notes

- Telegram handlers are thin and delegate to application services.
- `WorkoutInput` is the shared DTO for workout ingestion, so Strava can submit workouts without changing business logic.
- Carbohydrates are calculated from an in-code duration x `TSS/hour` rule table.
- `TSS/hour` is estimated from `weighted_average_watts / FTP` when both are available; otherwise the app falls back to the workout intensity bucket.
- The `goal` field remains in the database for now, but the bot no longer exposes goal-related functionality.
- Webhook ingestion currently processes only Strava `activity` `create` events.
