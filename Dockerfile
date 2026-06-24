FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
COPY app ./app
COPY docker ./docker
COPY alembic.ini ./
COPY alembic ./alembic
COPY main.py ./

RUN python -m ensurepip --upgrade && \
    python -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python -m pip install --no-cache-dir -r requirements.txt

CMD ["sh", "-c", "python docker/start.py && alembic upgrade head && python main.py"]
