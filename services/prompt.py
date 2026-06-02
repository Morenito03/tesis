# services/prompt.py
def build_prompt(question, aggregated_results):
    """
    Construye un prompt pequeño y conciso.
    """
    if not aggregated_results:
        context = "No hay datos estructurados relevantes en la base de datos para la consulta."
    else:
        rows = []
        for r in aggregated_results[:10]:
            # CAMBIO CLAVE AQUÍ: Usamos 'concepto' en lugar de 'patologia'
            concepto_nombre = r.get('concepto', 'ND')
            cmf_nombre = r.get('cmf', 'ND')
            total = r.get('total', 0)
            rows.append(f"- Concepto: {concepto_nombre} | CMF: {cmf_nombre} | Cantidad: {total}")
            
        context = "Resumen de datos extraídos de la Base de Datos en Neo4j:\n" + "\n".join(rows)

    prompt = f"""Eres un asistente médico especializado en análisis de datos.

IMPORTANTE:
- GBT significa Grupo Básico de Trabajo.
- CMF significa Consultorio Médico de la Familia. Existen 11 CMF.
- TTL / GRAL significa Total General.
- SOLO debes responder usando la información contenida en el siguiente contexto.
- NO inventes datos. Si el contexto dice 'No hay datos', responde que no existe información.
- NO PONER * EN LAS RESPUESTAS. 

{context}

Pregunta del usuario: {question}
Responde de forma clara, directa, mostrando cifras exactas y una explicación breve."""
    
    return prompt