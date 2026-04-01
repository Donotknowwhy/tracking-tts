#!/usr/bin/env bash
set -euo pipefail

cd /home/ubuntu/tts-tracking
source venv/bin/activate

URL_FILE="${URL_FILE:-test_urls.txt}"
INTERVAL_HOURS="${INTERVAL_HOURS:-3}"

if [[ -n "${TTS_PROXY:-}" ]]; then
  exec python auto_track.py "$URL_FILE" "$INTERVAL_HOURS" --proxy "$TTS_PROXY"
else
  exec python auto_track.py "$URL_FILE" "$INTERVAL_HOURS"
fi
