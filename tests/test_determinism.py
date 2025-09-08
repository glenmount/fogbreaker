import hashlib, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; PY=sys.executable
def filehash(p: Path):
    h=hashlib.sha256(); f=open(p,'rb')
    for chunk in iter(lambda:f.read(8192), b''): h.update(chunk)
    f.close(); return h.hexdigest()
def test_determinism_twice():
    subprocess.check_call([PY,'-m','cli.ingest'], cwd=ROOT)
    subprocess.check_call([PY,'-m','cli.score'], cwd=ROOT)
    subprocess.check_call([PY,'-m','cli.digest'], cwd=ROOT)
    h1e=filehash(ROOT/'receipts'/'events.jsonl'); h1t=filehash(ROOT/'rankings'/'top5.json')
    d1=next((ROOT/'ledger').glob('digest-*.json')).read_text()
    subprocess.check_call([PY,'-m','cli.ingest'], cwd=ROOT)
    subprocess.check_call([PY,'-m','cli.score'], cwd=ROOT)
    subprocess.check_call([PY,'-m','cli.digest'], cwd=ROOT)
    h2e=filehash(ROOT/'receipts'/'events.jsonl'); h2t=filehash(ROOT/'rankings'/'top5.json')
    d2=next((ROOT/'ledger').glob('digest-*.json')).read_text()
    assert (h1e,h1t,d1)==(h2e,h2t,d2)
