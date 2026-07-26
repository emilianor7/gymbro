"""Crea para emiliano (user_id=3) una carpeta + rutina de 5 dias adaptada
para cuidar el hombro (hipertrofia sin irritar el manguito).

Convencion de SUPERSERIES (el modelo no las soporta nativamente):
  - Los ejercicios de una superserie van CONSECUTIVOS en el order_index.
  - El primero (A1) lleva rest_seconds=0 y la nota arranca con "SUPERSERIE A1".
  - El segundo (A2) lleva el descanso real del bloque y la nota "SUPERSERIE A2".
  Asi, en la sesion en vivo, A1 no dispara el timer y A2 si.

Reutiliza los exercise_id que emiliano ya venia usando para no cortar el
historial ni la deteccion de PRs. Crea solo los 4 que faltaban.

Idempotente-ish: aborta si ya existe la carpeta.
"""
import sqlite3

DB = "data/gym.db"
OWNER = 3
FOLDER_NAME = "5 dias - Hombro cuidado"

INDICACIONES = (
    "RIR: torso 3 / brazos 1-2 / piernas 1-2. Sin fallo en pecho, espalda ni deltoides. "
    "Descenso controlado 2-3 seg. Principales: 2 min de descanso; prensa, hack y RDL hasta 3 min. "
    "Superseries: A1 y A2 seguidos sin descanso, y recien ahi 75-90 seg. "
    "Regla de dolor: si aparece dolor punzante, enganche, perdida de fuerza, no poder controlar el "
    "descenso o dolor nocturno nuevo, se suspende el ejercicio ese dia."
)

# Ejercicios que faltaban en el catalogo: (name, primary_muscle, equipment)
NUEVOS = [
    ("Press inclinado en maquina convergente", "CHEST", "MACHINE"),
    ("Peso muerto rumano en Smith", "HAMSTRINGS", "SMITH"),
    ("Reverse crunch", "ABDOMINALS", "BODYWEIGHT"),
    ("Crunch en maquina", "ABDOMINALS", "MACHINE"),
]


def sets(n, reps):
    return [(i + 1, "NORMAL", reps) for i in range(n)]


def ss(letra, pos, otro, descanso_txt=None):
    """Prefijo de nota para superserie."""
    if pos == 1:
        return f"SUPERSERIE {letra}1 - seguido y sin descanso con {otro}. "
    return f"SUPERSERIE {letra}2 - viene de {otro}. Recien al terminar esta, descansar {descanso_txt}. "


con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys=ON")
cur = con.cursor()

existe = cur.execute(
    "SELECT id FROM routine_folders WHERE owner_id=? AND name=?", (OWNER, FOLDER_NAME)
).fetchone()
if existe:
    raise SystemExit(f"ABORTADO: ya existe la carpeta '{FOLDER_NAME}' (id={existe[0]}).")

# --- ejercicios nuevos -------------------------------------------------
ids = {}
for name, muscle, equip in NUEVOS:
    row = cur.execute(
        "SELECT id FROM exercises WHERE owner_id=? AND name=?", (OWNER, name)
    ).fetchone()
    if row:
        ids[name] = row[0]
        print(f"  (ya existia) {name} -> id={row[0]}")
        continue
    cur.execute(
        """INSERT INTO exercises (name, primary_muscle, secondary_muscles, equipment,
                                  is_custom, owner_id, created_at)
           VALUES (?,?,?,?,1,?, datetime('now'))""",
        (name, muscle, "[]", equip, OWNER),
    )
    ids[name] = cur.lastrowid
    print(f"  Ejercicio creado: {name} -> id={ids[name]}")

PRESS_INC_MAQ = ids["Press inclinado en maquina convergente"]
RDL_SMITH = ids["Peso muerto rumano en Smith"]
REVERSE_CRUNCH = ids["Reverse crunch"]
CRUNCH_MAQ = ids["Crunch en maquina"]

