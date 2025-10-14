# Dockerfile
# ---------- builder ----------
FROM python:3.11-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# derleme araçları (wheel çıkarmak için)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*

# bağımlılıklar
COPY requirements.txt .
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
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# kodu komple kopyala (bootstrap_ephe.py, ephe/, app/, vs.)
# .dockerignore ile gereksizleri dışarıda tuttuğundan emin ol
COPY . /app

# (opsiyonel) ephemeris dosyalarını imaja koyuyorsan ephe/ klasörü burada bulunur
# COPY ephe/ ephe/

# izinler
RUN useradd -u 10001 -m engineuser && chown -R 10001:10001 /app
USER 10001

EXPOSE 8000

# Ephemeris yoksa (seas_00.se1) varsa bootstrap'i çalıştır, ardından uvicorn'u başlat
# NOT: /opt/venv/bin/uvicorn YOK; PATH'ten 'uvicorn' çağrılıyor.
CMD ["/bin/sh","-c","if [ ! -f \"$SE_EPHE_PATH/seas_00.se1\" ] && [ -f /app/bootstrap_ephe.py ]; then python /app/bootstrap_ephe.py; fi; exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --access-log"]
