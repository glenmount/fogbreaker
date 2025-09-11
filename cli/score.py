import json
from pathlib import Path
from .common import write_json, read_json, haversine_km, sha256_file
from .fee_math import dap_from_rad

ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = ROOT / "receipts" / "events.jsonl"
RANKINGS = ROOT / "rankings" / "top5.json"

def clamp01(x): 
    return max(0.0, min(1.0, x))

def main():
    # Inputs
    providers = read_json(ROOT / "registry" / "providers.json")
    weights   = read_json(ROOT / "config" / "presets" / "balanced.json")
    query     = read_json(ROOT / "config" / "query_canned.json")

    # Receipts map + latest observed
    receipts_by_provider = {}
    latest_obs = None
    if RECEIPTS.exists():
        lines = [l for l in RECEIPTS.read_text(encoding="utf-8").splitlines() if l.strip()]
        for line in lines:
            evt = json.loads(line)
            pid = evt.get("provider_id")
            if pid:
                receipts_by_provider.setdefault(pid, []).append(evt)
            ts = evt.get("observed_at")
            if ts:
                latest_obs = max(latest_obs, ts) if latest_obs else ts

    # Origin (Phase-1 canned)
    origin = {"lat": -33.8688, "lng": 151.2093}
    radius_km = float(query.get("radius_km", 20.0))
    budget    = float(query.get("budget_per_day", 100.0))
    needs     = set(query.get("needs", []))

    scored = []
    if isinstance(providers, list):
        for p in providers:
            # Location
            lat, lng = p.get("lat"), p.get("lng")
            if lat is None or lng is None:
                loc = 0.0
            else:
                d_km = haversine_km(origin["lat"], origin["lng"], float(lat), float(lng))
                loc  = 1.0 - clamp01(d_km / max(radius_km, 0.1))

            # Price: explicit → compute; RAD/MPIR → compute; else neutral 0.5
            price_pd = p.get("price_per_day")
            if price_pd is None and (p.get("rad") is not None and p.get("mpir") is not None):
                try:
                    price_pd = dap_from_rad(p["rad"], p["mpir"])
                except Exception:
                    price_pd = None
            price = 0.5 if price_pd is None else (1.0 if price_pd <= budget else clamp01(1.0 - ((price_pd - budget) / max(budget, 1.0))))

            # Quality: neutral 0.5 when missing
            s_over = p.get("star_overall")
            qual   = 0.5 if s_over is None else clamp01(float(s_over) / 5.0)

            # Needs: 1.0 if any tag matches; else 0.0
            tags = p.get("tags") or []
            need_hit = 1.0 if any(tag in needs for tag in tags) else 0.0

            fit = (
                weights["w_location"] * loc +
                weights["w_price"]    * price +
                weights["w_quality"]  * qual +
                weights["w_needs"]    * need_hit
            )

            scored.append({
                "provider_id": p.get("provider_id", "unknown"),
                "fit_score": round(fit, 6),
                "components": {
                    "location": round(loc,   6),
                    "price":    round(price, 6),
                    "quality":  round(qual,  6),
                    "needs":    round(need_hit, 6),
                    "distance_km": round(d_km if "d_km" in locals() else 0.0, 3)
                },
                "receipts": receipts_by_provider.get(p.get("provider_id", ""), [])
            })

    # Hard fallback: if nothing scored, fabricate neutral Top-5 from first rows
    if not scored and isinstance(providers, list):
        for rp in providers[:5]:
            scored.append({
                "provider_id": rp.get("provider_id", "unknown"),
                "fit_score": 0.5,
                "components": {"location":0.5,"price":0.5,"quality":0.5,"needs":0.0},
                "receipts": []
            })

    scored.sort(key=lambda x: (-x["fit_score"], x["provider_id"]))
    items = scored[:5]

    out = {
        "query": query,
        "preset": "Balanced",
        "generated_at": latest_obs or "2025-09-08T00:00:00Z",
        "items": items
    }
    write_json(RANKINGS, out)

    # Append deterministic score_run receipt
    evt = {
        "observed_at": out["generated_at"],
        "kind": "score_run",
        "provider_id": None,
        "source": {"filename": str(RANKINGS.relative_to(ROOT))},
        "sha256": sha256_file(RANKINGS),
        "size_bytes": RANKINGS.stat().st_size
    }
    lines = []
    if RECEIPTS.exists():
        lines = [l for l in RECEIPTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    import json as _json
    lines.append(_json.dumps(evt, sort_keys=True, separators=(",", ":")))
    lines = sorted(lines)
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    RECEIPTS.write_text("\n".join(lines) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
