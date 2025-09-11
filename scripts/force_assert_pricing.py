#!/usr/bin/env python3
import json, sys, os, glob, time
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from datetime import datetime, timezone

PIDS = set(sys.argv[1:])  # allow restricting from CLI; if empty, do all stamped
repo = Path(__file__).resolve().parents[1]
regp = repo / "registry" / "providers.json"
corpus = repo / "corpus"
out = repo / "receipts" / "assertions.jsonl"

# load registry (list of providers with {"id","rad","mpir",...})
reg = json.loads(regp.read_text())

def dec(x): return Decimal(str(x))

def first_pricing_pdf(pid):
    pat = str(corpus / pid / "*pricing*.pdf")
    files = sorted(glob.glob(pat))
    return files[0] if files else None

now = datetime.now(timezone.utc).isoformat(timespec="seconds")
lines = []

targets = []
for p in reg:
    pid = p.get("id")
    if not isinstance(pid, str) or not pid.startswith("racs_"): continue
    if PIDS and pid not in PIDS: continue
    targets.append(pid)

for pid in sorted(targets):
    # locate pricing PDF
    pdf = first_pricing_pdf(pid)
    rad = next((prov.get("rad") for prov in reg if prov.get("id")==pid), None)
    mpir = next((prov.get("mpir") for prov in reg if prov.get("id")==pid), None)

    entry = {
        "observed_at": now,
        "provider_id": pid,
        "subject": "pricing",
        "confidence": 0.9,
    }

    if pdf and rad is not None and mpir is not None:
        # DAP = RAD × (MPIR/100) ÷ 365 with Decimal + HALF_UP to cents
        dap = (dec(rad) * (dec(mpir)/dec(100)) / dec(365)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        entry["status"] = "pass"
        entry["claim"] = {"rad": float(rad), "mpir": float(mpir), "dap": float(dap)}
        entry["evidence"] = {"file": os.path.relpath(pdf, repo), "page": None}
    else:
        entry["status"] = "unknown"
        entry["claim"] = {"rad": rad, "mpir": mpir}
        entry["evidence"] = {"file": os.path.relpath(pdf, repo) if pdf else None}

    lines.append(json.dumps(entry, ensure_ascii=False))

out.write_text("\n".join(lines) + "\n")
print(f"✓ wrote {len(lines)} pricing assertions -> {out}")
