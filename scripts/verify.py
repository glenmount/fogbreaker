#!/usr/bin/env python3
import re, json, math, hashlib, datetime
from pathlib import Path
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

ROOT = Path(__file__).resolve().parents[1]
REG = json.loads((ROOT/"registry"/"providers.json").read_text(encoding="utf-8"))
OUT = ROOT/"receipts"/"assertions.jsonl"
OUT.parent.mkdir(parents=True, exist_ok=True)

def iso_now():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat()+'Z'

def sha256_text(s: str):
    h=hashlib.sha256(); h.update((s or "").encode('utf-8')); return h.hexdigest()

def load_pdf_text(path: Path):
    if not PdfReader: return None
    try:
        r = PdfReader(str(path))
        return [(i+1, (r.pages[i].extract_text() or "")) for i in range(len(r.pages))]
    except Exception:
        return None

def find_first(pattern, pages):
    rx = re.compile(pattern, re.IGNORECASE)
    for pageno, text in (pages or []):
        m = rx.search(text or "")
        if m:
            start=max(0, m.start()-80); end=min(len(text), m.end()+80)
            return pageno, text[start:end]
    return None, None

rows=[]
for r in REG:
    pid = r.get("provider_id")
    cdir = ROOT/"corpus"/pid
    if not cdir.exists(): 
        continue

    # ---- PRICING (verify RAD or DAP appears in pricing PDF) ----
    rad, mpir = r.get("rad"), r.get("mpir")
    if rad is not None and mpir is not None:
        pfiles = sorted([p for p in cdir.glob("*pricing*") if p.suffix.lower()==".pdf"])
        if pfiles:
            f = pfiles[0]
            pages = load_pdf_text(f)
            # RAD like "$400,000" (allow spaces/commas)
            rad_val = f"{int(rad):,}"
            p1, ex1 = find_first(rf"\$?\s*{rad_val}", pages)
            # DAP dollars and cents (rounded 2dp)
            dap = round(rad * (mpir/100.0) / 365.0 + 1e-9, 2)
            dap_dollars = int(dap); dap_cents = int(round((dap - dap_dollars)*100))
            p2, ex2 = find_first(rf"\$?\s*{dap_dollars}\.{str(dap_cents).zfill(2)}", pages)
            hits = (p1 is not None) + (p2 is not None)
            status = "pass" if hits>=1 else "fail"
            rows.append({
                "observed_at": iso_now(),
                "provider_id": pid,
                "subject": "pricing",
                "claim": {"rad": float(rad), "mpir": float(mpir), "dap": dap},
                "evidence": {
                    "file": str(f.relative_to(ROOT)),
                    "page": p1 or p2,
                    "text_excerpt_sha256": sha256_text((ex1 or ex2) or "")
                },
                "status": status,
                "confidence": 0.6 if hits==1 else (0.9 if hits==2 else 0.2)
            })
        else:
            rows.append({
                "observed_at": iso_now(), "provider_id": pid, "subject": "pricing",
                "claim":{"rad": float(rad), "mpir": float(mpir)}, 
                "evidence":{"file": None}, "status":"unknown", "confidence":0.1
            })

    # ---- COMPLIANCE (basic presence check) ----
    cfiles = sorted([p for p in cdir.glob("*compliance*") if p.suffix.lower()==".pdf"])
    if cfiles:
        f = cfiles[0]; pages = load_pdf_text(f)
        p, ex = find_first(r"(assessment|non-?compliance|notice|decision|sanction)", pages)
        rows.append({
            "observed_at": iso_now(), "provider_id": pid, "subject":"compliance",
            "evidence":{"file":str(f.relative_to(ROOT)),"page":p,"text_excerpt_sha256":sha256_text(ex or "")},
            "status": "pass" if p else "unknown", "confidence": 0.6 if p else 0.2
        })
    else:
        rows.append({
            "observed_at": iso_now(), "provider_id": pid, "subject":"compliance",
            "evidence":{"file":None},"status":"unknown","confidence":0.1
        })

    # ---- STARS (registry-based pass) ----
    rows.append({
        "observed_at": iso_now(), "provider_id": pid, "subject":"stars",
        "claim":{"star_overall": r.get("star_overall"), "star_clinical": r.get("star_clinical"), "star_compliance": r.get("star_compliance")},
        "evidence":{"file":"corpus/_sources"}, "status":"pass" if r.get("star_overall") is not None else "unknown", "confidence":0.8 if r.get("star_overall") is not None else 0.2
    })

# append (idempotent enough for phase-1)
with OUT.open("w", encoding="utf-8") as w:
    for row in rows:
        w.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",",":")) + "\n")
print(f"Wrote {len(rows)} assertion lines → {OUT}")