# --- dias --------------------------------------------------------------
# (exercise_id, rest_seconds, nota, sets)
DIAS = [
    {
        "title": "Lunes - Upper A",
        "notes": "Empuje + tiron horizontal, todo en linea comoda de hombro. RIR 3 en torso, nada al fallo. " + INDICACIONES,
        "ejercicios": [
            (52, 120, "RIR 3. Agarre neutro o semineutro, codos a 30-45 grados del cuerpo. No bajes hasta que los codos queden muy detras del torso: ahi es donde se pinza el hombro. Bajada controlada 2-3 seg.", sets(3, 12)),
            (38, 120, "RIR 3. Codos relativamente cerca del cuerpo, no los lleves exageradamente detras del torso. Jala con el codo, aprieta omoplato 1 seg y vuelve controlado.", sets(4, 12)),
            (84, 0, ss("A", 1, "triceps con soga") + "RIR 1-2. Codos pegados al torso, sin balanceo. Bajada 2-3 seg.", sets(3, 12)),
            (32, 90, ss("A", 2, "el curl", "75-90 seg") + "RIR 1-2. Codos quietos al costado, extension completa y vuelta controlada. Sin abrir los codos.", sets(3, 12)),
            (41, 90, "RIR 3. Recorrido CORTO y controlado: no lleves los brazos detras del cuerpo. Si molesta el hombro, se suspende.", sets(2, 13)),
            (77, 75, "Solo si no duele. RIR 3. Brazo ligeramente adelantado (plano escapular), sin superar el rango comodo y sin impulso. Peso chico.", sets(2, 18)),
        ],
    },
    {
        "title": "Martes - Piernas A (cuadriceps)",
        "notes": "Dia de cuadriceps. Aca si podes apretar: RIR 1-2. Descansos largos en prensa. " + INDICACIONES,
        "ejercicios": [
            (18, 180, "RIR 2. 2-3 min de descanso. Pies ancho de hombros, bajada controlada sin despegar la cola del respaldo. No traques la rodilla arriba.", sets(4, 10)),
            (34, 120, "RIR 2. 10-12 reps POR PIERNA. En Smith el riel te deja empujar sin pelear el equilibrio. Torso levemente adelantado, empuja con el talon de la pierna de adelante.", sets(3, 11)),
            (21, 0, ss("A", 1, "curl femoral acostado") + "RIR 1-2. Pausa 1 seg arriba, bajada controlada.", sets(3, 13)),
            (20, 90, ss("A", 2, "la extension de cuadriceps", "75-90 seg") + "RIR 1-2. Cadera pegada al banco, sin arquear la lumbar para levantar mas.", sets(3, 13)),
            (36, 0, ss("B", 1, "crunch en polea") + "RIR 1-2. Estiramiento profundo abajo 1 seg, subida alta. Sin rebote.", sets(4, 15)),
            (90, 90, ss("B", 2, "los gemelos", "60-90 seg") + "RIR 1-2. Redondea la espalda con el abdomen, no tires con los brazos. Exhala al bajar.", sets(3, 13)),
        ],
    },
    {
        "title": "Miercoles - Brazos, deltoides controlados y abdomen",
        "notes": "Dia liviano de articulacion: casi todo en superseries de brazos. El vuelo lateral entra SOLO si el lunes fue completamente indoloro. " + INDICACIONES,
        "ejercicios": [
            (14, 0, ss("A", 1, "extension de triceps en maquina") + "RIR 1-2. Si hay predicador en maquina, mejor que la barra Z. Codos apoyados y fijos, no despegues los hombros.", sets(3, 11)),
            (88, 90, ss("A", 2, "el curl predicador", "75-90 seg") + "RIR 1-2. Codos quietos, extension completa, vuelta controlada.", sets(3, 11)),
            (83, 0, ss("B", 1, "triceps unilateral hacia abajo") + "RIR 1-2. Curl martillo con soga: agarre neutro, codos pegados, sin balanceo.", sets(3, 13)),
            (80, 90, ss("B", 2, "el curl martillo", "75-90 seg") + "RIR 1-2. 12-15 POR BRAZO. Manten el brazo junto al cuerpo. Nada de extensiones por encima de la cabeza.", sets(3, 13)),
            (77, 75, "Solo si el lunes fue completamente indoloro. RIR 3. Brazo ligeramente adelantado, sin impulso. Si molesta, se elimina.", sets(2, 18)),
            (REVERSE_CRUNCH, 0, ss("C", 1, "crunch en maquina") + "En banco o piso. Lleva las rodillas al pecho enrollando la pelvis, sin tomar impulso con las piernas.", sets(3, 15)),
            (CRUNCH_MAQ, 75, ss("C", 2, "el reverse crunch", "60-75 seg") + "Flexiona con el abdomen, no tires con los brazos. Pausa 1 seg abajo.", sets(3, 13)),
        ],
    },
    {
        "title": "Jueves - Piernas B (gluteos y femorales)",
        "notes": "Cadena posterior. En hack y RDL descansos de hasta 3 min. Las series livianas de entrada no cuentan como efectivas. " + INDICACIONES,
        "ejercicios": [
            (46, 180, "RIR 2. 2-3 min de descanso. Las series livianas de entrada NO cuentan como efectivas: contabiliza solo las 4 en RIR 2. Bajada controlada, espalda pegada al respaldo.", sets(4, 10)),
            (44, 120, "RIR 1-2. Evita una posicion que te lleve los hombros hacia atras de forma incomoda: acomoda el banco a la altura de las escapulas y meti el menton. Pausa arriba 1 seg apretando gluteo.", sets(4, 10)),
            (RDL_SMITH, 180, "RIR 2. 2-3 min. Podes usar straps: los brazos SOLO sostienen la carga, no tires con los hombros. Bisagra de cadera, espalda neutra, baja hasta sentir el femoral sin perder la curva lumbar.", sets(3, 10)),
            (89, 0, ss("A", 1, "abductores en maquina") + "RIR 1-2. Pausa 1 seg en la contraccion, bajada 2-3 seg.", sets(3, 13)),
            (49, 90, ss("A", 2, "el curl femoral sentado", "75-90 seg") + "RIR 1-2. Torso levemente adelantado, abre con control y vuelve sin dejar que la maquina te cierre de golpe.", sets(3, 18)),
            (48, 0, ss("B", 1, "reverse crunch") + "RIR 1-2. Gemelo sentado: estiramiento completo abajo, subida alta, sin rebote.", sets(4, 15)),
            (REVERSE_CRUNCH, 90, ss("B", 2, "el gemelo sentado", "60-90 seg") + "Enrolla la pelvis, sin impulso de piernas.", sets(3, 15)),
        ],
    },
    {
        "title": "Viernes - Upper B",
        "notes": "Segundo upper: jalon vertical + empuje inclinado, todo en maquina y rango comodo. RIR 3, sin buscar cargas maximas. " + INDICACIONES,
        "ejercicios": [
            (5, 120, "RIR 3. Nunca detras de la nuca. No te dejes colgar completamente al final del recorrido: manten tension y un rango comodo de hombro.", sets(3, 12)),
            (PRESS_INC_MAQ, 120, "RIR 3. Inclinacion moderada (no muy alta, que ahi el hombro sufre). Agarre neutro o semineutro. No busques cargas maximas, buscas estimulo limpio.", sets(3, 12)),
            (29, 120, "RIR 3. Agarre neutro, codos relativamente cerca del cuerpo. No los lleves exageradamente detras del torso.", sets(3, 12)),
            (31, 0, ss("A", 1, "extension de triceps en maquina o polea") + "RIR 1-2. Codos fijos, sin balanceo.", sets(2, 13)),
            (88, 90, ss("A", 2, "el curl", "75-90 seg") + "RIR 1-2. Codos pegados, extension completa y vuelta controlada.", sets(2, 13)),
            (77, 75, "Solo si fue indoloro durante TODA la semana. RIR 3. Brazo ligeramente adelantado, sin impulso. Si aparece molestia, se elimina del plan.", sets(2, 18)),
        ],
    },
]

