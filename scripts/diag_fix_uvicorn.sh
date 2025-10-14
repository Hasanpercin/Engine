#!/usr/bin/env bash
set -euo pipefail

# === CONFIG ===
SVC="${SVC:-yeni-proje-astrocalc29rapor-ey4xwl}"
HEALTHZ="${HEALTHZ:-http://127.0.0.1:8000/healthz}"
SOLAR_JSON='{"start_year":2025,"start_month":1,"start_day":1,"end_year":2025,"end_month":12,"end_day":31,"debug":true}'
LUNAR_JSON='{"start_year":2025,"start_month":1,"start_day":1,"end_year":2025,"end_month":12,"end_day":31,"debug":true}'

say() { printf "\n\033[1;36m[diag]\033[0m %s\n" "$*"; }

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "missing: $1"; exit 1; }
}
require docker
require jq

say "Service: $SVC"

# --- 1) Mevcut image / komut / args
IMG="$(docker service inspect "$SVC" --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}' || true)"
CMD_JSON="$(docker service inspect "$SVC" --format '{{json .Spec.TaskTemplate.ContainerSpec.Command}}' || echo null)"
ARGS_JSON="$(docker service inspect "$SVC" --format '{{json .Spec.TaskTemplate.ContainerSpec.Args}}' || echo null)"
PORTS_JSON="$(docker service inspect "$SVC" --format '{{json .Endpoint.Spec.Ports}}' || echo null)"

say "Image            : ${IMG:-<none>}"
say "Command override : ${CMD_JSON}"
say "Args override    : ${ARGS_JSON}"
say "Ports            : ${PORTS_JSON}"

# --- 2) İmaj içinde uvicorn var mı? (PATH/versiyon)
if [[ -n "${IMG:-}" && "${IMG:-}" != "null" ]]; then
  say "Checking uvicorn inside image..."
  docker run --rm --entrypoint /bin/sh "$IMG" -c 'echo "PATH=$PATH"; command -v uvicorn || true; python - <<PY
try:
    import uvicorn, sys
    print("uvicorn module:", uvicorn.__file__)
    print("python:", sys.version)
except Exception as e:
    print("uvicorn import failed:", e)
PY'
fi

# --- 3) /opt/venv/bin/uvicorn kullanılıyor mu? -> düzelt
NEED_FIX=0
if echo "$CMD_JSON $ARGS_JSON" | grep -q "/opt/venv/bin/uvicorn"; then
  say "Found legacy path (/opt/venv/bin/uvicorn) in service command/args -> will fix."
  NEED_FIX=1
fi

# Ayrıca 'Command' tanımlıysa Dockerfile CMD override edilmiş demektir.
if [[ "$CMD_JSON" != "null" ]]; then
  say "Service has Command override -> will reset to Dockerfile CMD."
  NEED_FIX=1
fi

# --- 4) Port publish'ı ingress'e geçirip tek replika ile ayağa kaldırma
fix_ports() {
  say "Reset replicas to 0 (free any host port) ..."
  docker service update --replicas 0 "$SVC" >/dev/null

  say "Remove any existing publish on 8000 (best-effort)..."
  docker service update --publish-rm 8000 "$SVC" >/dev/null || true
  docker service update --publish-rm published=8000,target=8000,mode=host "$SVC" >/dev/null || true
  docker service update --publish-rm published=8000,target=8000,mode=ingress "$SVC" >/dev/null || true

  say "Add publish 8000->8000 in ingress mode..."
  docker service update --publish-add published=8000,target=8000,mode=ingress "$SVC" >/dev/null
}

fix_cmd() {
  say "Resetting entrypoint/args to Dockerfile CMD..."
  docker service update --entrypoint "" --args "" "$SVC" >/dev/null
}

set_cmd_explicit() {
  say "Setting explicit start command (bootstrap + uvicorn via PATH)..."
  docker service update \
    --entrypoint "/bin/sh" \
    --args "-c [ -f /app/ephe/seas_00.se1 ] || python /app/bootstrap_ephe.py; exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --access-log" \
    "$SVC" >/dev/null
}

wait_ready() {
  say "Scaling to 1 replica..."
  docker service update --replicas 1 "$SVC" >/dev/null

  say "Waiting for a RUNNING task..."
  for i in {1..40}; do
    ST="$(docker service ps "$SVC" --format '{{.CurrentState}}' | head -n1 || true)"
    if echo "$ST" | grep -qi 'Running'; then
      say "Task is running."
      return 0
    fi
    sleep 1
  done
  say "Timeout waiting for RUNNING state. Current:"
  docker service ps "$SVC" --no-trunc
  return 1
}

if [[ $NEED_FIX -eq 1 ]]; then
  fix_ports
  # Tercih 1: Dockerfile CMD'yi kullan (önerilen)
  fix_cmd || true
  if ! wait_ready; then
    say "Dockerfile CMD ile ayağa kalkmadı; explicit command denenecek."
    # Tercih 2: Açıkça doğru komutu ver
    fix_ports
    set_cmd_explicit
    wait_ready
  fi
else
  say "No legacy /opt/venv references detected. Ensuring publish + replicas..."
  fix_ports
  wait_ready
fi

say "Service ports after update:"
docker service inspect "$SVC" --format '{{json .Endpoint.Spec.Ports}}' | jq

say "Recent logs (2m):"
docker service logs --since 2m "$SVC" || true

# --- 5) Smoke (host publish üzerinden)
say "Smoke: /healthz"
curl -sS "$HEALTHZ" | jq .

say "Smoke: solar 2025"
curl -sS -H 'content-type: application/json' -d "$SOLAR_JSON" \
  "${HEALTHZ%/healthz}/eclipses/solar/range" | jq '.count, [.items[].type]'

say "Smoke: lunar 2025"
curl -sS -H 'content-type: application/json' -d "$LUNAR_JSON" \
  "${HEALTHZ%/healthz}/eclipses/lunar/range" | jq '.count, [.items[].type]'
