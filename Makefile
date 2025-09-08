.PHONY: all ingest score digest clean
all: ingest score digest
ingest:
	python -m cli.ingest
score:
	python -m cli.score
digest:
	python -m cli.digest
clean:
	rm -f receipts/events.jsonl
	rm -f rankings/top5.json
	rm -rf ledger

.PHONY: status
status:
	python scripts/update_status.py
