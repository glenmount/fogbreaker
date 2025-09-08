import json
from pathlib import Path

def w(p, s):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def j(p, o):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, sort_keys=True, ensure_ascii=False, separators=(",",":")), encoding="utf-8")

# .gitignore
w(".gitignore", "__pycache__/\n.pytest_cache/\n.venv/\n.DS_Store\n*.pyc\n*.pyo\n*.swp\n")

# README (no backticks)
w("README.md",
"# Fogbreaker (Residential First)\n\n"
"Clear the fog so families can find the best provider for them, fast, with proof—not pitch.\n\n"
"Quick start:\n"
"1) python -m venv .venv && source .venv/bin/activate\n"
"2) pip install -r requirements.txt\n"
"3) make all\n"
"4) pytest -q\n\n"
"Layout: corpus/ registry/ receipts/ ledger/ rankings/ schemas/ cli/ web/ qa/goldens/\n"
)

# requirements
w("requirements.txt", "jsonschema==4.23.0\npytest==8.3.2\npytest-socket==0.7.0\n")

# schemas
j("schemas/providers.schema.json", {
  "$schema":"https://json-schema.org/draft/2020-12/schema","title":"providers","type":"array",
  "items":{"type":"object","required":["provider_id","name","postcode"],
    "properties":{"provider_id":{"type":"string"},"name":{"type":"string"},
      "address":{"type":"string"},"suburb":{"type":"string"},"postcode":{"type":["string","number"]},
      "lat":{"type":["number","null"]},"lng":{"type":["number","null"]},
      "star_overall":{"type":["number","null"]},"star_clinical":{"type":["number","null"]},
      "star_compliance":{"type":["number","null"]},"tags":{"type":"array","items":{"type":"string"}},
      "price_per_day":{"type":["number","null"]},"rad":{"type":["number","null"]},"mpir":{"type":["number","null"]}},
    "additionalProperties": True}})
j("schemas/event.schema.json", {
  "$schema":"https://json-schema.org/draft/2020-12/schema","title":"event","type":"object",
  "required":["observed_at","kind","sha256","size_bytes"],
  "properties":{"observed_at":{"type":"string"},"kind":{"type":"string","enum":["doc_ingest","score_run"]},
    "provider_id":{"type":["string","null"]},"source":{"type":["object","null"]},
    "sha256":{"type":"string"},"size_bytes":{"type":"integer"}},
  "additionalProperties": True})
j("schemas/top5.schema.json", {
  "$schema":"https://json-schema.org/draft/2020-12/schema","title":"top5","type":"object",
  "required":["query","preset","generated_at","items"],
  "properties":{
    "query":{"type":"object","required":["postcode","radius_km","budget_per_day","needs"],
      "properties":{"postcode":{"type":["string","number"]},"radius_km":{"type":"number"},
        "budget_per_day":{"type":"number"},"needs":{"type":"array","items":{"type":"string"}}}},
    "preset":{"type":"string"},"generated_at":{"type":"string"},
    "items":{"type":"array","minItems":1,"items":{
      "type":"object","required":["provider_id","fit_score","components","receipts"],
      "properties":{"provider_id":{"type":"string"},"fit_score":{"type":"number"},
        "components":{"type":"object","required":["location","price","quality","needs"],
          "properties":{"location":{"type":"number"},"price":{"type":"number"},
            "quality":{"type":"number"},"needs":{"type":"number"}},
          "additionalProperties": False},
        "receipts":{"type":"array","items":{"type":"object"}}},
      "additionalProperties": True}}},
  "additionalProperties": True})

# config
j("config/presets/balanced.json", {"w_location":0.30,"w_price":0.30,"w_quality":0.30,"w_needs":0.10})
j("config/query_canned.json", {"postcode":"2000","radius_km":20.0,"budget_per_day":90.0,"needs":["memory_support"]})

# registry (stub)
j("registry/providers.json", [
  {"provider_id":"prov_demo_1","name":"Demo Care Home A","address":"1 Demo St","suburb":"Sydney","postcode":"2000","lat":-33.8688,"lng":151.2093,"star_overall":4.2,"star_clinical":4.0,"star_compliance":4.5,"tags":["memory_support","secure_unit"],"price_per_day":85.0,"rad":500000.0,"mpir":8.36},
  {"provider_id":"prov_demo_2","name":"Harbour View Lodge","address":"7 Foreshore Ave","suburb":"Neutral Bay","postcode":"2089","lat":-33.8381,"lng":151.2230,"star_overall":3.9,"star_clinical":3.8,"star_compliance":4.1,"tags":["palliative"],"price_per_day":95.0,"rad":450000.0,"mpir":8.36}
])

