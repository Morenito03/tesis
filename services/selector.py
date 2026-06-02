# services/selector.py
import re
from database.neo4j import get_graph

graph, _ = get_graph()

def extract_month_year_cmf_patologia(text):
    """
    Extrae entidades clave de la pregunta del usuario.
    """
    text = text.lower()
    
    # 1. Detección de CMF (Busca 'cmf 3', 'consultorio 5', o solo el número si viene con cmf)
    cmf = None
    m_cmf = re.search(r'(cmf|consultorio)\s*(\d+)', text)
    if m_cmf:
        # Lo guardamos como string para comparar con el nombre del nodo
        cmf = m_cmf.group(2)

    # 2. Detección de Conceptos Principales
    # Agregamos los términos exactos de tu Excel
    conceptos_clave = [
        "consulta medicina", "terreno medicina", "examen pre-empleo", 
        "examen periodico", "geriatria", "estomatologia", "citologia",
        "sindrome febril", "ingreso hogar"
    ]
    concepto_detectado = None
    for c in conceptos_clave:
        if c in text:
            concepto_detectado = c.upper()
            break

    # 3. Detección de Subconceptos (Rangos de edad o desgloses)
    subconceptos_clave = ["19", "20-59", "60y+", "total"]
    sub_detectado = None
    for s in subconceptos_clave:
        # Buscamos la palabra exacta para no confundir '19' con '2019'
        if re.search(rf'\b{s}\b', text):
            sub_detectado = s.upper()
            break

    return {
        "cmf": cmf,
        "concepto": concepto_detectado,
        "subconcepto": sub_detectado
    }

def query_aggregated(params):
    """
    Ejecuta la consulta en Neo4j adaptada a la jerarquía de Concepto-Subconcepto.
    """
    cmf = params.get("cmf")
    concepto = params.get("concepto")
    sub = params.get("subconcepto")

    # CASO A: El usuario pregunta por un TOTAL GENERAL (TTL/GRAL)
    # Ejemplo: "¿Cuál es el total de Consulta Medicina?"
    if (not cmf or "total" in str(sub).lower()) and concepto:
        cypher = """
        MATCH (n:Concepto)
        WHERE n.nombre CONTAINS $concepto
        RETURN n.nombre AS concepto, 'TODOS' AS cmf, n.total_general AS total
        """
        return graph.run(cypher, concepto=concepto).data()

    # CASO B: El usuario pregunta por un dato específico de un CMF
    # Ejemplo: "19 años en Consulta Medicina CMF 3"
    where_clauses = []
    if cmf:
        # Buscamos que el nombre del CMF contenga el número (ej. "3" en "3.0" o "CMF 3")
        where_clauses.append("c.nombre CONTAINS $cmf")
    
    if concepto and sub and sub != "TOTAL":
        # Buscamos el nombre combinado que creamos en el parser: "PADRE - HIJO"
        where_clauses.append("n.nombre CONTAINS $concepto AND n.nombre CONTAINS $sub")
    elif concepto:
        where_clauses.append("n.nombre CONTAINS $concepto")

    if not where_clauses:
        return []

    where_cy = "WHERE " + " AND ".join(where_clauses)

    cypher = f"""
    MATCH (c:CMF)<-[:REGISTRADO_EN]-(r:Registro)-[:CORRESPONDE_A]->(n)
    {where_cy}
    RETURN n.nombre AS concepto, c.nombre AS cmf, r.valor AS total
    """
    
    return graph.run(cypher, cmf=cmf, concepto=concepto, sub=sub).data()