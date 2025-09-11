#!/usr/bin/env python3
import re, sys, json, argparse
from pathlib import Path
from pdfminer.high_level import extract_text
from math import floor

RAD_PATTERNS = [
    r"Maximum\s+refundable\s+deposit[^$\d]*(?:AUD\s*)?\$?\s*([\d,]+)",
    r"Max(?:imum)?\s+refundable\s+accommodation\s+deposit[^$\d]*(?:AUD\s*)?\$?\s*([\d,]+)",
    r"Refundable\s+accommodation\s+deposit\s*\(RAD\)[^$\d]*(?:AUD\s*)?\$?\s*([\d,]+)",
    r"Maximum\s+room\s+price[^$\d]*(?:AUD\s*)?\$?\s*([\d,]+)",  # some providers use this label
]
DAP_PATTERN = r"Maximum\s+daily\s+payments?[^$\d]*(?:AUD\s*)?\$?\s*([0-9][\d,]*\.\d{2})"

def find_numbers(patterns, text):
    vals = []
    for pat in ([patterns] if isinstance(patterns, str) else patterns):
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            raw = m.group(1).replace(",", "")
            try: vals.append(float(raw))
            except: pass
    return vals

def extract_from_pdf(pdf_path: Path):
    try:
        txt = extract_text(str(pdf_path)) or ""
    except Exception as e:
        return {"error": f"extract_failed: {e}"}
    rads = find_numbers(RAD_PATTERNS, txt)
    daps = find_numbers(DAP_PATTERN, txt)
    return {"rads": rads, "rads_max": (max(rads) if rads else None), "daps": daps}

def load_registry(reg_path: Path):
    with open(reg_path, "r") as f:
        reg = json.load(f)
    if isinstance(reg, dict) and "providers" in reg and isinstance(reg["providers"], list):
        return {"shape": "object", "providers": reg["providers"], "root": reg}
    elif isinstance(reg, list):
        return {"shape": "list", "providers": reg, "root": reg}
    else:
        raise ValueError("Unsupported registry shape")

def save_registry(reg_path: Path, ctx: dict):
    tmp = reg_path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(ctx["root"], f, indent=2, ensure_ascii=False); f.write("\n")
    tmp.replace(reg_path)

def set_provider_field(ctx, pid, field, value):
    updated = False
    for p in ctx["providers"]:
        if p.get("id") == pid:
            p[field] = value
            updated = True
    return updated

def main():
    ap = argparse.ArgumentParser(description="Extract RAD/DAP and stamp into registry (optional).")
    ap.add_argument("--registry", default="registry/providers.json")
    ap.add_argument("--apply", action="store_true", help="Write RAD/MPIR into registry")
    ap.add_argument("--mpir", type=float, default=None, help="MPIR to apply (e.g., 7.78)")
    ap.add_argument("--limit", nargs="*", help="Limit to provider IDs, e.g., racs_2710 racs_2713")
    ap.add_argument("--estimate-from-dap", action="store_true",
                    help="If RAD not found, estimate from DAP and MPIR (round to nearest $1k)")
    args = ap.parse_args()

    reg_path = Path(args.registry)
    ctx = load_registry(reg_path)

    corpus = Path("corpus")
    providers = sorted([p for p in corpus.glob("racs_*") if p.is_dir()])
    if args.limit:
        lim = set(args.limit); providers = [p for p in providers if p.name in lim]

    rows = []
    for prov in providers:
        pid = prov.name
        pdfs = sorted(list(prov.glob("*.pdf")))  # scan ALL PDFs now
        if not pdfs:
            rows.append((pid, None, [], [], "no_pdfs"))
            continue
        best_rad = None; rad_sources = []; daps_all = []
        for pdf in pdfs:
            res = extract_from_pdf(pdf)
            if "error" in res:
                rows.append((pid, None, [], [], f"error:{res['error']}")); continue
            if res["rads_max"] is not None:
                rad_sources.append((res["rads_max"], pdf.name))
                best_rad = max(best_rad or 0, res["rads_max"])
            if res["daps"]:
                daps_all.extend(res["daps"])
        status = "ok" if (best_rad is not None or daps_all) else "no_rad_or_dap"
        rows.append((pid, best_rad, rad_sources, sorted(set(daps_all)), status))

    # write report
    out_csv = Path("rad_extract_report.csv")
    with open(out_csv, "w") as f:
        f.write("pid,rad,rad_sources,daps,status\n")
        for pid, rad, sources, daps, status in rows:
            s_str = ";".join([f"{int(v)}:{name}" for v, name in sources])
            d_str = ";".join([str(x) for x in daps])
            f.write(f"{pid},{'' if rad is None else int(rad)},{s_str},{d_str},{status}\n")
    print(f"→ wrote {out_csv}")

    if args.apply:
        if args.mpir is None:
            print("ERROR: --apply requires --mpir <rate> (e.g., --mpir 7.78)", file=sys.stderr); sys.exit(2)
        changed = 0
        for pid, rad, sources, daps, status in rows:
            final_rad = rad
            if final_rad is None and args.estimate_from_dap and daps:
                # RAD ≈ DAP × 365 ÷ (mpir/100); round to nearest $1,000
                est = (max(daps) * 365.0) / (args.mpir / 100.0)
                final_rad = round(est / 1000.0) * 1000.0
            if final_rad is None:
                continue
            ok1 = set_provider_field(ctx, pid, "rad", int(final_rad))
            ok2 = set_provider_field(ctx, pid, "mpir", float(args.mpir))
            if ok1 or ok2: changed += 1
        save_registry(reg_path, ctx)
        print(f"✓ stamped RAD and MPIR={args.mpir} for {changed} providers")
    else:
        print("Dry run only (no registry changes). Use --apply --mpir 7.78 to stamp.")
if __name__ == "__main__":
    main()
