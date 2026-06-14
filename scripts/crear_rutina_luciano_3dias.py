"""Crea para luciano (user_id=13) una carpeta + rutina de 3 dias.

Contexto: vuelve al gym tras ~10 anios sin pesas, pero es activo (otros deportes,
vida sana). Buena base aerobica y motriz; lo limitante son tendones, articulaciones
y el patron tecnico bajo carga.

Enfoque PT: FULL BODY 3 dias (cada musculo 3x/semana) = lo mejor para readaptar.
Fase de reintroduccion: 3 series, lejos del fallo (2-3 reps en reserva), tecnica
antes que carga, sesgo a maquina/mancuerna en lo articularmente sensible. Los
grandes con barra (sentadilla / peso muerto) entran al 3er dia, livianos y tecnicos.
Sin pesos objetivo: que registre su propia carga las primeras semanas.

Idempotente-ish: aborta si ya existe la carpeta.
"""
import sqlite3

DB = "data/gym.db"
OWNER = 13
FOLDER_NAME = "Plan 3 dias (Vuelta al gym - Full body)"


# (exercise_id, rest_seconds, nota, [(set_number, set_type, target_reps), ...])
def sets(n, reps, t="NORMAL"):
    return [(i + 1, t, reps) for i in range(n)]


DIAS = [
    {
        "title": "Dia A - Full body (patron base)",
        "notes": "Primer dia de la semana. Sin prisa: calentar 5-10 min y dejar 2-3 reps en reserva en cada serie. La meta hoy es reaprender el movimiento, no buscar carga.",
        "ejercicios": [
            (18, 120, "Empezamos por prensa (no sentadilla) para cargar pierna sin exigir tecnica de barra todavia. Pies ancho de hombros, bajada controlada 2-3 seg hasta angulo recto sin despegar la cola del respaldo. No traques la rodilla arriba.", sets(3, 12)),
            (2, 90, "Banco a 30°. Omoplatos pegados, pecho afuera. Bajada lenta 2 seg a los lados del pecho, sin rebotar. Mancuerna te deja mas margen articular que la barra al volver.", sets(3, 10)),
            (6, 90, "Pecho afuera, jala con el CODO hacia el ombligo (no con la mano). Aprieta omoplatos atras 1 seg. Sin balanceo de tronco.", sets(3, 12)),
            (9, 90, "Carga muy conservadora la primera semana: el hombro es lo que mas se resiente al volver. Abdomen apretado, empuja arriba sin arquear la lumbar. Si molesta el hombro, avisame y lo cambiamos por mancuernas.", sets(3, 10)),
            (20, 60, "Cadera pegada al banco. Sube con control, pausa 1 seg en la contraccion y baja lento 2-3 seg. Senti el femoral trabajar, no la lumbar.", sets(3, 12)),
            (23, 45, "40-45 segundos por serie. Cuerpo en linea recta, gluteo y abdomen activados. No hundas la cadera ni saques la cola. Respira tranquilo.", sets(3, 40)),
        ],
    },
    {
        "title": "Dia B - Full body (unilateral + jalon)",
        "notes": "Segundo dia. Sumamos trabajo unilateral (corrige asimetrias tipicas tras parar) y jalon vertical. Misma regla: tecnica y reps en reserva, nada al fallo.",
        "ejercicios": [
            (19, 90, "Estocada en Smith: el riel te da estabilidad para reaprender el patron sin pelear el equilibrio. Pie trasero atras, baja recto hasta que la rodilla delantera quede a 90°. 10 reps por pierna. Empuja con el talon delantero.", sets(3, 10)),
            (5, 90, "Agarre neutro cerrado. Pecho afuera, lleva los codos hacia los bolsillos. Baja la barra al pecho con el dorsal, no con los brazos. Sin impulso de tronco.", sets(3, 12)),
            (1, 120, "Hoy si press banca con barra, pero liviano y con observador o pines de seguridad. Omoplatos pegados, codos ~45°, barra al esternon, bajada controlada 2 seg. Calidad antes que peso.", sets(3, 10)),
            (10, 45, "Codo apenas flexionado, sube con el codo (pulgar levemente abajo). Peso chico, sin balanceo. El hombro se reconstruye con volumen limpio, no con carga.", sets(3, 15)),
            (21, 60, "Espalda apoyada. Pausa 1 seg arriba con el cuadriceps duro, sin trabar la rodilla de golpe. Bajada controlada. Ideal para preparar la rodilla para la sentadilla del dia C.", sets(3, 12)),
            (25, 45, "Arrodillado en polea. Redondea la espalda llevando los codos a las rodillas con el abdomen, no con los brazos. Exhala al bajar. Sin tirones.", sets(3, 15)),
        ],
    },
    {
        "title": "Dia C - Full body (patrones de fuerza)",
        "notes": "Tercer dia: reintroducimos los grandes patrones con barra (sentadilla y peso muerto) MUY livianos y tecnicos. Si algo de la zona lumbar o rodilla molesta, paramos esa serie. Estos dos son la base a futuro, hoy solo grabamos el patron.",
        "ejercicios": [
            (17, 150, "Barra sobre el trapecio (no sobre el cuello). Pies ancho de hombros, punta levemente afuera. Baja hasta donde mantengas la espalda recta y comoda (no fuerces profundidad aun). Rodillas siguen la linea de los pies. Peso muy conservador.", sets(3, 8)),
            (8, 150, "Peso muerto solo tecnico: barra pegada a las canillas, espalda recta y neutra, empuja el piso con los pies y extiende cadera y rodilla juntas. Baja con bisagra de cadera. Si pierdes la espalda recta, bajaste demasiado el peso o subiste de mas las reps. Sin prisa entre reps.", sets(3, 6)),
            (3, 60, "Pecho recuperado con apertura en polea, mas amable para el hombro tras los empujes de la semana. Codos apenas flexionados y fijos, junta las manos al frente apretando el pecho 1 seg. Sin convertirlo en press.", sets(3, 12)),
            (13, 60, "Curl martillo: agarre neutro, codos pegados al torso y fijos. Sube con el biceps sin balancear, baja controlado 2 seg. Cuida tambien el tendon del codo: peso moderado.", sets(3, 12)),
            (16, 60, "Codos pegados y quietos, solo se mueve el antebrazo. Extension completa con contraccion 1 seg, vuelta controlada. Peso comodo.", sets(3, 12)),
            (22, 45, "Estiramiento profundo abajo 1 seg, subida alta a punta de pie. Tempo lento sin rebote. Foco en la sensacion del gemelo.", sets(3, 15)),
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
print("OK - rutina de 3 dias creada para luciano.")
