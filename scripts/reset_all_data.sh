#!/usr/bin/env bash
# Xóa SQLite và toàn bộ file trong data/output — dữ liệu app về trạng thái sạch.
# Dùng trên server: SYSTEMD_SERVICE=tts-web.service ./scripts/reset_all_data.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p data/output

if [[ -n "${SYSTEMD_SERVICE:-}" ]] && command -v systemctl >/dev/null 2>&1; then
  echo "Stopping ${SYSTEMD_SERVICE}..."
  sudo systemctl stop "$SYSTEMD_SERVICE" || true
fi

rm -f data/tracking.db data/tracking.db-wal data/tracking.db-shm
rm -rf data/output/*
echo "Removed tracking.db and cleared data/output/"

if [[ -n "${SYSTEMD_SERVICE:-}" ]] && command -v systemctl >/dev/null 2>&1; then
  echo "Starting ${SYSTEMD_SERVICE}..."
  sudo systemctl start "$SYSTEMD_SERVICE"
fi

echo "Done."
