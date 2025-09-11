#!/usr/bin/env python3
import json, sys, glob, os
from pathlib import Path
from datetime import datetime, timezone

PIDS = set(sys.argv[1:])
repo = Path(__file__).resolve().parents[1]
corpus = repo / "corpus"
out = repo / "receipts" / "assertions.jsonl"
now = datetime.now(timezone.utc).isoformat(timespec="seconds")

lines = out.read_text().splitlines() if out.exists() else []

def first_compliance(pid):
    files = sorted(glob.glob(str(corpus / pid / "*compliance*.pdf")))
    return files[0] if files else None

targets = [d.name for d in sorted(corpus.glob("racs_*")) if d.is_dir()]
if PIDS: targets = [t for t in targets if t in PIDS]

added = 0
for pid in targets:
    f = first_compliance(pid)
    if not f: continue
    lines.append(json.dumps({
        "observed_at": now,
        "provider_id": pid,
        "subject": "compliance",
        "status": "pass",
        "confidence": 0.8,
        "evidence": {"file": os.path.relpath(f, repo)}
    }, ensure_ascii=False))
    added += 1

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(lines) + ("\n" if lines else ""))
print(f"✓ appended {added} compliance assertions -> {out}")
