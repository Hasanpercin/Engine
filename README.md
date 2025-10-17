# 🌌 AstroCalc Calculation Engine

Professional-grade astrology calculation engine built with FastAPI, Swiss Ephemeris, and modern Python.

## 📊 Current Status: **Production Ready** ✅

**v1.0 - Full-Stack Astrology Engine**
- ✅ **12 API Modules** (Natal, Synastry, Transits, Progressions, Eclipses, Lunar, Electional, Composite, Returns, Profections, Retrogrades, Health)
- ✅ **Swiss Ephemeris Integration** (High-precision astronomical calculations)
- ✅ **Rate Limiting** (FREE vs PRO tier via Redis)
- ✅ **Docker Ready** (Multi-stage build, health checks)
- ✅ **OpenAPI Documentation** (Swagger UI + ReDoc)
- ✅ **Production Tested** (Pytest + golden data validation)

## 🚀 Quick Start

### Local Development (Docker Compose)

```bash
git clone https://github.com/Hasanpercin/Engine.git
cd Engine
docker-compose up --build
```

### Access the API:
- Health: http://localhost:8000/healthz
- Docs: http://localhost:8000/docs
- Version: http://localhost:8000/version

## 🏗️ Architecture

12 API Routers → Swiss Ephemeris + Kerykeion + Immanuel + Skyfield → Redis Rate Limiting

## 🛠️ API Modules

1. **Natal** (`/natal`) - Birth charts
2. **Synastry** (`/synastry`) - Compatibility 
3. **Transits** (`/transits`) - Current transits
4. **Progressions** (`/progressions`) - Secondary progressions
5. **Returns** (`/returns`) - Solar/Lunar returns
6. **Eclipses** (`/eclipses`) - Eclipse calculations
7. **Lunar** (`/lunar`) - Moon phases & VoC
8. **Electional** (`/electional`) - Optimal timing
9. **Composite** (`/composite`) - Relationship charts
10. **Profections** (`/profections`) - Annual profections
11. **Retrogrades** (`/retrogrades`) - Retrograde periods
12. **Health** (`/healthz`) - Health check

## 🔧 Configuration

See docker-compose.yml and Dockerfile for full configuration.

**Environment Variables:**
- SE_EPHE_PATH=/app/ephe
- REDIS_URL=redis://redis:6379/0
- API_KEYS_FREE, API_KEYS_PRO
- FREE_HOURLY_LIMIT=100, PRO_HOURLY_LIMIT=1000

## 📡 API Documentation

Interactive docs at `/docs` and `/redoc` when running.

## 🧪 Testing

```bash
pytest -v
pytest --cov=app --cov-report=html
```

## 📚 Tech Stack

- FastAPI 0.104.1
- pyswisseph 2.10.3
- Kerykeion 4.14.0
- Immanuel 1.4.2
- Skyfield 1.48
- Redis 7

## 📄 License

Private - All rights reserved

---

**Version:** 1.0.0 | **Status:** 🟢 Production Ready | **Modules:** 12