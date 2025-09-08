import json
from pathlib import Path
from .common import write_json, read_json, haversine_km, sha256_file
from .fee_math import dap_from_rad
ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = ROOT/'receipts'/'events.jsonl'
RANKINGS = ROOT/'rankings'/'top5.json'
def clamp01(x): return max(0.0, min(1.0, x))
def main():
    providers = read_json(ROOT/'registry'/'providers.json')
    weights = read_json(ROOT/'config'/'presets'/'balanced.json')
    query = read_json(ROOT/'config'/'query_canned.json')
    receipts_by_provider, latest_obs = {}, None
    if RECEIPTS.exists():
        for line in RECEIPTS.read_text(encoding='utf-8').strip().splitlines():
            if not line.strip(): continue
            evt = json.loads(line); pid = evt.get('provider_id')
            if pid: receipts_by_provider.setdefault(pid, []).append(evt)
            ts = evt.get('observed_at'); 
            if ts: latest_obs = max(latest_obs, ts) if latest_obs else ts
    origin = {"lat": -33.8688, "lng": 151.2093}
    radius_km = float(query['radius_km']); budget = float(query['budget_per_day'])
    needs = set(query.get('needs', []))
    scored = []
    for p in providers:
        lat, lng = p.get('lat'), p.get('lng')
        if lat is None or lng is None: continue
        d_km = haversine_km(origin['lat'], origin['lng'], float(lat), float(lng))
        loc = 1.0 - clamp01(d_km / radius_km)
        price_pd = p.get('price_per_day')
        if price_pd is None and (p.get('rad') is not None and p.get('mpir') is not None):
            price_pd = dap_from_rad(p['rad'], p['mpir'])
        if price_pd is None: continue
        price = 1.0 if price_pd <= budget else clamp01(1.0 - ((price_pd - budget) / max(budget, 1.0)))
        qual = (float(p.get('star_overall') or 0.0) / 5.0)
        need_hit = 1.0 if any(tag in needs for tag in p.get('tags', [])) else 0.0
        fit = (weights['w_location']*loc + weights['w_price']*price + weights['w_quality']*qual + weights['w_needs']*need_hit)
        scored.append({"provider_id":p['provider_id'],"fit_score":round(fit,6),
                      "components":{"location":round(loc,6),"price":round(price,6),"quality":round(qual,6),"needs":round(need_hit,6)},
                      "receipts":receipts_by_provider.get(p['provider_id'],[])})
    scored.sort(key=lambda x:(-x['fit_score'], x['provider_id']))
    out = {"query":query,"preset":"Balanced","generated_at":latest_obs or "2025-09-08T00:00:00Z","items":scored[:5]}
    write_json(RANKINGS, out)
    evt = {"observed_at":out["generated_at"],"kind":"score_run","provider_id":None,
           "source":{"filename":str(RANKINGS.relative_to(ROOT))},"sha256":sha256_file(RANKINGS),"size_bytes":RANKINGS.stat().st_size}
    lines=[]
    if RECEIPTS.exists(): lines=[l for l in RECEIPTS.read_text(encoding='utf-8').splitlines() if l.strip()]
    import json as _j; lines.append(_j.dumps(evt, sort_keys=True, separators=(',', ':')))
    lines=sorted(lines); RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    RECEIPTS.write_text('\n'.join(lines)+'\n', encoding='utf-8')
if __name__ == '__main__': main()
