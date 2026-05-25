"""
Agrega notas tipo personal trainer a cada ejercicio de la rutina de 5 dias de emiliano.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session

from app.database import engine
from app.models import RoutineExercise


# (routine_exercise_id, nota)
NOTES = [
    # Lunes - Pecho Hombros Triceps
    (63, "Top set pesado, RIR 1-2. Codos a 75°, no los abras. Bajada controlada 2 seg, sin rebotar en el pecho."),
    (65, "Omoplatos pegados al banco. Mancuernas bajan a los lados del pecho, sin chocarlas arriba. Mantene tension."),
    (64, "Codo levemente flexionado y fijo. Sentir estiramiento al abrir, contraer fuerte al juntar. Sin impulso."),
    (66, "Codo apenas flexionado. Sube con el codo, no con la muneca. Pulgar levemente hacia abajo en la cima."),
    (92, "Codos altos, traccion hacia la frente. Rotacion externa al final. Aprieta omoplatos atras."),
    (68, "Codos pegados a la cabeza, no los abras. Estiramiento profundo abajo, extension completa arriba."),
    (69, "Codo fijo al lado del torso. Extension completa con contraccion 1 seg. No muevas el hombro."),

    # Martes - Espalda Biceps
    (70, "Top set pesado, RIR 1-2. Jala con el codo, no con la mano. Aprieta omoplatos atras, pecho afuera."),
    (71, "Pecho afuera, codos a los bolsillos. Lleva la barra al esternon. Sin balancear el torso."),
    (72, "Torso firme, no te eches atras. Codos pegados al cuerpo, jala al ombligo. Aprieta dorsal abajo."),
    (74, "Codo fijo al costado. Supinacion al subir. Bajada en 2 seg, sin impulso del torso."),
    (73, "Codos pegados al torso. Separa las cuerdas en la cima. Cero impulso de hombros."),

    # Jueves - Piernas Abdomen
    (75, "Top set pesado, RIR 1-2. Pies medio-altos ancho de hombros. Bajada profunda sin despegar la cadera."),
    (78, "Pierna delantera lejos, peso en talon. Tronco levemente inclinado. 10 reps por pierna."),
    (76, "Cadera pegada al banco. Pausa 1 seg arriba en contraccion. Bajada controlada en 2-3 seg."),
    (77, "Espalda apoyada. Pausa arriba con cuadriceps duro. Sin trabar la rodilla con impulso."),
    (91, "Estiramiento profundo abajo (1 seg), contraccion alta arriba. Tempo lento, sin rebote."),
    (93, "Redondea la espalda alta, codos a las rodillas. No flexiones desde la cadera."),
    (95, "Sube las rodillas al pecho sin balancearte. Si te impulsas, hacelas con rodillas dobladas."),

    # Viernes - Upper
    (79, "Top set pesado, RIR 1-2. Pecho afuera, jala con el codo al esternon. Aprieta dorsal abajo."),
    (81, "Banco a 30°, no mas. Codos a 75°, omoplatos pegados. Bajada controlada al pecho."),
    (80, "Espalda firme contra el respaldo. No tranques el codo arriba. Bajada controlada."),
    (94, "Pecho afuera, espalda neutra. Codos pegados al cuerpo, aprieta omoplatos arriba."),
    (84, "Brazo entero apoyado. No rebotes abajo. Sube sin balancear el cuerpo."),
    (85, "Codos fijos. Extension completa con contraccion 1 seg. Bajada controlada."),
    (96, "Codo apenas flexionado. Aprieta omoplatos al final. Pecho contra el almohadon."),

    # Sabado - Piernas Gluteos Femoral
    (86, "Top set pesado, RIR 1-2. Profundidad maxima. Rodillas en linea con los pies."),
    (87, "Barra sobre cadera, escapula apoyada en banco. Empuja con talones, aprieta gluteo 1 seg arriba."),
    (89, "Rodillas semi-flexionadas y fijas. Bisagra de cadera, espalda recta. Sentir estiramiento femoral, no bajar al piso."),
    (88, "Pausa 1 seg en contraccion. Bajada en 2-3 seg. Cadera pegada al asiento."),
    (90, "Foco soleo (rodilla doblada). Estiramiento profundo, pausa 1 seg arriba, tempo lento."),
    (97, "Torso levemente inclinado hacia adelante (mas gluteo medio). Pausa 1 seg abierto."),
]


def main() -> None:
    with Session(engine) as db:
        for re_id, note in NOTES:
            re = db.get(RoutineExercise, re_id)
            if not re:
                print(f"WARN: routine_exercise {re_id} no existe")
                continue
            re.note = note
            db.add(re)
        db.commit()
        print(f"Notas aplicadas: {len(NOTES)}")


if __name__ == "__main__":
    main()
