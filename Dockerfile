# Dockerfile
# ---------- builder ----------
FROM python:3.11-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# derleme araçları (wheel çıkarmak için)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*

# pip/setuptools/wheel upgrade -> dependency resolver hız/kare
RUN python -m pip install --upgrade pip setuptools wheel

RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt && \
    python -c "import pkgutil, sys; print('--- BUILDER FREEZE ---'); import subprocess; subprocess.run([sys.executable,'-m','pip','freeze'])"

# bağımlılıklar
COPY requirements.txt .
# Not: requirements.txt içinde pydantic-settings>=2.5.2 ve fastapi-mcp==0.4.0 olmalı (çatışmayı çözmek için)
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------- runtime ----------
FROM python:3.11-slim
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# build-time metadata (CI'dan --build-arg ile geçilebilir)
ARG ENGINE_VERSION=dev
ARG GIT_SHA=unknown
ARG BUILD_TIME=
ENV ENGINE_VERSION=${ENGINE_VERSION} \
    GIT_SHA=${GIT_SHA} \
    BUILD_TIME=${BUILD_TIME} \
    SE_EPHE_PATH=/app/ephe

# küçük runtime bağımlılığı
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# wheel'leri yükle
COPY --from=builder /wheels /wheels
# (opsiyonel) runtime imajında da pip'i güncellemek istersen uncomment et:
# RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# kodu komple kopyala (bootstrap_ephe.py, ephe/, app/, vs.)
# .dockerignore ile gereksizleri dışarıda tuttuğundan emin ol
COPY . /app

# (opsiyonel) ephemeris dosyalarını imaja koyuyorsan ephe/ klasörü burada bulunur
# COPY ephe/ ephe/

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3); sys.exit(0)" || exit 1

# izinler
RUN useradd -u 10001 -m engineuser && chown -R 10001:10001 /app
USER 10001

EXPOSE 8000

# Ephemeris yoksa bootstrap, sonra uvicorn
CMD ["/bin/sh","-c","if [ ! -f \"$SE_EPHE_PATH/seas_00.se1\" ] && [ -f /app/bootstrap_ephe.py ]; then python /app/bootstrap_ephe.py; fi; exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --access-log"]
