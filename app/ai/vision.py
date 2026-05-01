SYSTEM_SCAN = """
Sos un experto en fitness analizando planillas de entrenamiento escritas a mano o impresas.
Tu tarea es extraer los ejercicios y crear rutinas estructuradas.
Debes responder UNICAMENTE con un JSON valido, sin texto adicional, sin markdown, sin backticks.

El JSON debe tener esta estructura exacta:
{
  "routine_base_name": "Nombre base de la rutina (ej: Full B)",
  "blocks": [
    {
      "label": "Sem 1-2",
      "exercises": [
        {
          "name": "Nombre del ejercicio en español",
          "sets": 4,
          "target_reps": 10,
          "rest_seconds": 90,
          "note": "aclaracion si la hay"
        }
      ]
    }
  ],
  "notes": "Observaciones generales de la planilla si las hay"
}

Reglas:
- Si hay multiples bloques de semanas (Sem 1-2, Sem 3-4, etc), crea un bloque por cada uno
- Si no hay bloques de semanas, crea un solo bloque con label "Semana 1"
- target_reps: usar el numero de reps de la planilla, si hay rango usar el limite superior
- sets: usar el numero de series indicado, si no hay usar 4
- rest_seconds: 90 por defecto
- Corrige errores de escritura en los nombres de ejercicios
- Responde SOLO el JSON puro, sin markdown, sin backticks, sin texto antes o despues
""".strip()


def scan_routine_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """Extrae rutinas de una imagen usando Gemini Vision."""
    import os
    from google import genai
    from google.genai import types
    from . import gemini as g

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY no configurada")

    client = genai.Client(api_key=key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            types.Part.from_text(
                text="Extrae todos los ejercicios y bloques de semanas de esta planilla de entrenamiento. "
                     "Responde SOLO el JSON puro, sin markdown, sin backticks."
            ),
        ],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_SCAN,
            temperature=0.2,
            max_output_tokens=4096,
        ),
    )

    raw = response.text
    # fix encoding si viene mal
    try:
        raw = raw.encode("latin1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    print(f"[vision] raw response ({len(raw)} chars): {raw[:300]}")

    try:
        return g._extract_json(raw)
    except Exception as e:
        raise RuntimeError(f"No se pudo parsear la respuesta de Gemini: {e}\nRespuesta: {raw[:500]}")