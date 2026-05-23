"""
Mapea cada ejercicio del catalogo local de gymbro contra el dataset de ExerciseDB
(metadata en /tmp/exercises_v2.json). No descarga nada; solo imprime top 3
candidatos por ejercicio para revision humana.

Output: /tmp/exercise_mapping_candidates.json
"""
import json
import re
import sqlite3
from difflib import SequenceMatcher
from pathlib import Path

DB = "data/gym.db"
DATASET = "/tmp/exercises_v2.json"
OUT = "/tmp/exercise_mapping_candidates.json"
USER_ID = 3

# Keywords ES->EN. Aplicados en orden, primero los compuestos.
ES_TO_EN = [
    # compuestos primero
    (r"\bpress de pecho con mancuernas\b", "dumbbell bench press"),
    (r"\bpress de pecho en maquina\b", "machine chest press"),
    (r"\bpress inclinado con mancuernas\b", "incline dumbbell bench press"),
    (r"\bpress plano con mancuernas\b", "dumbbell bench press"),
    (r"\bpress maquina hombros\b", "machine shoulder press"),
    (r"\bjalon al pecho agarre neutro\b", "close grip lat pulldown"),
    (r"\bjalon al pecho agarre normal\b", "lat pulldown"),
    (r"\bjalon unilateral\b", "one arm lat pulldown"),
    (r"\bjalon supino\b", "underhand lat pulldown"),
    (r"\bremo pecho apoyado\b", "chest supported row"),
    (r"\bremo bajo con agarre cerrado\b", "close grip cable row"),
    (r"\bremo en t\b", "t bar row"),
    (r"\bremo en maquina\b", "machine row"),
    (r"\bremo sentado con cable\b", "cable seated row"),
    (r"\bcurl femoral acostado\b", "lying leg curl"),
    (r"\bcurl femoral sentado\b", "seated leg curl"),
    (r"\bcurl femoral en maquina sentado\b", "seated leg curl machine"),
    (r"\bextension de cuadriceps\b", "leg extension"),
    (r"\bextension de triceps con maquina\b", "machine triceps extension"),
    (r"\bextension de triceps por cable\b", "cable triceps extension"),
    (r"\btriceps a una mano\b", "single arm cable kickback"),
    (r"\btriceps trasnuca\b", "overhead triceps extension"),
    (r"\btriceps frances\b", "lying triceps extension"),
    (r"\bbiceps con soga\b", "rope cable curl"),
    (r"\bbiceps alternado\b", "alternating dumbbell curl"),
    (r"\bcurl biceps inclinado\b", "incline dumbbell curl"),
    (r"\bcurl martillo\b", "hammer curl"),
    (r"\bcurl predicador\b", "preacher curl"),
    (r"\baperturas en peck deck\b", "pec deck fly"),
    (r"\baperturas en polea\b", "cable fly"),
    (r"\baperturas en cables\b", "cable fly"),
    (r"\breverse peck deck\b", "reverse pec deck"),
    (r"\bvuelos posteriores en maquina\b", "machine rear delt fly"),
    (r"\bvuelos posteriores\b", "rear delt fly"),
    (r"\bvuelo lateral\b", "dumbbell lateral raise"),
    (r"\belevaciones laterales en polea\b", "cable lateral raise"),
    (r"\bface pull\b", "face pull"),
    (r"\bsentadilla bulgara\b", "bulgarian split squat"),
    (r"\bhack squat\b", "hack squat"),
    (r"\bpeso muerto rumano\b", "romanian deadlift"),
    (r"\bhip thrust\b", "barbell hip thrust"),
    (r"\bprensa 45\b", "leg press"),
    (r"\bprensa\b", "leg press"),
    (r"\bgemelos de pie\b", "standing calf raise"),
    (r"\bgemelos en prensa\b", "leg press calf raise"),
    (r"\bgemelo sentado\b", "seated calf raise"),
    (r"\babductores\b", "hip abductor"),
    (r"\baductores\b", "hip adductor"),
    (r"\bgluteo medio\b", "hip abductor"),
    (r"\bcrunch en polea\b", "cable crunch"),
    (r"\bleg raise colgado\b", "hanging leg raise"),
    (r"\bpushdown con cuerda\b", "rope triceps pushdown"),
    (r"\bpushdown\b", "triceps pushdown"),
    (r"\bchest press\b", "machine chest press"),

    # palabras sueltas
    (r"\bcon mancuernas\b", "dumbbell"),
    (r"\bcon mancuerna\b", "dumbbell"),
    (r"\bcon cable\b", "cable"),
    (r"\bcon barra\b", "barbell"),
    (r"\ben maquina\b", "machine"),
    (r"\ben polea\b", "cable"),
    (r"\ben cables\b", "cable"),
    (r"\binclinado\b", "incline"),
    (r"\bagarre cerrado\b", "close grip"),
    (r"\bagarre neutro\b", "neutral grip"),
    (r"\bagarre normal\b", ""),
    (r"\bsentado\b", "seated"),
    (r"\bacostado\b", "lying"),
    (r"\bcomodo\b", ""),
    (r"\bo .*?$", ""),       # quitar "o variante alternativa"
    (r"\s+", " "),
]


