import json, subprocess, sys
from pathlib import Path
from jsonschema import validate
ROOT = Path(__file__).resolve().parents[1]
def test_schema_validity():
    providers=json.loads((ROOT/'registry'/'providers.json').read_text())
    providers_schema=json.loads((ROOT/'schemas'/'providers.schema.json').read_text())
    validate(providers, providers_schema)
    subprocess.check_call([sys.executable,'-m','cli.ingest'], cwd=ROOT)
    subprocess.check_call([sys.executable,'-m','cli.score'], cwd=ROOT)
    top5=json.loads((ROOT/'rankings'/'top5.json').read_text())
    top5_schema=json.loads((ROOT/'schemas'/'top5.schema.json').read_text())
    validate(top5, top5_schema)
    event_schema=json.loads((ROOT/'schemas'/'event.schema.json').read_text())
    for ln in (ROOT/'receipts'/'events.jsonl').read_text().splitlines():
        if ln.strip(): validate(json.loads(ln), event_schema)
