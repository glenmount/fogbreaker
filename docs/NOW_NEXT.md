# Fogbreaker — NOW / NEXT Tracker

> Canonical, auto-updated status for the Fogbreaker build.

## North Star (why & scope)
- **Goal:** Help families find the right residential provider, fast, with proof — not pitch.
- **Must answer:** Top-5 near me • What will it cost (RAD/DAP) • Show your sources.
- **Non-negotiables:** receipts-first • deterministic • no network in scoring • explainable ranking.

## Scoreboard (auto-updated)
| Metric | Target | Current |
|---|---:|---:|
| Providers in registry | — | 2523 |
| Providers with any docs in `corpus/` | — | 0 |
| Receipts (events.jsonl lines) | — | 7 |
| Top-5 last generated at | — | 2025-09-08T00:00:00Z |
| Missing overall star ratings | ↓ | 90 |
| Missing clinical ratings | ↓ | 59 |
| Missing compliance ratings | ↓ | 48 |

## What’s built (kept green in CI)
- End-to-end: **ingest → score → digest**, receipts written; deterministic tests pass.
- Minimal viewer (`web/index.html`) shows Top-5 + receipts.
- Branch protection: required CI + review + conversation resolution; auto-merge available.

## What’s next (Phase-1)
- **DoD:** ≥50 Sydney providers with ≥2 receipts each; ≥30 with fee-math receipts; public demo page; CI green.
- **This week:** ingest 10 real providers (pricing + stars/complaints); evidence badges in viewer; publish Pages from `/docs`.
- **Next:** scale to 30–40 providers; RAG-lite citations over local corpus; canned postcode queries.

## Help Cards (open small tasks)
- [ ] JSONL validator for `receipts/events.jsonl` (scripts/validate_events.py; CI target `make validate`).
- [ ] Postcode centroid fallback (config/postcode_centroids.json + scoring hook).
- [ ] Fee-math receipt writer when pricing exists (extend schema + tests).

## Document pack (per provider) — reference
Must-have: **pricing**, **star ratings snapshot**, **compliance snapshot**. Strong-should-have: residents’ experience, staffing minutes, quality measures, dementia/palliative page, fees/complaints/privacy policies, admissions info.
(Names like: `20250908__pricing__example.org.pdf`)

## Decision log (append entries)
- 2025-09-08: Neutral defaults for missing price/quality; never-empty Top-5 to prevent empty UI.

