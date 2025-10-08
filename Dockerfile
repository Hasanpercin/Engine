# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_ROOT_USER_ACTION=ignore

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) VENV ÖNCE
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 2) Sonra requirements (artık venv'in pip'i)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) Uygulama kodu
COPY . .

# 4) Güvenlik: non-root kullanıcı ile çalış
RUN useradd -m app && chown -R app:app /app
USER app

# 5) Ephemeris yolu (Dokploy volume'ünü buraya bağlayacaksın)
ENV SE_EPHE_PATH=/app/ephe

EXPOSE 8000

# 6) Uvicorn: düz tırnak + logları aç
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--log-level","info","--access-log"]
