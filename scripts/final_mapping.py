"""Mapeo final con picks manuales. Imprime resumen y guarda JSON listo para download."""
import json

# Mis picks (local_id -> dataset exerciseId, o "SKIP" si no hay equivalente)
PICKS = {
    49: "side hip abduction",          # Abductores o gluteo medio
    37: "cable hip adduction",         # Aductores
    3: "cable low fly",                # Aperturas en Polea
    41: "cable decline fly",           # Aperturas peck deck (no hay pec deck en dataset)
    83: "cable curl",                  # Biceps con soga (best disponible — no hay rope cable curl explícito)
    28: "lever chest press",           # Chest press / press convergente
    90: "cable side crunch",           # Crunch En Polea (mejor que tener nada)
    20: "lever lying leg curl",        # Curl Femoral Acostado
    89: "lever seated leg curl",       # Curl Femoral En Maquina Sentado (corregido)
    13: "dumbbell hammer curl",        # Curl Martillo
    14: "lever preacher curl",         # Curl Predicador
    31: "dumbbell incline curl",       # Curl biceps inclinado o cable
    35: "lever lying leg curl",        # Curl femoral acostado o sentado
    47: "lever seated leg curl",       # Curl femoral sentado o acostado
    30: "cable lateral raise",         # Elevaciones laterales en polea
    88: "cable incline triceps extension",  # Extension Triceps Maquina
    21: "lever leg extension",         # Extension Cuadriceps
    43: "cable incline triceps extension",  # Extension triceps por cable
    66: "SKIP",                        # Face Pull — no hay match limpio en dataset
    48: "lever seated calf raise",     # Gemelo sentado
    36: "cable standing calf raise",   # Gemelos de pie o en prensa
    46: "sled hack squat",             # Hack squat
    44: "SKIP",                        # Hip thrust — solo banda, no es lo mismo
    5: "lever front pulldown",         # Jalon agarre neutro cerrado
    82: "cable pulldown",              # Jalon al pecho agarre normal
    40: "cable one arm pulldown",      # Jalon unilateral
    93: "hanging leg raise",           # Leg raise colgado
    45: "dumbbell romanian deadlift",  # Peso muerto rumano mancuernas (corregido)
    33: "sled 45в° leg press",         # Prensa (note: el dataset tiene encoding raro)
    18: "sled 45в° leg press",         # Prensa 45
    2: "dumbbell incline bench press",     # Press Inclinado con mancuernas (corregido!)
    86: "lever shoulder press v. 2",        # Press Maquina Hombros (corregido)
    76: "dumbbell bench press",             # Press de pecho con mancuernas
    52: "lever chest press",                # Press de pecho en maquina (corregido)
    27: "dumbbell palms in incline bench press",  # Press inclinado neutro/semi (corregido!)
    39: "dumbbell bench press",             # Press plano mancuernas
    32: "cable pushdown (with rope attachment)",  # Pushdown con cuerda
    57: "cable seated row",                 # Remo bajo agarre cerrado (corregido!)
    92: "lever t bar row",                  # Remo en T
    38: "cable seated row",                 # Remo maquina pecho apoyado (corregido!)
    29: "cable seated row",                 # Remo pecho apoyado cable (corregido!)
    91: "lever seated reverse fly",    # Reverse Peck Deck (corregido)
    34: "barbell side split squat",    # Sentadilla bulgara (mejor disponible)
    75: "barbell lying triceps extension",  # Triceps Frances
    77: "dumbbell lateral raise",      # Vuelo lateral
    42: "lever seated reverse fly",    # Vuelos posteriores maquina (corregido)
    84: "dumbbell alternate biceps curl",   # biceps alternado sentado (corregido)
    80: "cable standing one arm triceps extension",  # triceps a una mano (corregido)
    79: "lever triceps extension",     # triceps trasnuca
}

dataset = json.load(open('/tmp/exercises_v2.json'))
by_name = {}
for d in dataset:
    by_name.setdefault(d['name'].lower(), []).append(d)

local = json.load(open('/tmp/exercise_mapping_candidates.json'))

final = []
skipped = []
not_found = []

for entry in local:
    lid = entry['local_id']
    pick = PICKS.get(lid)
    if pick == "SKIP":
        skipped.append((lid, entry['local_name']))
        continue
    if not pick:
        not_found.append((lid, entry['local_name']))
        continue
    matches = by_name.get(pick.lower())
    if not matches:
        not_found.append((lid, entry['local_name'], pick))
        continue
    d = matches[0]
    final.append({
        "local_id": lid,
        "local_name": entry['local_name'],
        "dataset_id": d['exerciseId'],
        "dataset_name": d['name'],
        "gif_url": d['gifUrl'],
    })

print(f"\n{'ID':<5}{'Local':<55}{'Dataset':<50}")
print('-' * 110)
for f in sorted(final, key=lambda x: x['local_name']):
    print(f"  {f['local_id']:<3}{f['local_name'][:53]:<55}{f['dataset_name'][:48]}")

print(f"\nSKIP (sin animación, podés mapear manualmente luego):")
for lid, name in skipped:
    print(f"  {lid:<3} {name}")

if not_found:
    print(f"\n⚠️  No encontrados en dataset:")
    for item in not_found:
        print(f"  {item}")

print(f"\n{'='*80}")
print(f"Total mapeados: {len(final)}    Skip: {len(skipped)}    No encontrados: {len(not_found)}")

with open('/tmp/exercise_mapping_final.json', 'w') as f:
    json.dump(final, f, indent=2)
print("Guardado: /tmp/exercise_mapping_final.json")
