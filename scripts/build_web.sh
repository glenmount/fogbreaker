#!/usr/bin/env bash
set -euo pipefail
mkdir -p web/data
jq -n 'reduce (inputs|select(.subject=="pricing" or .subject=="compliance"))
       as $a ({}; .[$a.provider_id][$a.subject]=($a.status=="pass"))' \
   receipts/assertions.jsonl > web/data/verified.json
jq -n 'reduce (inputs|select(.subject=="pricing" or .subject=="compliance")
       | {pid:.provider_id, sub:.subject, file:("/" + .evidence.file)})
       as $a ({}; .[$a.pid][$a.sub]=$a.file)' \
   receipts/assertions.jsonl > web/data/evidence.json
echo "✓ built web/data/*.json"
