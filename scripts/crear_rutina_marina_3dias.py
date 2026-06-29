"""Crea para marina (user_id=9) una carpeta + rutina de 3 dias (Opcion A):
2 dias de pierna/gluteo pesado + 1 dia de tren superior completo.
Sin pesos objetivo (igual que su rutina actual). Idempotente-ish: aborta si ya existe la carpeta.
"""
import sqlite3

DB = "data/gym.db"
OWNER = 9
FOLDER_NAME = "Plan 3 dias (Pierna + Gluteo)"

# (exercise_id, rest_seconds, nota, [(set_number, set_type, target_reps), ...])
def sets(n, reps, t="NORMAL"):
    return [(i + 1, t, reps) for i in range(n)]

DIAS = [
    {
        "title": "Dia 1 - Gluteo & cadera (bisagra)",
        "notes": "Foco en bisagra de cadera y gluteo. Tecnica y rango antes que carga.",
        "ejercicios": [
            (94, 120, "Espalda alta apoyada en banco, barra sobre cadera con almohadilla. Empuja con talones y aprieta gluteo 1 seg arriba. Cuello neutro.", sets(4, 10)),
            (100, 90, "Rodillas semi-flexionadas y fijas. Bisagra desde la cadera con espalda recta. Senti el estiramiento femoral, no llegues al piso.", sets(4, 10)),
            (96, 60, "Inclina el torso levemente adelante para sesgar mas gluteo medio. Pausa 1 seg en apertura. Sin impulso.", sets(3, 15)),
            (107, 60, "Cadera pegada al asiento. Pausa 1 seg en contraccion. Bajada lenta 2-3 seg. Foco en sensacion femoral.", sets(3, 12)),
            (98, 60, "Pierna casi extendida, talon hacia arriba. La extension viene del gluteo, no de la lumbar. Pausa 1 seg arriba. Por lado.", sets(3, 12)),
            (23, 45, "45 segundos por serie. Cuerpo en linea recta, gluteo activado. No hundas la cadera. Respira tranquila.", sets(3, 45)),
        ],
    },
    {
        "title": "Dia 2 - Tren superior completo",
        "notes": "Unico dia de tren superior: push + pull + hombro + brazos. Carga moderada, calidad de ejecucion.",
        "ejercicios": [
            (2, 90, "Banco a 30°. Omoplatos pegados, pecho afuera. Mancuernas bajan a los lados del pecho con control 2 seg.", sets(4, 10)),
            (5, 90, "Agarre neutro estrecho. Pecho afuera, codos hacia los bolsillos. Lleva la barra al esternon. Sin impulso.", sets(4, 10)),
            (104, 60, "Respaldo firme, abdomen apretado. Empuja arriba sin trabar el codo. Bajada controlada a angulo recto.", sets(3, 12)),
            (6, 60, "Pecho afuera, agarre firme. Jala con el codo hacia el ombligo, no con la mano. Aprieta omoplatos atras.", sets(3, 12)),
            (10, 45, "Codo apenas flexionado. Sube con el codo, pulgar levemente abajo. Peso chico, calidad antes que carga.", sets(3, 15)),
            (12, 45, "SUPERSERIE con el siguiente. Codos pegados al torso. Subi con el biceps, bajada controlada 2 seg.", sets(3, 12)),
            (16, 45, "SUPERSERIE con el anterior. Codos pegados y fijos. Extension completa con contraccion 1 seg.", sets(3, 12)),
        ],
    },
    {
        "title": "Dia 3 - Cuadriceps & gluteo (rodilla)",
        "notes": "Dominante de rodilla con asistencia de gluteo. Profundidad y control en los compuestos.",
        "ejercicios": [
            (17, 150, "Barra sobre trapecio. Pies ancho de hombros, punta levemente afuera. Bajada profunda comoda. Rodillas siguen la linea de los pies.", sets(4, 8)),
            (18, 120, "Pies altos en la plataforma para sesgar mas gluteo. Bajada profunda controlada sin despegar la cola del asiento.", sets(4, 12)),
            (102, 90, "Pie trasero en banco, pierna delantera bien adelante. Peso en el talon, tronco levemente inclinado. 10 reps por pierna.", sets(3, 10)),
            (21, 60, "Espalda apoyada. Pausa 1 seg arriba con cuadriceps duro. No tranques la rodilla con impulso. Bajada controlada.", sets(3, 12)),
            (97, 60, "De pie con tobillera en polea baja. Sin balancear, eleva la pierna al costado. Pausa 1 seg arriba. Por lado.", sets(3, 15)),
            (22, 45, "Estiramiento profundo abajo 1 seg, subida alta. Tempo lento sin rebote. Foco en la sensacion del gemelo.", sets(4, 15)),
        ],
    },
]

con = sqlite3.connect(DB)
con.execute("PRAGMA foreign_keys=ON")
cur = con.cursor()

existe = cur.execute(
    "SELECT id FROM routine_folders WHERE owner_id=? AND name=?", (OWNER, FOLDER_NAME)
).fetchone()
if existe:
    raise SystemExit(f"ABORTADO: ya existe la carpeta '{FOLDER_NAME}' (id={existe[0]}).")

# siguiente order_index de carpeta
row = cur.execute("SELECT COALESCE(MAX(order_index),-1)+1 FROM routine_folders WHERE owner_id=?", (OWNER,)).fetchone()
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
print("OK - rutina de 3 dias creada para marina.")
