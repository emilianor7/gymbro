"""Baja los GIFs del mapping final y actualiza image_path en la DB."""
import json
import sqlite3
import urllib.request
from pathlib import Path

MAPPING = "/tmp/exercise_mapping_final.json"
DB = "data/gym.db"
MEDIA_DIR = Path("static/exercise_media")
UA = "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://exercisedb.dev/"})
    with urllib.request.urlopen(req, timeout=20) as r, open(dest, "wb") as f:
        f.write(r.read())

mapping = json.load(open(MAPPING))

print(f"Bajando {len(mapping)} GIFs a {MEDIA_DIR}/")
print()

con = sqlite3.connect(DB)
ok, skip, fail = 0, 0, 0

for m in mapping:
    dest = MEDIA_DIR / f"{m['dataset_id']}.gif"
    rel_path = f"/static/exercise_media/{m['dataset_id']}.gif"
    if dest.exists():
        print(f"  ⏭  ya existe: {m['local_name']}")
        skip += 1
    else:
        try:
            download(m['gif_url'], dest)
            size = dest.stat().st_size
            print(f"  ✅ {m['local_name']}  ({size//1024} KB)")
            ok += 1
        except Exception as e:
            print(f"  ❌ {m['local_name']}  → {e}")
            fail += 1
            continue
    # update DB
    con.execute("UPDATE exercises SET image_path=? WHERE id=?", (rel_path, m['local_id']))

con.commit()
con.close()

print(f"\n{'='*60}")
print(f"Descargados: {ok}    Ya existían: {skip}    Fallos: {fail}")
print(f"image_path actualizado en {len(mapping)-fail} ejercicios")
