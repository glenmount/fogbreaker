import pandas as pd, json, re, sys
from pathlib import Path

XLSX = "FOGBREAKER_Provider_Dataset.xlsx"
SHEET = "Milestone1_Working CK"

try:
    xl = pd.ExcelFile(XLSX)
except FileNotFoundError:
    sys.exit(f"Excel not found at {XLSX}")

sheet = None
for s in xl.sheet_names:
    if s.strip().lower() == SHEET.strip().lower():
        sheet = s; break
if sheet is None:
    sys.exit(f"Sheet not found: {SHEET} (available: {xl.sheet_names})")

df = pd.read_excel(xl, sheet_name=sheet)

# --- Resolve columns (tolerant) ---
def pick(dfcols, *names):
    low = {str(c).strip().lower(): c for c in dfcols}
    # direct
    for n in names:
        if n and n.strip().lower() in low: return low[n.strip().lower()]
    # relaxed (strip non-alnum)
    def norm(s): return re.sub(r'[^a-z0-9]','', str(s).lower())
    for n in names:
        nn = norm(n)
        for lc, orig in low.items():
            if norm(lc) == nn:
                return orig
    return None

# Detect RACS column automatically if not provided
racs_col = next((c for c in df.columns if "racs" in str(c).lower()), None)
if not racs_col:
    # last resort guesses
    racs_col = pick(df.columns, "RACS code", "RACS", "RACS ID", "RACS Code – Service")
if not racs_col:
    sys.exit("Could not locate a RACS column. Please tell me the exact header text and rerun.")

# Common fields with aliases
name_col     = pick(df.columns, "Provider Name", "Service Name", "Name")
addr_col     = pick(df.columns, "Physical Address", "Address", "Street Address")
suburb_col   = pick(df.columns, "Suburb", "Service Suburb", "City", "Town")
state_col    = pick(df.columns, "Physical State", "State")
pc_col       = pick(df.columns, "Postal Code", "Postcode", "ZIP")
lat_col      = pick(df.columns, "Latitude", "Lat")
lng_col      = pick(df.columns, "Longitude", "Long", "Lng")
over_col     = pick(df.columns, "Overall Star Rating", "Overall Rating")
clin_col     = pick(df.columns, "Staffing rating", "Clinical Star Rating", "Clinical Rating")
comp_col     = pick(df.columns, "Compliance rating", "Compliance Star Rating", "Compliance Rating")

def pid_from_racs(x):
    s = re.sub(r'[^0-9A-Za-z]+','', str(x).strip()).lower()
    return f"racs_{s}"

def num(x):
    try:
        import math, pandas as _pd
        if _pd.isna(x): return None
        v=float(x)
        return v if math.isfinite(v) else None
    except: return None

out=[]
for _, r in df.iterrows():
    racs = r.get(racs_col)
    if pd.isna(racs) or str(racs).strip()=="":
        continue
    out.append({
      "provider_id": pid_from_racs(racs),
      "name":        "" if not name_col   else ("" if pd.isna(r.get(name_col))   else str(r.get(name_col)).strip()),
      "address":     "" if not addr_col   else ("" if pd.isna(r.get(addr_col))   else str(r.get(addr_col)).strip()),
      "suburb":      "" if not suburb_col else ("" if pd.isna(r.get(suburb_col)) else str(r.get(suburb_col)).strip()),
      "postcode":    "" if not pc_col     else ("" if pd.isna(r.get(pc_col))     else str(r.get(pc_col)).strip()),
      "lat":          None if not lat_col else num(r.get(lat_col)),
      "lng":          None if not lng_col else num(r.get(lng_col)),
      "star_overall": None if not over_col else num(r.get(over_col)),
      "star_clinical":None if not clin_col else num(r.get(clin_col)),
      "star_compliance": None if not comp_col else num(r.get(comp_col)),
      "tags": []
    })

Path("registry").mkdir(exist_ok=True)
Path("registry/providers.json").write_text(
  json.dumps(out, sort_keys=True, ensure_ascii=False, separators=(",",":")),
  encoding="utf-8"
)
print(f"OK: wrote registry/providers.json with {len(out)} providers")
print("Columns used →",
      {"racs":racs_col, "name":name_col, "address":addr_col, "suburb":suburb_col,
       "state":state_col, "postcode":pc_col, "lat":lat_col, "lng":lng_col,
       "star_overall":over_col, "star_clinical":clin_col, "star_compliance":comp_col})
