#!/usr/bin/env python3
import json, sys
from pathlib import Path

reg = Path("registry/providers.json")
corpus = Path("corpus")
# load registry (array of providers)
data = json.loads(reg.read_text())
assert isinstance(data, list), "registry/providers.json must be a list"
have = {p.get("id") for p in data if isinstance(p, dict)}
added = 0
for d in sorted(corpus.glob("racs_*")):
    if not d.is_dir(): continue
    pid = d.name
    if pid not in have:
        data.append({"id": pid})
        have.add(pid); added += 1
reg.write_text(json.dumps(data, indent=2) + "\n")
print(f"✓ synced registry: added {added} providers")
