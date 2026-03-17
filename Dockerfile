# Stage 1: Build frontend
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --legacy-peer-deps
COPY frontend/ ./
RUN npm run build

# Stage 2: Install Python dependencies
FROM python:3.12-slim AS backend-build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src/ src/
COPY leaderboard_card_coach.md ./
RUN uv sync --frozen --no-dev

# Stage 3: Runtime
FROM python:3.12-slim
RUN useradd --create-home appuser
WORKDIR /app
COPY --from=backend-build /app/.venv .venv
COPY --from=backend-build /app/src src
COPY --from=backend-build /app/leaderboard_card_coach.md .
COPY --from=frontend-build /app/frontend/dist frontend/dist
ENV PATH="/app/.venv/bin:$PATH" DEBUG=false
EXPOSE 8000
USER appuser
CMD ["life-coach-api"]
