#!/usr/bin/env bash
# Copy event-site -> public/ and inject Web3Forms key from env (Vercel).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/event-site"
OUT="$ROOT/public"

rm -rf "$OUT"
mkdir -p "$OUT"
cp -R "$SRC"/. "$OUT"/
rm -f "$OUT/README.md" "$OUT/vercel.json" "$OUT/.gitignore" "$OUT/package.json"

KEY="${WEB3FORMS_ACCESS_KEY:-}"
if [[ -z "$KEY" && -f "$SRC/js/form-config.js" ]]; then
  # Local fallback: reuse gitignored form-config.js if present
  cp "$SRC/js/form-config.js" "$OUT/js/form-config.js"
  echo "Injected form-config.js from local event-site copy."
elif [[ -n "$KEY" ]]; then
  # Escape for JS string
  ESCAPED="${KEY//\\/\\\\}"
  ESCAPED="${ESCAPED//\"/\\\"}"
  cat > "$OUT/js/form-config.js" <<EOF
window.SIPS_FORM_CONFIG = {
  accessKey: "${ESCAPED}",
};
EOF
  echo "Injected form-config.js from WEB3FORMS_ACCESS_KEY."
else
  cp "$SRC/js/form-config.example.js" "$OUT/js/form-config.js"
  echo "WARNING: WEB3FORMS_ACCESS_KEY not set; forms will show as unconfigured."
fi
