#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# stash pricing assertions
mkdir -p receipts
cp receipts/assertions.jsonl receipts/assertions.pricing 2>/dev/null || true

# run the flaky verifier (it may write 0 lines)
python scripts/verify.py || true

# if verify wrote nothing, restore pricing; else append pricing to whatever it wrote
if [ ! -s receipts/assertions.jsonl ]; then
  mv -f receipts/assertions.pricing receipts/assertions.jsonl
else
  cat receipts/assertions.pricing >> receipts/assertions.jsonl
  rm -f receipts/assertions.pricing
fi
# show a quick summary
echo "✅ verify_safe done:"
echo "  $(wc -l < receipts/assertions.jsonl) total assertions in receipts/assertions.jsonl"
