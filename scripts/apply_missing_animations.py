"""
Aplica image_path a los 25 ejercicios sin animacion que usan marina y emiliano.
Baja los GIFs faltantes desde el CDN publico de ExerciseDB.
Las picks reusan IDs ya descargados cuando es la misma animacion para que no
dupliquemos archivos en disco (15 descargas nuevas, 10 reusos).
"""
import sqlite3
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "gym.db"
MEDIA_DIR = ROOT / "static" / "exercise_media"
CDN_TPL = "https://static.exercisedb.dev/media/{ex_id}.gif"
UA = "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# (local_id, dataset_id, comentario corto)
PICKS = [
    (96,  "CHpahtl", "lever seated hip abduction"),
    (97,  "CHpahtl", "reuse hip abduction (no cable version en dataset)"),
    (105, "Wgaz7pm", "lever seated crunch"),
    (12,  "25GPyDY", "barbell curl"),
    (107, "Zg3XY7P", "reuse lever seated leg curl"),
    (7,   "lBDjFxJ", "pull-up"),
    (22,  "8ozhUIZ", "barbell standing calf raise"),
    (10,  "DsgkuIt", "reuse dumbbell lateral raise"),
    (102, "qx4fgX7", "dumbbell single leg split squat (bulgaro)"),
    (103, "RRWFUcw", "dumbbell lunge (caminando)"),
    (16,  "Hx1WC8I", "reuse cable triceps extension"),
    (66,  "wqNPGCg", "cable rear delt row con rope (mejor proxy a face pull)"),
    (106, "wqNPGCg", "reuse face pull proxy"),
    (44,  "qKBpF7I", "barbell glute bridge (mejor proxy a hip thrust)"),
    (94,  "qKBpF7I", "reuse hip thrust proxy"),
    (95,  "qKBpF7I", "reuse hip thrust proxy (no unilateral)"),
    (98,  "HEJ6DIX", "cable kickback"),
    (100, "rR0LJzx", "reuse dumbbell romanian deadlift"),
    (101, "KgI0tqW", "barbell sumo deadlift"),
    (23,  "VBAWRPG", "weighted front plank"),
    (104, "vqsbmL0", "reuse lever shoulder press"),
    (99,  "OM46QHm", "cable pull through (with rope)"),
    (6,   "fUBheHs", "reuse cable seated row"),
    (24,  "NAgVB3t", "wheel rollerout"),
    (17,  "qXTaZnJ", "barbell full squat"),
]


def download(ex_id: str, dest: Path) -> int:
    url = CDN_TPL.format(ex_id=ex_id)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://exercisedb.dev/"})
    with urllib.request.urlopen(req, timeout=20) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest.stat().st_size


def main() -> int:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)

    downloaded, reused, failed, updated = 0, 0, 0, 0
    for local_id, ex_id, comment in PICKS:
        dest = MEDIA_DIR / f"{ex_id}.gif"
        rel = f"/static/exercise_media/{ex_id}.gif"

        if dest.exists():
            print(f"  reuse  local={local_id:<4} {ex_id}  {comment}")
            reused += 1
        else:
            try:
                kb = download(ex_id, dest) // 1024
                print(f"  fetch  local={local_id:<4} {ex_id}  ({kb} KB)  {comment}")
                downloaded += 1
            except Exception as e:
                print(f"  FAIL   local={local_id:<4} {ex_id}  -> {e}")
                failed += 1
                continue

        cur = con.execute("UPDATE exercises SET image_path=? WHERE id=?", (rel, local_id))
        if cur.rowcount == 1:
            updated += 1
        else:
            print(f"  WARN: exercise id={local_id} no existe en DB")

    con.commit()
    con.close()

    print(f"\nDescargados: {downloaded}  Reusados: {reused}  Fallos: {failed}")
    print(f"image_path actualizado en {updated} ejercicios")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
