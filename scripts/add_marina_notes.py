"""
Agrega notas tipo personal trainer a cada ejercicio de la rutina de marina.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session

from app.database import engine
from app.models import RoutineExercise


# (routine_exercise_id, nota)
NOTES = [
    # Dia 1 - Gluteo dominante
    (99, "Espalda alta apoyada en banco, barra sobre cadera (usa almohadilla). Pies ancho de hombros. Empuja con talones y aprieta gluteo 1 seg arriba. Cuello neutro."),
    (100, "Rodillas semi-flexionadas y FIJAS. Bisagra desde la cadera con espalda recta. Sentir estiramiento femoral, no llegar al piso. Mancuernas cerca de las piernas."),
    (101, "Inclina el torso levemente hacia adelante para sesgar mas gluteo medio. Pausa 1 seg en posicion abierta. Sin impulso."),
    (102, "Soporte en barra fija. Pierna casi extendida, talon hacia arriba. La extension viene del gluteo, no de la lumbar. Pausa 1 seg arriba."),
    (103, "Pies separados, polea baja entre las piernas. Bisagra de cadera limpia, espalda neutra. Empuja la cadera adelante y aprieta gluteo en la cima."),
    (104, "45 segundos por serie. Cuerpo en linea recta, gluteo activado. No hundas la cadera ni levantes la cola. Respira tranquila."),

    # Dia 2 - Push
    (105, "Banco a 30°, no mas. Omoplatos pegados al banco, pecho afuera. Mancuernas bajan a los lados del pecho con control 2 seg."),
    (106, "Respaldo firme, abdomen apretado. Empuja arriba sin trabar el codo. Bajada controlada hasta angulo recto en el codo."),
    (107, "Codo apenas flexionado y fijo. Sentir estiramiento al abrir, contraer fuerte al juntar. Movimiento solo desde el hombro."),
    (108, "Codo apenas flexionado. Sube con el codo (no con la muneca). Pulgar levemente hacia abajo. Peso chico, calidad antes que carga."),
    (109, "Codos pegados al torso y fijos. Extension completa con contraccion 1 seg. Bajada controlada, sin balancear el hombro."),
    (110, "Redondea la espalda alta, codos a las rodillas. Foco en abdomen, no en flexion de cadera. Pausa 1 seg en contraccion."),

    # Dia 3 - Cuadriceps
    (111, "Barra sobre trapecio. Pies ancho de hombros, punta levemente afuera. Bajada profunda comoda. Rodillas siguen la linea de los pies."),
    (112, "Pies altos en la plataforma para sesgar mas gluteo. Bajada profunda controlada sin despegar la cola del asiento."),
    (113, "Pie trasero en banco, pierna delantera bien adelante. Peso en talon, tronco levemente inclinado. 10 reps por pierna."),
    (114, "Espalda apoyada. Pausa 1 seg arriba con cuadriceps duro. No tranques la rodilla con impulso. Bajada controlada."),
    (115, "Estiramiento profundo abajo (1 seg), subida alta. Tempo lento sin rebote. Foco en sensacion del gemelo."),
    (116, "Avanza solo hasta donde puedas mantener la espalda baja sin arquearse. Abdomen apretado todo el movimiento."),

    # Dia 4 - Pull
    (117, "Pecho afuera, omoplatos abajo antes de subir. Si no salen, usa banda o maquina asistida. Cero impulso. Bajada controlada en 2 seg."),
    (118, "Pecho afuera, agarra firme. Jala con el codo hacia el ombligo, no con la mano. Aprieta omoplatos atras al final."),
    (119, "Agarre neutro estrecho. Pecho afuera, codos hacia los bolsillos. Lleva la barra al esternon, no al cuello."),
    (120, "Codos altos a la altura de los ojos. Traccion hacia la frente. Rotacion externa al final. Aprieta omoplatos."),
    (121, "Codos pegados al torso, no los muevas. Subi con el biceps, no con el hombro. Bajada controlada en 2 seg."),
    (122, "Agarre neutro (pulgar arriba). Codo fijo al costado. Foco en braquial. Sin balancear el torso."),

    # Dia 5 - Gluteo + femoral
    (123, "Una sola pierna apoyada, la otra estirada o cruzada. Empuja con el talon de la pierna activa. 10 reps POR LADO. Cuidar cadera centrada."),
    (124, "Pies bien anchos, punta hacia afuera 30-45°. Bisagra desde cadera, espalda neutra. La barra baja entre las piernas. Aprieta gluteo arriba."),
    (125, "Cadera pegada al banco TODO el movimiento. Pausa 1 seg en contraccion maxima. Bajada controlada en 2-3 seg."),
    (126, "Cadera pegada al asiento. Pausa 1 seg en contraccion. Bajada lenta en 2-3 seg. Foco en sensacion femoral."),
    (127, "De pie con tobillera en polea baja. Sin balancear, eleva la pierna al costado. Pausa 1 seg arriba. Por lado."),
    (128, "Paso largo, rodilla trasera casi al piso. Empuja con el talon delantero al levantarte. 12 pasos por pierna. Tronco erguido."),
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
