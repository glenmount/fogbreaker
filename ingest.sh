#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob
usage(){ echo "Usage: $0 racs_<code> /path/to/drive_folder [--no-commit]"; exit 1; }
PID="${1:-}"; SRC="${2:-}"; COMMIT="yes"
[[ -z "${PID}" || -z "${SRC}" ]] && usage
[[ "${3:-}" == "--no-commit" ]] && COMMIT="no"
DEST="corpus/${PID}"; mkdir -p "$DEST"
# 1) move PDFs
found=0; for f in "$SRC"/*.pdf "$SRC"/*.PDF; do [[ -e "$f" ]] || continue; mv -- "$f" "$DEST/"; ((found++))||true; done
[[ $found -eq 0 ]] && echo "No PDFs found in $SRC" && exit 2
# 2) normalize names
for f in "$DEST"/*\ *; do nf="${f// /-}"; [[ "$f" != "$nf" ]] && mv -- "$f" "$nf" || true; done
for f in "$DEST"/*costs* "$DEST"/*cost*; do [[ -e "$f" ]] || continue; nf="${f//costs/pricing}"; nf="${nf//cost/pricing}"; [[ "$f" != "$nf" ]] && mv -- "$f" "$nf" || true; done
for f in "$DEST"/*overall_stars*; do nf="${f//overall_stars/overall-stars}"; mv -- "$f" "$nf" || true; done
for f in "$DEST"/*.pdf.pdf; do nf="${f%.pdf}"; mv -- "$f" "$nf" || true; done
for f in "$DEST"/*.PDF; do nf="${f%.*}.pdf"; mv -- "$f" "$nf" || true; done
# fix “…__https://domain/…” → “…__domain…”
for f in "$DEST"/*__https:* "$DEST"/*__http:*; do
  base="$(basename "$f")"
  fixed="$(printf '%s\n' "$base" | sed -E 's#__https?://([^/]+)/?#__\1#')"
  [[ "$base" != "$fixed" ]] && mv -- "$DEST/$base" "$DEST/$fixed" || true
done
echo "→ Current files in $DEST"; ls -lh "$DEST"
# 3) rebuild receipts → score → digest
make all
# 4) verifier (writes receipts/assertions.jsonl)
if [[ -f scripts/verify.py ]]; then
  python scripts/verify.py || true
  echo "Assertions for ${PID}:"; grep -n "\"provider_id\":\"${PID}\"" receipts/assertions.jsonl || true
fi
echo "→ Recent receipts for ${PID}:"; grep -n "\"provider_id\":\"${PID}\"" receipts/events.jsonl | tail -n 10 || true
# 5) commit (unless --no-commit)
if [[ "${COMMIT}" == "yes" ]]; then
  git add "$DEST" receipts rankings ledger || true
  git add registry/providers.json 2>/dev/null || true
  CHANGES=$(git diff --cached --name-only | wc -l | tr -d ' ')
  [[ "$CHANGES" != "0" ]] && git commit -m "data: ingest docs for ${PID} ($(ls -1 "$DEST" | wc -l | tr -d ' ' ) files) + receipts/digest" && git push || echo "No staged changes."
else
  echo "→ Skipping commit (--no-commit)"
fi
echo "✅ Done."
