FROM python:3.12-slim

# Instalamos uv desde su contendor oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copiamos definicion de paquetes e instalamos
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copiamos la app y la configuración de Alembic
COPY src/ ./src/
COPY main.py ./
COPY data/ ./data/
COPY alembic.ini ./
COPY alembic/ ./alembic/


CMD ["uv", "run", "main.py"]