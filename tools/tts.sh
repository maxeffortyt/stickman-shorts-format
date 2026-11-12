#!/usr/bin/env bash
# ElevenLabs voice-over with character timestamps, via curl.
#
# Usage:  tools/tts.sh narration.txt OUT_BASENAME
#   writes OUT_BASENAME.mp3 and OUT_BASENAME.alignment.json
#
# Needs in the environment (for example: set -a; source .env; set +a):
#   ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL_ID
# Optional: STABILITY (default 0.5), OUTPUT_FORMAT (default mp3_44100_192).
# curl does the HTTP call (some Python installs have no SSL certificates); python3 only builds/parses JSON.
# Never commit .env or print the key.
set -euo pipefail
TXT="${1:?usage: tts.sh narration.txt OUT_BASENAME}"
OUT="${2:?usage: tts.sh narration.txt OUT_BASENAME}"
: "${ELEVENLABS_API_KEY:?set ELEVENLABS_API_KEY}" "${ELEVENLABS_VOICE_ID:?set ELEVENLABS_VOICE_ID}" "${ELEVENLABS_MODEL_ID:?set ELEVENLABS_MODEL_ID}"
STABILITY="${STABILITY:-0.5}"
FORMAT="${OUTPUT_FORMAT:-mp3_44100_192}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 -c 'import json,sys; print(json.dumps({"text": open(sys.argv[1]).read().strip(), "model_id": sys.argv[2], "voice_settings": {"stability": float(sys.argv[3])}}))' \
  "$TXT" "$ELEVENLABS_MODEL_ID" "$STABILITY" > "$TMP/req.json"

HTTP=$(curl -sS -m 180 -o "$TMP/resp.json" -w "%{http_code}" -X POST \
  "https://api.elevenlabs.io/v1/text-to-speech/${ELEVENLABS_VOICE_ID}/with-timestamps?output_format=${FORMAT}" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" -H "Content-Type: application/json" --data @"$TMP/req.json")
if [ "$HTTP" != "200" ]; then echo "ElevenLabs HTTP $HTTP" >&2; head -c 500 "$TMP/resp.json" >&2; echo >&2; exit 1; fi

python3 - "$TMP/resp.json" "$OUT" <<'EOF'
import base64, json, sys
r = json.load(open(sys.argv[1]))
open(sys.argv[2] + ".mp3", "wb").write(base64.b64decode(r["audio_base64"]))
json.dump(r.get("alignment") or {}, open(sys.argv[2] + ".alignment.json", "w"))
al = r.get("alignment") or {}
end = (al.get("character_end_times_seconds") or [0])[-1]
words = len("".join(al.get("characters", [])).split())
print(f"{sys.argv[2]}.mp3: {end:.2f} s of speech, {words} words, {words / end if end else 0:.2f} words/s")
EOF
