#!/usr/bin/env python3
import argparse, json, re, hashlib, datetime
from pathlib import Path

# PDF text extraction (optional)
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

# Stars extract (cached)
try:
    import pandas as pd
except Exception:
    pd = None

ROOT = Path(__file__).resolve().parents[1]
REG_PATH = ROOT/"registry"/"providers.json"
SRC_DIR  = ROOT/"corpus"
OUT_PATH = ROOT/"receipts"/"assertions.jsonl"

def iso_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def sha256_text(s: str) -> str:
    h = hashlib.sha256(); h.update((s or "").encode("utf-8")); return h.hexdigest()

def read_registry():
    return json.loads(REG_PATH.read_text(encoding="utf-8"))

def load_pdf_text(path: Path):
    if not PdfReader: return None
    try:
        r = PdfReader(str(path))
        pages = []
        for i in range(len(r.pages)):
            try:
                txt = r.pages[i].extract_text() or ""
            except Exception:
                txt = ""
            pages.append((i+1, txt))
        return pages
    except Exception:
        return None

def find_first(pattern, pages):
    rx = re.compile(pattern, re.IGNORECASE)
    for pageno, text in (pages or []):
        m = rx.search(text or "")
        if m:
            start = max(0, m.start()-80); end = min(len(text), m.end()+80)
            return pageno, text[start:end]
    return None, None

def verify_pricing(pid: str, rad, mpir, corpus_dir: Path):
    if rad is None or mpir is None:
        return {"provider_id":pid,"subject":"pricing","status":"unknown","confidence":0.1,
                "claim":{"rad":rad,"mpir":mpir},"evidence":{"file":None}}
    pats = ("*pricing*","*cost*","*room*","*fee*")
    pdfs = []
    for pat in pats:
        pdfs += [p for p in corpus_dir.glob(pat) if p.suffix.lower()==".pdf"]
    pdfs = sorted(set(pdfs))
    if not pdfs:
        return {"provider_id":pid,"subject":"pricing","status":"unknown","confidence":0.1,
                "claim":{"rad":float(rad),"mpir":float(mpir)},"evidence":{"file":None}}
    f = pdfs[0]
    pages = load_pdf_text(f)

    rad_str = f"{int(rad):,}"
    p1, ex1 = find_first(rf"\$?\s*{rad_str}", pages)

    dap = round(float(rad) * (float(mpir)/100.0) / 365.0 + 1e-9, 2)
    dap_d = int(dap); dap_c = int(round((dap - dap_d)*100))
    p2, ex2 = find_first(rf"\$?\s*{dap_d}\.{str(dap_c).zfill(2)}", pages)

    hits = (p1 is not None) + (p2 is not None)
    status = "pass" if hits>=1 else "fail"
    conf   = 0.6 if hits==1 else (0.9 if hits==2 else 0.2)
    return {
        "provider_id":pid,"subject":"pricing","status":status,"confidence":conf,
        "claim":{"rad":float(rad),"mpir":float(mpir),"dap":dap},
        "evidence":{"file":str(f.relative_to(ROOT)),
                    "page":p1 or p2,
                    "text_excerpt_sha256": sha256_text((ex1 or ex2) or "")}
    }

def verify_compliance(pid: str, corpus_dir: Path):
    pats = ("*compliance*","*assess*","*decision*","*sanction*")
    pdfs = []
    for pat in pats:
        pdfs += [p for p in corpus_dir.glob(pat) if p.suffix.lower()==".pdf"]
    pdfs = sorted(set(pdfs))
    if not pdfs:
        return {"provider_id":pid,"subject":"compliance","status":"unknown","confidence":0.2,
                "evidence":{"file":None}}
    f = pdfs[0]
    pages = load_pdf_text(f)
    p, ex = find_first(r"(assessment|decision|sanction|non-?compliance|notice)", pages)
    return {
        "provider_id":pid,"subject":"compliance","status":"pass" if p else "unknown","confidence":0.6 if p else 0.2,
        "evidence":{"file":str(f.relative_to(ROOT)),"page":p,
                    "text_excerpt_sha256": sha256_text(ex or "")}
    }

def build_stars_index():
    if pd is None: return None
    xlsxs = list((ROOT/"corpus"/"_sources").glob("*.xlsx"))
    if not xlsxs: return None
    try:
        df = pd.read_excel(xlsxs[0], sheet_name=0)
    except Exception:
        return None
    cols = {c.lower().strip(): c for c in df.columns if isinstance(c, str)}
    def pick(*names):
        for n in names:
            if n in cols: return cols[n]
        return None
    c_racs = pick("racs id","racs","racs code")
    c_over = pick("overall star rating","overall rating")
    c_clin = pick("staffing rating","clinical star rating","clinical rating")
    c_comp = pick("compliance rating","compliance")
    if not c_racs: return None
    idx = {}
    for _, row in df.iterrows():
        rid = str(row[c_racs]).strip().lower().replace(" ","") if c_racs in row else ""
        if not rid: continue
        def num(x):
            try:
                f=float(x)
                return f if f==f else None
            except: return None
        idx[rid] = {
            "star_overall": num(row[c_over]) if c_over in row else None,
            "star_clinical":num(row[c_clin]) if c_clin in row else None,
            "star_compliance":num(row[c_comp]) if c_comp in row else None
        }
    return {"file": str(xlsxs[0].relative_to(ROOT)), "map": idx}

def verify_stars(pid: str, reg_row: dict, stars_index):
    claim = {k: reg_row.get(k) for k in ("star_overall","star_clinical","star_compliance")}
    if not stars_index:
        return {"provider_id":pid,"subject":"stars","status":"unknown","confidence":0.2,
                "claim": claim, "evidence":{"file":"corpus/_sources"}}
    rid = reg_row.get("provider_id","").replace("racs_","").strip().lower().replace(" ","")
    row = stars_index["map"].get(rid)
    if not row:
        return {"provider_id":pid,"subject":"stars","status":"unknown","confidence":0.2,
                "claim": claim, "evidence":{"file":stars_index["file"]}}
    same = (row.get("star_overall")==claim.get("star_overall") and
            row.get("star_clinical")==claim.get("star_clinical") and
            row.get("star_compliance")==claim.get("star_compliance"))
    return {"provider_id":pid,"subject":"stars","status":"pass" if same else "fail",
            "confidence":0.9 if same else 0.5,
            "claim": claim, "evidence":{"file":stars_index["file"]}}

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="verify only these provider_ids (e.g., racs_160)")
    args = ap.parse_args()

    reg = read_registry()
    only = set([x.strip() for x in (args.only or [])])
    stars_index = build_stars_index()
    out_lines = []

    for r in reg:
        pid = r.get("provider_id")
        if only and pid not in only:
            continue
        if pid is None:
            continue
        cdir = SRC_DIR/pid
        if not cdir.exists(): 
            continue
        out_lines.append(verify_pricing(pid, r.get("rad"), r.get("mpir"), cdir))
        out_lines.append(verify_compliance(pid, cdir))
        out_lines.append(verify_stars(pid, r, stars_index))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as w:
        for row in out_lines:
            row["observed_at"] = iso_now()
            w.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",",":"))+"\n")
    print(f"Wrote {len(out_lines)} assertion lines -> {OUT_PATH}")

if __name__ == "__main__":
    main()
