FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Render/Railway/Fly set $PORT; default for local docker runs
ENV PORT=10000

# NOTE: SQLite is used when DATABASE_URL is not set. On free hosts the
# filesystem is ephemeral, so set DATABASE_URL to a persistent Postgres
# for a real league (see README).
CMD ["sh", "-c", "gunicorn 'run:app' --bind 0.0.0.0:${PORT} --workers 2 --timeout 120"]
