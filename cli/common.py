import json, hashlib, math, datetime
from pathlib import Path
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()
def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
def read_json(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
def iso_z(dt: datetime.datetime) -> str:
    return dt.replace(microsecond=0, tzinfo=datetime.timezone.utc).isoformat().replace('+00:00','Z')
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(1-a), math.sqrt(a))
    return R*c
