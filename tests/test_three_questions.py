import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def test_three_question_guarantee():
    subprocess.check_call([sys.executable,'-m','cli.ingest'], cwd=ROOT)
    subprocess.check_call([sys.executable,'-m','cli.score'], cwd=ROOT)
    data=json.loads((ROOT/'rankings'/'top5.json').read_text())
    assert data.get('items') and len(data['items'])>=1
    for it in data['items']:
        assert 'components' in it and all(k in it['components'] for k in ('location','price','quality','needs'))
        assert isinstance(it.get('receipts',[]), list)
