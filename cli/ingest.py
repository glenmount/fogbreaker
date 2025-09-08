import json
from pathlib import Path
from .common import sha256_file
ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT/'corpus'
RECEIPTS = ROOT/'receipts'/'events.jsonl'
FIXED_OBSERVED = '2025-09-08T00:00:00Z'
def main():
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for provider_dir in sorted(CORPUS.glob('*')):
        if not provider_dir.is_dir(): continue
        provider_id = provider_dir.name
        for f in sorted(provider_dir.glob('*')):
            if f.is_file():
                sha = sha256_file(f); size = f.stat().st_size
                evt = {"observed_at":FIXED_OBSERVED,"kind":"doc_ingest","provider_id":provider_id,
                       "source":{"filename":str(f.relative_to(ROOT))},"sha256":sha,"size_bytes":size}
                lines.append(json.dumps(evt, sort_keys=True, separators=(',', ':')))
    RECEIPTS.write_text('\n'.join(lines) + ('\n' if lines else ''), encoding='utf-8')
if __name__ == '__main__': main()
