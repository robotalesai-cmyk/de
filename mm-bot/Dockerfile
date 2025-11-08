FROM python:3.11-slim

ENV POETRY_HOME=/opt/poetry \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY pyproject.toml README.md .
COPY src ./src
COPY configs ./configs
COPY docker-compose.yml .
COPY .env.example .

RUN poetry install --no-interaction --no-root
RUN poetry install --no-interaction

ENTRYPOINT ["poetry", "run", "bot-mm"]