# --- carga -------------------------------------------------------------
row = cur.execute(
    "SELECT COALESCE(MAX(order_index),-1)+1 FROM routine_folders WHERE owner_id=?", (OWNER,)
).fetchone()
folder_order = row[0]

cur.execute(
    "INSERT INTO routine_folders (name, owner_id, order_index, created_at) VALUES (?,?,?, datetime('now'))",
    (FOLDER_NAME, OWNER, folder_order),
)
folder_id = cur.lastrowid
print(f"Carpeta creada: id={folder_id}  '{FOLDER_NAME}'")

for dia in DIAS:
    cur.execute(
        """INSERT INTO routines (title, notes, owner_id, created_at, updated_at, folder_id)
           VALUES (?,?,?, datetime('now'), datetime('now'), ?)""",
        (dia["title"], dia["notes"], OWNER, folder_id),
    )
    rid = cur.lastrowid
    print(f"  Rutina id={rid}: {dia['title']}")
    for order_index, (ex_id, rest, nota, set_list) in enumerate(dia["ejercicios"]):
        cur.execute(
            """INSERT INTO routine_exercises (routine_id, exercise_id, order_index, rest_seconds, note)
               VALUES (?,?,?,?,?)""",
            (rid, ex_id, order_index, rest, nota),
        )
        re_id = cur.lastrowid
        for set_number, set_type, target_reps in set_list:
            cur.execute(
                """INSERT INTO routine_sets (routine_exercise_id, set_number, set_type, target_kg, target_reps)
                   VALUES (?,?,?,?,?)""",
                (re_id, set_number, set_type, None, target_reps),
            )

con.commit()
con.close()
print("OK - rutina de 5 dias (hombro cuidado) creada para emiliano.")
