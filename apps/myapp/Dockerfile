# FROM python:3.13.2-alpine3.21@sha256:323a717dc4a010fee21e3f1aac738ee10bb485de4e7593ce242b36ee48d6b352

# Needed psycopg2, python:3.13.2 was incompatible. No way to get or build it.
# Moved down to python 3.12.
FROM python:3.12-alpine3.21@sha256:690af2fd7f62e24289b28a397baa54eb6978340b4a3106df1015807706f1c7f2
# latest? eb120d016adcbc8bac194e15826bbb4f1d1569d298d8817bb5049ed5e59f41d9
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app
RUN apk add --no-cache gcc musl-dev postgresql-dev
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-cache
COPY . .
CMD ["uv", "run", "python", "app.py"]