# corpus placeholders
w("corpus/prov_demo_1/pricing.txt","RAD: 500000\nMPIR: 8.36\n")
w("corpus/prov_demo_1/stars.txt","Stars Overall: 4.2\n")
w("corpus/prov_demo_1/complaints.txt","Complaints: none\n")
w("corpus/prov_demo_2/pricing.txt","RAD: 450000\nMPIR: 8.36\n")
w("corpus/prov_demo_2/stars.txt","Stars Overall: 3.9\n")
w("corpus/prov_demo_2/complaints.txt","Complaints: minor\n")

# cli
w("cli/__init__.py","")
w("cli/common.py",
"import json, hashlib, math, datetime\n"
"from pathlib import Path\n"
"def sha256_file(path: Path) -> str:\n"
"    h = hashlib.sha256()\n"
"    with open(path, 'rb') as f:\n"
"        for chunk in iter(lambda: f.read(8192), b''):\n"
"            h.update(chunk)\n"
"    return h.hexdigest()\n"
"def write_json(path: Path, obj):\n"
"    path.parent.mkdir(parents=True, exist_ok=True)\n"
"    with open(path, 'w', encoding='utf-8') as f:\n"
"        json.dump(obj, f, sort_keys=True, ensure_ascii=False, separators=(',', ':'))\n"
"def read_json(path: Path):\n"
"    with open(path, 'r', encoding='utf-8') as f:\n"
"        return json.load(f)\n"
"def iso_z(dt: datetime.datetime) -> str:\n"
"    return dt.replace(microsecond=0, tzinfo=datetime.timezone.utc).isoformat().replace('+00:00','Z')\n"
"def haversine_km(lat1, lon1, lat2, lon2):\n"
"    R = 6371.0\n"
"    phi1, phi2 = math.radians(lat1), math.radians(lat2)\n"
"    dphi = math.radians(lat2 - lat1)\n"
"    dlambda = math.radians(lon2 - lon1)\n"
"    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2\n"
"    c = 2*math.atan2(math.sqrt(1-a), math.sqrt(a))\n"
"    return R*c\n"
)
w("cli/fee_math.py",
"from decimal import Decimal, ROUND_HALF_UP, getcontext\n"
"getcontext().prec = 28\n"
"def dap_from_rad(rad: float, mpir_percent: float) -> float:\n"
"    RAD = Decimal(str(rad)); MPIR = Decimal(str(mpir_percent)) / Decimal('100')\n"
"    per_day = (RAD * MPIR) / Decimal('365')\n"
"    cents = per_day.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)\n"
"    return float(cents)\n"
)
w("cli/ingest.py",
"import json\nfrom pathlib import Path\nfrom .common import sha256_file\n"
"ROOT = Path(__file__).resolve().parents[1]\n"
"CORPUS = ROOT/'corpus'\n"
"RECEIPTS = ROOT/'receipts'/'events.jsonl'\n"
"FIXED_OBSERVED = '2025-09-08T00:00:00Z'\n"
"def main():\n"
"    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)\n"
"    lines = []\n"
"    for provider_dir in sorted(CORPUS.glob('*')):\n"
"        if not provider_dir.is_dir(): continue\n"
"        provider_id = provider_dir.name\n"
"        for f in sorted(provider_dir.glob('*')):\n"
"            if f.is_file():\n"
"                sha = sha256_file(f); size = f.stat().st_size\n"
"                evt = {\"observed_at\":FIXED_OBSERVED,\"kind\":\"doc_ingest\",\"provider_id\":provider_id,\n"
"                       \"source\":{\"filename\":str(f.relative_to(ROOT))},\"sha256\":sha,\"size_bytes\":size}\n"
"                lines.append(json.dumps(evt, sort_keys=True, separators=(',', ':')))\n"
"    RECEIPTS.write_text('\\n'.join(lines) + ('\\n' if lines else ''), encoding='utf-8')\n"
"if __name__ == '__main__': main()\n"
)
w("cli/score.py",
"import json\nfrom pathlib import Path\nfrom .common import write_json, read_json, haversine_km, sha256_file\nfrom .fee_math import dap_from_rad\n"
"ROOT = Path(__file__).resolve().parents[1]\n"
"RECEIPTS = ROOT/'receipts'/'events.jsonl'\n"
"RANKINGS = ROOT/'rankings'/'top5.json'\n"
"def clamp01(x): return max(0.0, min(1.0, x))\n"
"def main():\n"
"    providers = read_json(ROOT/'registry'/'providers.json')\n"
"    weights = read_json(ROOT/'config'/'presets'/'balanced.json')\n"
"    query = read_json(ROOT/'config'/'query_canned.json')\n"
"    receipts_by_provider, latest_obs = {}, None\n"
"    if RECEIPTS.exists():\n"
"        for line in RECEIPTS.read_text(encoding='utf-8').strip().splitlines():\n"
"            if not line.strip(): continue\n"
"            evt = json.loads(line); pid = evt.get('provider_id')\n"
"            if pid: receipts_by_provider.setdefault(pid, []).append(evt)\n"
"            ts = evt.get('observed_at'); \n"
"            if ts: latest_obs = max(latest_obs, ts) if latest_obs else ts\n"
"    origin = {\"lat\": -33.8688, \"lng\": 151.2093}\n"
"    radius_km = float(query['radius_km']); budget = float(query['budget_per_day'])\n"
"    needs = set(query.get('needs', []))\n"
"    scored = []\n"
"    for p in providers:\n"
"        lat, lng = p.get('lat'), p.get('lng')\n"
"        if lat is None or lng is None: continue\n"
"        d_km = haversine_km(origin['lat'], origin['lng'], float(lat), float(lng))\n"
"        loc = 1.0 - clamp01(d_km / radius_km)\n"
"        price_pd = p.get('price_per_day')\n"
"        if price_pd is None and (p.get('rad') is not None and p.get('mpir') is not None):\n"
"            price_pd = dap_from_rad(p['rad'], p['mpir'])\n"
"        if price_pd is None: continue\n"
"        price = 1.0 if price_pd <= budget else clamp01(1.0 - ((price_pd - budget) / max(budget, 1.0)))\n"
"        qual = (float(p.get('star_overall') or 0.0) / 5.0)\n"
"        need_hit = 1.0 if any(tag in needs for tag in p.get('tags', [])) else 0.0\n"
"        fit = (weights['w_location']*loc + weights['w_price']*price + weights['w_quality']*qual + weights['w_needs']*need_hit)\n"
"        scored.append({\"provider_id\":p['provider_id'],\"fit_score\":round(fit,6),\n"
"                      \"components\":{\"location\":round(loc,6),\"price\":round(price,6),\"quality\":round(qual,6),\"needs\":round(need_hit,6)},\n"
"                      \"receipts\":receipts_by_provider.get(p['provider_id'],[])})\n"
"    scored.sort(key=lambda x:(-x['fit_score'], x['provider_id']))\n"
"    out = {\"query\":query,\"preset\":\"Balanced\",\"generated_at\":latest_obs or \"2025-09-08T00:00:00Z\",\"items\":scored[:5]}\n"
"    write_json(RANKINGS, out)\n"
"    evt = {\"observed_at\":out[\"generated_at\"],\"kind\":\"score_run\",\"provider_id\":None,\n"
"           \"source\":{\"filename\":str(RANKINGS.relative_to(ROOT))},\"sha256\":sha256_file(RANKINGS),\"size_bytes\":RANKINGS.stat().st_size}\n"
"    lines=[]\n"
"    if RECEIPTS.exists(): lines=[l for l in RECEIPTS.read_text(encoding='utf-8').splitlines() if l.strip()]\n"
"    import json as _j; lines.append(_j.dumps(evt, sort_keys=True, separators=(',', ':')))\n"
"    lines=sorted(lines); RECEIPTS.parent.mkdir(parents=True, exist_ok=True)\n"
"    RECEIPTS.write_text('\\n'.join(lines)+'\\n', encoding='utf-8')\n"
"if __name__ == '__main__': main()\n"
)
w("cli/digest.py",
"import json, hashlib\nfrom pathlib import Path\nfrom .common import write_json\n"
"ROOT = Path(__file__).resolve().parents[1]\n"
"RECEIPTS = ROOT/'receipts'/'events.jsonl'\n"
"LEDGER = ROOT/'ledger'\n"
"def main():\n"
"    if not RECEIPTS.exists(): return\n"
"    lines=[l for l in RECEIPTS.read_text(encoding='utf-8').splitlines() if l.strip()]\n"
"    if not lines: return\n"
"    latest_obs='2025-09-08T00:00:00Z'\n"
"    for ln in lines:\n"
"        evt=json.loads(ln); ts=evt.get('observed_at') or latest_obs\n"
"        if ts>latest_obs: latest_obs=ts\n"
"    date=latest_obs.split('T')[0]\n"
"    h=hashlib.sha256()\n"
"    for ln in sorted(lines): h.update((ln+'\\n').encode('utf-8'))\n"
"    out={'date':date,'events_count':len(lines),'inputs_digest':h.hexdigest()}\n"
"    LEDGER.mkdir(parents=True, exist_ok=True); write_json(LEDGER/f'digest-{date}.json', out)\n"
"if __name__ == '__main__': main()\n"
)

