#!/usr/bin/env python3
"""Revision semanal de progresion de Emiliano (rutina 5 dias).

Por cada ejercicio cuenta cuantas sesiones seguidas lleva con el MISMO peso en
el top set llegando al tope de reps => candidato a subir peso (doble
progresion). Prioriza los que mas tiempo llevan clavados y manda el resumen por
Telegram. Pensado para cron 1x/semana. Solo lee la DB.
"""
import sqlite3
import subprocess
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "gym.db"
USER_ID = 3                          # emiliano
ROUTINE_IDS = (19, 20, 21, 23, 24)   # carpeta "5 dias"
TG_NOTIFY = "/home/emiliano/.local/bin/tg-notify"
TOP_N = 4                            # cuantas marcar como prioridad de la semana
MIN_CLAVADAS = 3                     # sesiones seguidas en el mismo peso para entrar


def main():
    c = sqlite3.connect(DB)

    # ejercicios actuales + reps objetivo del top set (set 1, el mas pesado)
    ejercicios = {}
    for exid, name, treps in c.execute(
        """SELECT e.id, e.name,
                  (SELECT rs.target_reps FROM routine_sets rs
                   WHERE rs.routine_exercise_id = re.id ORDER BY rs.set_number LIMIT 1)
           FROM routine_exercises re JOIN exercises e ON e.id = re.exercise_id
           WHERE re.routine_id IN (%s)""" % ",".join("?" * len(ROUTINE_IDS)),
        ROUTINE_IDS,
    ):
        ejercicios[exid] = (name, treps or 0)

    candidatos, progresando = [], []
    for exid, (name, treps) in ejercicios.items():
        rows = c.execute(
            """SELECT ws.started_at, ss.kg, ss.reps
               FROM workout_sessions ws
               JOIN session_exercises se ON se.session_id = ws.id
               JOIN session_sets ss ON ss.session_exercise_id = se.id
               WHERE ws.user_id = ? AND se.exercise_id = ?
                 AND ss.completed = 1 AND ss.kg IS NOT NULL AND ss.reps IS NOT NULL
               ORDER BY ws.started_at""",
            (USER_ID, exid),
        ).fetchall()
        if not rows:
            continue
        # top set (mas peso) por sesion
        por_fecha = {}
        for started, kg, reps in rows:
            d = started[:10]
            top = por_fecha.get(d)
            if top is None or kg > top[0] or (kg == top[0] and reps > top[1]):
                por_fecha[d] = (kg, reps)
        ses = [por_fecha[d] for d in sorted(por_fecha)]  # oldest -> newest
        if len(ses) < 2:
            continue

        ult_kg, ult_reps = ses[-1]
        # sesiones seguidas (desde la ultima hacia atras) con el mismo peso
        clavadas = 1
        for kg, _ in reversed(ses[:-1]):
            if kg == ult_kg:
                clavadas += 1
            else:
                break
        llega_tope = treps and ult_reps >= treps

        if clavadas >= MIN_CLAVADAS and llega_tope:
            candidatos.append((name, ult_kg, ult_reps, clavadas))
        elif clavadas == 1:  # subio en la ultima sesion
            progresando.append(name)

    c.close()
    candidatos.sort(key=lambda x: -x[3])  # mas clavados primero

    L = ["\U0001F3CB️ *Revisión semanal GymBro*", ""]
    if candidatos:
        prioridad = candidatos[:TOP_N]
        resto = candidatos[TOP_N:]
        L.append(f"\U0001F3AF *Prioridad esta semana* — subí peso en estos {len(prioridad)}:")
        for name, kg, reps, n in prioridad:
            L.append(f"• {name} — {kg:g}kg x{reps} (≥{n} sesiones clavado)")
        L.append("")
        L.append("_Regla: si hacés todas las series a RIR 1-2, subí al siguiente "
                 "escalón aunque bajen las reps; después volvé a trepar las reps._")
        if resto:
            L.append("")
            L.append(f"También listos ({len(resto)}), cuando despeges los de arriba: "
                     + ", ".join(n for n, *_ in resto))
    else:
        L.append("\U0001F44C Nada clavado hace rato — venís progresando bien.")
    if progresando:
        L.append("")
        L.append("✅ Subiste en la última: " + ", ".join(sorted(set(progresando))))

    msg = "\n".join(L)
    print(msg)
    subprocess.run([TG_NOTIFY, "-m", "Markdown", msg], check=False)


if __name__ == "__main__":
    main()
