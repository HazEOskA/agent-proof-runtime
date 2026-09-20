FROM node:22-slim AS frontend

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    APR_CONTROL_PLANE_DIST=/app/frontend/dist

WORKDIR /app
COPY . /app
# The installed package lives in site-packages, so the control plane cannot
# find the bundle by walking up from its own file. APR_CONTROL_PLANE_DIST above
# points at this copy instead.
COPY --from=frontend /frontend/dist /app/frontend/dist
RUN python -m pip install --no-cache-dir '.[openai]' \
    && useradd --create-home --uid 10001 apr \
    && mkdir -p /app/.runs \
    && chown -R apr:apr /app

USER apr
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8080') + '/health', timeout=2)" || exit 1

CMD ["apr", "mission-control", "--host", "0.0.0.0", "--allow-remote"]
