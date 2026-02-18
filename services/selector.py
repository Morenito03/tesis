# services/selector.py
import re
from database.neo4j import get_graph
graph, _ = get_graph()

def extract_month_year_cmf_patologia(text):
    # ejemplo simple: buscar año 20xx y mes en español
    meses = {
        "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
        "julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12
    }
    month = None
    year = None
    cmf = None
    patologia = None

    # year
    ys = re.findall(r'20\d{2}', text)
    if ys:
        year = int(ys[0])

    # month
    for mname, mi in meses.items():
        if mname in text.lower():
            month = mi
            break

    # cmf detection (buscar 'cmf 1' o 'cmf' + palabra)
    m = re.search(r'cmf\s*(\d+)', text.lower())
    if m:
        cmf = f"CMF {m.group(1)}"
    else:
        # intentar detectar palabras 'cmf' o 'consultorio' + nombre
        m2 = re.search(r'(cmf|consultorio)\s*[:\-]?\s*([a-zA-Z0-9\s]+)', text.lower())
        if m2:
            cmf = m2.group(2).strip().upper()

    # patologia simple: buscar palabras clave 'diabetes', 'asma', etc.
    # ideal: usar lista de patologías; aquí extraemos palabra previa a 'casos de X'
    pat_match = re.search(r'(diabetes|asma|hipertensión|hipertension)', text.lower())
    if pat_match:
        patologia = pat_match.group(1)

    return {"month": month, "year": year, "cmf": cmf, "patologia": patologia}

def query_aggregated(params):
    """
    Devuelve un resumen (total y algunos detalles) FIFO sobre la consulta:
    - total por patología/CMF/mes
    - desglose por 'Registro' (ej. días)
    """
    month = params.get("month")
    year = params.get("year")
    cmf = params.get("cmf")
    pat = params.get("patologia")

    # construir cláusula WHERE dinámicamente
    where_clauses = []
    if cmf:
        where_clauses.append("cmf.nombre = $cmf")
    if pat:
        where_clauses.append("pat.nombre CONTAINS $pat")
    # si tienes mes/año como propiedades en Documento o Registro, añade filtros
    where_cy = " AND ".join(where_clauses)
    if where_cy:
        where_cy = "WHERE " + where_cy

    # ejemplo de agregación: total por patologia y lista de primeros registros
    cypher = f"""
    MATCH (pat:Patologia)<-[:ES_PARA]-(r:Registro)-[:EN_CMF]->(cmf:CMF)
    {where_cy}
    RETURN pat.nombre AS patologia, cmf.nombre AS cmf, sum(r.cantidad) AS total
    LIMIT 50
    """
    result = graph.run(cypher, cmf=cmf, pat=pat).data()
    return result

# services/selector.py
# ... (tu código existente)

def select_documents_for_question(question: str, documentos: list) -> list:
    """
    Versión básica: selecciona documentos cuya ruta o nombre contenga palabras clave
    de la pregunta (mes, año, CMF, patología).
    """
    question_lower = question.lower()
    
    # Extraer posibles claves de la pregunta
    info = extract_month_year_cmf_patologia(question_lower)
    
    selected = []
    for doc in documentos:
        nombre = (doc.get("nombre") or "").lower()
        ruta = (doc.get("ruta") or "").lower()
        contenido = (doc.get("contenido") or "").lower()  # si guardaste contenido
        
        # Criterios simples de coincidencia
        match = False
        
        if info.get("month") and info.get("year"):
            # Buscar mes-año aproximado en nombre o ruta
            mes_anio = f"{info['month']:02d}-{info['year']}"
            if mes_anio in nombre or mes_anio in ruta:
                match = True
        
        if info.get("cmf") and info["cmf"].lower() in nombre or info["cmf"].lower() in ruta:
            match = True
            
        if info.get("patologia") and info["patologia"] in nombre or info["patologia"] in contenido:
            match = True
        
        # Si no detectamos nada específico, incluir todos (o los últimos N)
        if not info.get("month") and not info.get("year") and not info.get("cmf") and not info.get("patologia"):
            match = True  # fallback: todo si la pregunta es muy general
        
        if match:
            selected.append(doc)
    
    # Limitar a 5-10 documentos como máximo para no saturar el prompt
    return selected[:8]