def translate(name: str) -> str:
    s = name.lower().strip()
    for pat, repl in ES_TO_EN:
        s = re.sub(pat, repl, s)
    return s.strip()


def score(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def main():
    dataset = json.load(open(DATASET))
    print(f"Dataset: {len(dataset)} ejercicios")

    con = sqlite3.connect(DB)
    user_exs = con.execute("""
        SELECT id, name FROM exercises
        WHERE id IN (
            SELECT DISTINCT exercise_id FROM routine_exercises
            WHERE routine_id IN (SELECT id FROM routines WHERE owner_id=?)
            UNION
            SELECT DISTINCT exercise_id FROM session_exercises
            WHERE session_id IN (SELECT id FROM workout_sessions WHERE user_id=?)
        )
        ORDER BY name
    """, (USER_ID, USER_ID)).fetchall()
    con.close()

    results = []
    for ex_id, ex_name in user_exs:
        translated = translate(ex_name)
        ranked = sorted(
            ((score(translated, d["name"]), d) for d in dataset),
            key=lambda x: -x[0],
        )[:3]
        results.append({
            "local_id": ex_id,
            "local_name": ex_name,
            "translated": translated,
            "candidates": [
                {
                    "score": round(sc, 2),
                    "dataset_id": d["exerciseId"],
                    "dataset_name": d["name"],
                    "gif_url": d["gifUrl"],
                    "target": d["targetMuscles"],
                    "equipment": d["equipments"],
                }
                for sc, d in ranked
            ],
        })

    Path(OUT).write_text(json.dumps(results, indent=2))

    # imprimir resumen humano
    print(f"\n{'='*80}\nMAPEO (mejor candidato + 2 alternativas)\n{'='*80}\n")
    confident, ambiguous, weak = 0, 0, 0
    for r in results:
        best = r["candidates"][0]
        marker = "✅" if best["score"] >= 0.7 else ("🟡" if best["score"] >= 0.5 else "🔴")
        if best["score"] >= 0.7:
            confident += 1
        elif best["score"] >= 0.5:
            ambiguous += 1
        else:
            weak += 1
        print(f"{marker} {r['local_name']}")
        print(f"   ES→EN: '{r['translated']}'")
        for c in r["candidates"]:
            print(f"   [{c['score']:.2f}] {c['dataset_name']} ({c['equipment']}, {c['target']})")
        print()

    print(f"\n{'='*80}")
    print(f"Confident (≥0.7): {confident}   Ambiguous (0.5-0.7): {ambiguous}   Weak (<0.5): {weak}")
    print(f"Mapping completo guardado en: {OUT}")


if __name__ == "__main__":
    main()
