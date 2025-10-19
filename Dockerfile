# Dockerfile
# ---------- builder ----------
FROM python:3.11-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# wheel derlemek için derleyici araçlar
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*

# (isteğe bağlı) pip/setuptools güncelle
RUN python -m pip install --upgrade pip setuptools wheel

# 🔴 KRİTİK: requirements.txt'yi builder aşamasına kopyala
# Eğer dosyanız repo kökünde değilse yolu düzeltin (ör. app/requirements.txt -> ./requirements.txt)
COPY requirements.txt .

# (opsiyonel) dosya gerçekten geldi mi kontrol et
RUN test -f requirements.txt || (echo "requirements.txt not found in build context!" && exit 1)

# bağımlılık tekerleklerini çıkar
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt && \
    python -c "import sys,subprocess; print('--- BUILDER FREEZE ---'); subprocess.run([sys.executable,'-m','pip','freeze'])"

# ---------- runtime ----------
FROM python:3.11-slim
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

ARG ENGINE_VERSION=dev
ARG GIT_SHA=unknown
ARG BUILD_TIME=
ENV ENGINE_VERSION=${ENGINE_VERSION} GIT_SHA=${GIT_SHA} BUILD_TIME=${BUILD_TIME} SE_EPHE_PATH=/app/ephe

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# builder’dan wheel’leri kopyala ve kur
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# uygulama kodunu kopyala
COPY . /app

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3); sys.exit(0)" || exit 1

RUN useradd -u 10001 -m engineuser && chown -R 10001:10001 /app
USER 10001

EXPOSE 8000

CMD ["/bin/sh","-c","if [ ! -f \"$SE_EPHE_PATH/seas_00.se1\" ] && [ -f /app/bootstrap_ephe.py ]; then python /app/bootstrap_ephe.py; fi; exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --access-log"]
