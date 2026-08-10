# KisanAI OS - backend production image
#
# Build:
#   docker build -t kisanai-os-backend .
# Run (SQLite with a persistent volume):
#   docker run -d -p 8000:8000 \
#     -e APP_MODE=production \
#     -e DEBUG=false \
#     -e SECRET_KEY=<32+ char secret> \
#     -e DATABASE_URL=sqlite:////data/kisanai.db \
#     -v kisanai_data:/data \
#     -v kisanai_media:/app/media \
#     kisanai-os-backend
# Recommended for production: use PostgreSQL and a managed media bucket,
# see DEPLOYMENT.md.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Create a non-root user to run the application.
RUN groupadd --gid 10001 kisanai \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin kisanai

WORKDIR /app

# Install dependencies first (layer caching).
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY alembic.ini ./
COPY alembic ./alembic
COPY config ./config
COPY main.py ./
COPY .env.example ./.env.example

# Persistent media/upload directory (mounted as a volume in production).
RUN mkdir -p /app/media/uploads && chown -R kisanai:kisanai /app

USER kisanai

EXPOSE 8000

# Runs migrations then starts the ASGI server. Override PORT via env if needed.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --no-access-log"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)" || exit 1