# web
w("web/index.html","<!doctype html><html><body><h1>Fogbreaker — Top-5</h1><script>fetch('../rankings/top5.json').then(r=>r.json()).then(d=>document.body.insertAdjacentHTML('beforeend','<pre>'+JSON.stringify(d,null,2)+'</pre>'));</script></body></html>\n")

# Makefile
w("Makefile",".PHONY: all ingest score digest clean\nall: ingest score digest\ningest:\n\tpython -m cli.ingest\nscore:\n\tpython -m cli.score\ndigest:\n\tpython -m cli.digest\nclean:\n\trm -f receipts/events.jsonl\n\trm -f rankings/top5.json\n\trm -rf ledger\n")

# tests
w("tests/test_determinism.py",
"import hashlib, subprocess, sys\nfrom pathlib import Path\nROOT = Path(__file__).resolve().parents[1]; PY=sys.executable\n"
"def filehash(p: Path):\n"
"    h=hashlib.sha256(); f=open(p,'rb')\n"
"    for chunk in iter(lambda:f.read(8192), b''): h.update(chunk)\n"
"    f.close(); return h.hexdigest()\n"
"def test_determinism_twice():\n"
"    subprocess.check_call([PY,'-m','cli.ingest'], cwd=ROOT)\n"
"    subprocess.check_call([PY,'-m','cli.score'], cwd=ROOT)\n"
"    subprocess.check_call([PY,'-m','cli.digest'], cwd=ROOT)\n"
"    h1e=filehash(ROOT/'receipts'/'events.jsonl'); h1t=filehash(ROOT/'rankings'/'top5.json')\n"
"    d1=next((ROOT/'ledger').glob('digest-*.json')).read_text()\n"
"    subprocess.check_call([PY,'-m','cli.ingest'], cwd=ROOT)\n"
"    subprocess.check_call([PY,'-m','cli.score'], cwd=ROOT)\n"
"    subprocess.check_call([PY,'-m','cli.digest'], cwd=ROOT)\n"
"    h2e=filehash(ROOT/'receipts'/'events.jsonl'); h2t=filehash(ROOT/'rankings'/'top5.json')\n"
"    d2=next((ROOT/'ledger').glob('digest-*.json')).read_text()\n"
"    assert (h1e,h1t,d1)==(h2e,h2t,d2)\n"
)
w("tests/test_schemas.py",
"import json, subprocess, sys\nfrom pathlib import Path\nfrom jsonschema import validate\nROOT = Path(__file__).resolve().parents[1]\n"
"def test_schema_validity():\n"
"    providers=json.loads((ROOT/'registry'/'providers.json').read_text())\n"
"    providers_schema=json.loads((ROOT/'schemas'/'providers.schema.json').read_text())\n"
"    validate(providers, providers_schema)\n"
"    subprocess.check_call([sys.executable,'-m','cli.ingest'], cwd=ROOT)\n"
"    subprocess.check_call([sys.executable,'-m','cli.score'], cwd=ROOT)\n"
"    top5=json.loads((ROOT/'rankings'/'top5.json').read_text())\n"
"    top5_schema=json.loads((ROOT/'schemas'/'top5.schema.json').read_text())\n"
"    validate(top5, top5_schema)\n"
"    event_schema=json.loads((ROOT/'schemas'/'event.schema.json').read_text())\n"
"    for ln in (ROOT/'receipts'/'events.jsonl').read_text().splitlines():\n"
"        if ln.strip(): validate(json.loads(ln), event_schema)\n"
)
w("tests/test_three_questions.py",
"import json, subprocess, sys\nfrom pathlib import Path\nROOT = Path(__file__).resolve().parents[1]\n"
"def test_three_question_guarantee():\n"
"    subprocess.check_call([sys.executable,'-m','cli.ingest'], cwd=ROOT)\n"
"    subprocess.check_call([sys.executable,'-m','cli.score'], cwd=ROOT)\n"
"    data=json.loads((ROOT/'rankings'/'top5.json').read_text())\n"
"    assert data.get('items') and len(data['items'])>=1\n"
"    for it in data['items']:\n"
"        assert 'components' in it and all(k in it['components'] for k in ('location','price','quality','needs'))\n"
"        assert isinstance(it.get('receipts',[]), list)\n"
)
w("tests/test_no_network.py","import pytest, socket\n\ndef test_network_blocked():\n    with pytest.raises(Exception):\n        socket.create_connection(('example.com',80),timeout=1)\n")
# CI
w(".github/workflows/ci.yml",
"name: ci\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.11'\n      - name: Install deps\n        run: |\n          python -m pip install --upgrade pip\n          pip install -r requirements.txt\n      - name: Build artifacts\n        run: make all\n      - name: Run tests\n        run: pytest -q\n")
print("Scaffold written.")
