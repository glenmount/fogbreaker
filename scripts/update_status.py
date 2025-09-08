#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
reg = json.loads((ROOT/"registry"/"providers.json").read_text(encoding="utf-8"))
top5 = json.loads((ROOT/"rankings"/"top5.json").read_text(encoding="utf-8"))
evts = (ROOT/"receipts"/"events.jsonl").read_text(encoding="utf-8").splitlines()

registry_count = len(reg)
providers_with_docs = 0
corpus = ROOT/"corpus"
if corpus.exists():
    ids = {p.get("provider_id") for p in reg if p.get("provider_id")}
    for pid in ids:
        pdir = corpus/pid
        if pdir.exists():
            try:
                if any(pdir.iterdir()):
                    providers_with_docs += 1
            except Exception:
                pass

missing_overall    = sum(1 for p in reg if p.get("star_overall")    is None)
missing_clinical   = sum(1 for p in reg if p.get("star_clinical")   is None)
missing_compliance = sum(1 for p in reg if p.get("star_compliance") is None)
receipt_lines      = sum(1 for l in evts if l.strip())
top5_generated_at  = top5.get("generated_at","—")

tmpl = (ROOT/"docs"/"NOW_NEXT.md").read_text(encoding="utf-8")
for k,v in {
  "{{REGISTRY_COUNT}}": str(registry_count),
  "{{PROVIDERS_WITH_DOCS}}": str(providers_with_docs),
  "{{RECEIPT_LINES}}": str(receipt_lines),
  "{{TOP5_GENERATED_AT}}": top5_generated_at,
  "{{MISSING_OVERALL}}": str(missing_overall),
  "{{MISSING_CLINICAL}}": str(missing_clinical),
  "{{MISSING_COMPLIANCE}}": str(missing_compliance),
}.items():
    tmpl = tmpl.replace(k, v)

(Path(ROOT/"docs"/"NOW_NEXT.md")).write_text(tmpl, encoding="utf-8")
print("Updated NOW_NEXT.md")
