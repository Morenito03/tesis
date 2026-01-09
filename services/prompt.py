def build_prompt(question: str, documents: list) -> str:
    """
    Construye el prompt maestro para la IA usando documentos Excel médicos (GBT).
    Cada documento debe venir como:
    {
        "nombre": str,
        "ruta": str,
        "contenido": str
    }
    """

    intro = """
Eres un asistente médico especializado.

IMPORTANTE:
- GBT significa Grupo Básico de Trabajo.
- CMF significa Consultorio Médico de la Familia.
- TTL / GRAL significa total general.
- CONS significa consultorio.
- TERR significa Terreno.
- Existen 11 CMF (consultorios).
- El TOTAL GENERAL de cada mes está en la hoja llamada CONSOLIDADO.
- Los datos por CMF están en hojas individuales con los mismos indicadores.
- El nombre del archivo indica el MES y el AÑO (ej: REGISTRO DIARIO DE GBT I ENERO 2024).
- SOLO debes responder usando la información contenida en los documentos.
- NO inventes datos.
- Si la información no está disponible, responde claramente que no existe en los registros.
"""

    docs_text = ""

    for doc in documents:
        # 🔒 Protección total contra errores
        if not isinstance(doc, dict):
            continue

        nombre = doc.get("nombre", "Documento sin nombre")
        contenido = doc.get("contenido", "")

        docs_text += f"""
==============================
DOCUMENTO: {nombre}

Este documento corresponde a un REGISTRO DIARIO DE GBT.
El TOTAL GENERAL se encuentra en la hoja CONSOLIDADO.

CONTENIDO:
{contenido}
==============================
"""

    prompt = f"""
{intro}

DOCUMENTOS DISPONIBLES:
{docs_text}

PREGUNTA DEL USUARIO:
{question}

RESPUESTA:
"""

    return prompt
