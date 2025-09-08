import json, hashlib
from pathlib import Path
from .common import write_json
ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = ROOT/'receipts'/'events.jsonl'
LEDGER = ROOT/'ledger'
def main():
    if not RECEIPTS.exists(): return
    lines=[l for l in RECEIPTS.read_text(encoding='utf-8').splitlines() if l.strip()]
    if not lines: return
    latest_obs='2025-09-08T00:00:00Z'
    for ln in lines:
        evt=json.loads(ln); ts=evt.get('observed_at') or latest_obs
        if ts>latest_obs: latest_obs=ts
    date=latest_obs.split('T')[0]
    h=hashlib.sha256()
    for ln in sorted(lines): h.update((ln+'\n').encode('utf-8'))
    out={'date':date,'events_count':len(lines),'inputs_digest':h.hexdigest()}
    LEDGER.mkdir(parents=True, exist_ok=True); write_json(LEDGER/f'digest-{date}.json', out)
if __name__ == '__main__': main()
