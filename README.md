# AstroCalc Calculation Engine — Patch v1

This patch brings:
- Electional module completion (Moon VoC, lunar phases, essential dignities, aspect matrix, Part of Fortune, basic scorer).
- FastAPI scaffold with `/electional/search`, `/healthz`.
- Rate limiting via Redis (FREE vs PRO per hour).
- Dockerfile + docker-compose for Dokploy.
- Pytest scaffolding and golden-data hooks.

## Quickstart (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Put your Swiss Ephemeris *.se1 files under ./ephe or set SE_EPHE_PATH
export SE_EPHE_PATH=./ephe

uvicorn app.main:app --host 0.0.0.0 --port 8000
# Open http://localhost:8000/docs
```

## Environment

Copy `.env.example` to `.env` and set:
- `API_KEYS_FREE`, `API_KEYS_PRO`
- `REDIS_URL`
- `FREE_HOURLY_LIMIT`, `PRO_HOURLY_LIMIT`
- `SE_EPHE_PATH`
- `NOMINATIM_USER_AGENT`

## Testing

Place your golden data under `tests/data/`:
- `golden_charts.json`
- `electional_scenarios.json`

Run:
```bash
pytest -q
```

## Notes
- Electional scorer is a baseline; plug in your event-type weights.
- VoC uses strict definition (from last major Moon aspect in sign until ingress).
