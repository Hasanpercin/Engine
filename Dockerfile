# Dockerfile
# ---------- builder ----------
FROM python:3.11-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------- runtime ----------
FROM python:3.11-slim
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Build-time metadata (CI'da --build-arg ile geçin)
ARG ENGINE_VERSION=dev
ARG GIT_SHA=unknown
ARG BUILD_TIME=
ENV ENGINE_VERSION=${ENGINE_VERSION} \
    GIT_SHA=${GIT_SHA} \
    BUILD_TIME=${BUILD_TIME} \
    SE_EPHE_PATH=/app/ephe

# (opsiyonel) küçük runtime bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Uygulama
COPY app/ app/
# Eğer ephemeris dosyalarını imaja koymak istiyorsan: COPY ephe/ ephe/
EXPOSE 8000

# non-root
RUN useradd -u 10001 -m engineuser
USER 10001

# Uvicorn access-log açık
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--access-log"]
