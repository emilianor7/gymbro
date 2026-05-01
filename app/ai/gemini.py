"""
Capa de acceso a Gemini. Maneja prompts, parsing de JSON y reintentos.
"""
import json
import os
import re
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"


def _client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY no configurada")
    return genai.Client(api_key=key)


def _extract_json(text: str) -> dict | list:
    """Extrae JSON de la respuesta aunque venga con markdown fences."""
    text = text.strip()
    # quitar ```json ... ``` o ``` ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text.strip())


def _chat(system: str, user: str) -> str:
    client = _client()
    response = client.models.generate_content(
        model=MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.4,
            max_output_tokens=4096,
        ),
    )
    return response.text


# ============================================================
# A) GENERAR RUTINA
# ============================================================
SYSTEM_GENERATE = """
Sos un personal trainer experto en hipertrofia y fuerza.
El usuario te va a pedir que generes una rutina de entrenamiento.
Debes responder UNICAMENTE con un JSON valido, sin texto adicional, sin markdown.

El JSON debe tener esta estructura exacta:
{
  "routines": [
    {
      "title": "Upper A",
      "exercises": [
        {
          "name": "Nombre del ejercicio",
          "sets": 3,
          "target_reps": 10,
          "rest_seconds": 90,
          "note": "Tip tecnico opcional"
        }
      ]
    }
  ],
  "explanation": "Breve explicacion de la logica del programa (2-3 oraciones)"
}

Reglas:
- Usa nombres de ejercicios en español
- target_reps debe ser un numero entero (usa el limite superior del rango)
- rest_seconds: 60 para aislamiento, 90 para compuestos moderados, 120-180 para compuestos pesados
- No incluyas target_kg, el usuario lo va a cargar cuando entrene
- El campo "note" es opcional, usalo para aclaraciones tecnicas importantes
- Responde SOLO el JSON, sin ningun texto antes o despues
""".strip()


def generate_routine(prompt: str, available_exercises: list[str]) -> dict:
    """
    prompt: lo que pide el usuario ("hipertrofia 4 dias upper lower")
    available_exercises: lista de nombres del catalogo para que el LLM los use si puede
    """
    ex_list = "\n".join(f"- {e}" for e in available_exercises[:80])
    user_msg = f"""
Genera una rutina con estas caracteristicas: {prompt}

Ejercicios disponibles en el catalogo del usuario (usa estos cuando puedas, si necesitas otros crealos):
{ex_list}

Responde solo el JSON.
""".strip()

    raw = _chat(SYSTEM_GENERATE, user_msg)
    return _extract_json(raw)


# ============================================================
# B) AJUSTAR PESOS Y REPS
# ============================================================
SYSTEM_ADJUST = """
Sos un personal trainer experto en progresion de cargas.
El usuario te va a mostrar el historial de sus ultimas sesiones de una rutina y te va a pedir ajustes.
Debes responder UNICAMENTE con un JSON valido, sin texto adicional, sin markdown.

El JSON debe tener esta estructura exacta:
{
  "adjustments": [
    {
      "exercise_name": "Nombre del ejercicio",
      "current_kg": 80.0,
      "suggested_kg": 82.5,
      "current_reps": 10,
      "suggested_reps": 10,
      "reason": "Completaste todas las series con buena forma, subir 2.5kg"
    }
  ],
  "summary": "Resumen general de la semana y recomendaciones (3-4 oraciones)"
}

Reglas de progresion:
- Si completo todas las series con las reps objetivo: subir 2.5kg en ejercicios de tren superior, 5kg en tren inferior
- Si no completo alguna serie: mantener el peso, posiblemente bajar 1-2 reps
- Si le costo mucho (rpe alto o reps muy por debajo): bajar 5-10% el peso
- Para ejercicios de aislamiento subir de a 1.25kg o 2.5kg maximo
- Responde SOLO el JSON, sin ningun texto antes o despues
""".strip()


def suggest_adjustments(routine_title: str, history: list[dict], objective: str = "hipertrofia") -> dict:
    """
    history: lista de sesiones con ejercicios y sets completados
    """
    history_text = json.dumps(history, ensure_ascii=False, indent=2)
    user_msg = f"""
Rutina: {routine_title}
Objetivo del usuario: {objective}

Historial de las ultimas sesiones:
{history_text}

Sugiere ajustes de pesos y repeticiones para la proxima semana.
Responde solo el JSON.
""".strip()

    raw = _chat(SYSTEM_ADJUST, user_msg)
    return _extract_json(raw)


# ============================================================
# D) ANALISIS POST-WORKOUT
# ============================================================
SYSTEM_ANALYZE = """
Sos un personal trainer experto. El usuario acaba de terminar un entrenamiento.
Analiza el workout y da feedback constructivo y motivador.
Debes responder UNICAMENTE con un JSON valido, sin texto adicional, sin markdown.

El JSON debe tener esta estructura exacta:
{
  "score": 85,
  "highlights": ["Punto positivo 1", "Punto positivo 2"],
  "improvements": ["Cosa a mejorar 1"],
  "feedback": "Mensaje personalizado de 3-4 oraciones sobre el entrenamiento",
  "next_session_tip": "Un tip especifico para la proxima sesion"
}

Reglas:
- score: 0-100, donde 100 es entrenamiento perfecto
- highlights: maximo 3 puntos positivos
- improvements: maximo 2 sugerencias de mejora (constructivas, no negativas)
- feedback: tono motivador pero honesto
- Responde SOLO el JSON, sin ningun texto antes o despues
""".strip()


def analyze_workout(session: dict, objective: str = "hipertrofia") -> dict:
    """
    session: dict con titulo, duracion, ejercicios y sets completados
    """
    session_text = json.dumps(session, ensure_ascii=False, indent=2)
    user_msg = f"""
Objetivo del usuario: {objective}

Datos del entrenamiento:
{session_text}

Analiza este entrenamiento y da feedback.
Responde solo el JSON.
""".strip()

    raw = _chat(SYSTEM_ANALYZE, user_msg)
    return _extract_json(raw)
