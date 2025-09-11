#!/usr/bin/env python3
"""
Rank providers deterministically using receipts + registry.

Locked decisions (11 Sep 2025):
- Stars: use registry `star_overall` (float 1–5), clamp 1..5, default 3.0.
- Compliance v1: PASS if compliance receipt exists; else PASS if any *compliance*.pdf exists in corpus.
- Distance: use provider lat/lon (or latitude/longitude/lng) else no penalty; CBD kept as constant.
- MPIR: default 7.78 unless provider.mpir is set.
- DAP: RAD × (MPIR/100) ÷ 365, Decimal HALF_UP to cents.
Outputs: rankings/top10.json (with human 'reasons'), rankings/why.jsonl
"""
import json, math, pathlib, re, sys
from decimal import Decimal, ROUND_HALF_UP

# --- constants ---
MPIR_DEFAULT = 7.78
CBD = (-33.8688, 151.2093)  # Sydney CBD centroid

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "providers.json"
ASSERTIONS = ROOT / "receipts" / "assertions.jsonl"
CORPUS = ROOT / "corpus"
RANKINGS_DIR = ROOT / "rankings"
RANKINGS_DIR.mkdir(exist_ok=True)

def safe_float(x, fallback=None):
    try:
        return float(x)
    except Exception:
        return fallback

def load_registry():
    with open(REGISTRY, "r") as f:
        data = json.load(f)
    return data["providers"] if isinstance(data, dict) and "providers" in data else data

def load_assertions():
    pricing_ids, compliance_ids, dap_values = set(), set(), {}
    if ASSERTIONS.exists():
        with open(ASSERTIONS, "r") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                pid = rec.get("provider_id")
                if not pid: continue
                subj = (rec.get("subject") or rec.get("type") or "").lower()
                if "pricing" in subj:
                    pricing_ids.add(pid)
                    claim = rec.get("claim") or {}
                    if "dap" in claim:
                        v = safe_float(claim["dap"])
                        if v is not None: dap_values[pid] = v
                if "compliance" in subj:
                    compliance_ids.add(pid)
    return pricing_ids, compliance_ids, dap_values

def any_compliance_pdf(provider_id: str) -> bool:
    pdir = CORPUS / provider_id
    if not pdir.is_dir(): return False
    pat = re.compile(r"compliance", re.I)
    # rglob covers nested; cheap enough at our scale
    for p in pdir.rglob("*.pdf"):
        if pat.search(p.name):
            return True
    return False

def compute_dap(rad, mpir):
    if rad is None or mpir is None:
        return None
    RAD = Decimal(str(rad))
    MPIR = Decimal(str(mpir))
    dap = (RAD * (MPIR / Decimal("100"))) / Decimal("365")
    return float(dap.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    to_rad = math.radians
    dlat, dlon = to_rad(lat2 - lat1), to_rad(lon2 - lon1)
    a = (math.sin(dlat/2)**2
         + math.cos(to_rad(lat1)) * math.cos(to_rad(lat2)) * math.sin(dlon/2)**2)
    return 2 * R * math.asin(math.sqrt(a))

def get_distance_km(p):
    lat = p.get("lat") or p.get("latitude")
    lon = p.get("lon") or p.get("lng") or p.get("longitude")
    if lat is None or lon is None:
        return None
    try:
        return haversine_km(CBD[0], CBD[1], float(lat), float(lon))
    except Exception:
        return None

def build_reasons(r):
    parts = []
    if r["dap"] is not None: parts.append(f"DAP ${r['dap']:.2f}")
    parts.append(f"{r['stars']}★ overall")
    parts.append("compliance ✓" if r["compliance_present"] else "compliance ✗")
    if r["distance_km"] is not None: parts.append(f"{r['distance_km']:.1f} km from CBD")
    return " • ".join(parts)

def main():
    registry = load_registry()
    _pricing_ids, compliance_ids, dap_values = load_assertions()

    rows = []
    for p in registry:
        pid = p.get("id") or p.get("provider_id") or p.get("code")
        if not pid: continue

        rad = safe_float(p.get("rad"))
        mpir = safe_float(p.get("mpir"), MPIR_DEFAULT)
        dap = dap_values.get(pid) or compute_dap(rad, mpir)

        stars = safe_float(p.get("star_overall"), 3.0)
        # clamp defensively
        stars = min(5.0, max(1.0, stars))

        has_compliance = (pid in compliance_ids) or any_compliance_pdf(pid)
        distance_km = get_distance_km(p)

        rows.append({
            "provider_id": pid,
            "name": p.get("name") or p.get("provider_name"),
            "dap": dap,
            "stars": stars,
            "compliance_present": bool(has_compliance),
            "distance_km": distance_km,
        })

    # price rank among those with DAP
    priced = [r for r in rows if r["dap"] is not None]
    priced.sort(key=lambda r: r["dap"])
    price_rank = {r["provider_id"]: i+1 for i, r in enumerate(priced)}

    ranked = []
    for r in rows:
        score = 100.0
        pr = price_rank.get(r["provider_id"])
        if pr: score -= 4 * pr
        score += (float(r["stars"]) - 3.0) * 5
        if not r["compliance_present"]: score -= 10
        if r["distance_km"] is not None: score -= min(10.0, r["distance_km"] / 3.0)
        out = dict(r)
        out["score"] = round(score, 2)
        ranked.append(out)

    # stable sort: score desc, then DAP asc (None at end)
    ranked.sort(key=lambda r: (r["score"], -(1e12 if r["dap"] is None else -r["dap"])), reverse=True)
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
        r["reasons"] = build_reasons(r)

    with open(RANKINGS_DIR / "top10.json", "w") as f:
        json.dump(ranked[:10], f, indent=2)

    with open(RANKINGS_DIR / "why.jsonl", "w") as f:
        for r in ranked:
            f.write(json.dumps({
                "provider_id": r["provider_id"],
                "name": r.get("name"),
                "rank": r["rank"],
                "score": r["score"],
                "dap": r["dap"],
                "stars": r["stars"],
                "compliance_present": r["compliance_present"],
                "distance_km": r["distance_km"],
                "reasons": r["reasons"],
            }) + "\n")

    print("✅ Wrote rankings/top10.json and rankings/why.jsonl")

if __name__ == "__main__":
    sys.exit(main())
