# services/prompt.py
def build_prompt(question, aggregated_results):
    """
    Construye un prompt pequeño y conciso:
    - una línea de contexto (por ejemplo: "Fuente: REGISTRO DIARIO DE GBT - CONSOLIDADO (mes año)")
    
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
-
- Si la información no está disponible, responde claramente que no existe en los registros
    """
    if not aggregated_results:
        context = "No hay datos estructurados relevantes en la base de datos para la consulta."
    else:
        rows = []
        for r in aggregated_results[:10]:
            rows.append(f"- {r.get('patologia', 'ND')} | {r.get('cmf','ND')} | total: {r.get('total',0)}")
        context = "Resumen de datos relevantes:\n" + "\n".join(rows)

    prompt = f"{context}\n\nPregunta: {question}\nResponde de forma concisa, mostrando cifras y explicación breve."
    return prompt
