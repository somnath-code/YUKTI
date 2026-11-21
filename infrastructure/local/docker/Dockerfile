FROM python:3.15.2-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/yukti
COPY infrastructure/local/docker/requirements-runtime.lock ./
RUN pip install --no-cache-dir -r requirements-runtime.lock && useradd --uid 10001 -m yukti && install -d -o yukti -g yukti /var/yukti /var/yukti/artifacts
COPY --chown=yukti:yukti apps apps
COPY --chown=yukti:yukti packages packages
COPY --chown=yukti:yukti adapters adapters
COPY --chown=yukti:yukti workers workers
COPY --chown=yukti:yukti scripts scripts
COPY --chown=yukti:yukti database database
COPY --chown=yukti:yukti config config
COPY --chown=yukti:yukti templates templates
USER 10001:0
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["python","-m","uvicorn","apps.api.main:app","--host","0.0.0.0","--port","8000","--no-proxy-headers"]
