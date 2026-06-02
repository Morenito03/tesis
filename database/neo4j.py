# database/neo4j.py
import os
import pandas as pd
from py2neo import Graph, Node, Relationship

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "password")  # ajusta según tu configuración

_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        _ensure_constraints(_graph)
    return _graph, None

def _ensure_constraints(graph):
    # Índices y restricciones para evitar nodos duplicados
    graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Policlinico) REQUIRE p.nombre IS UNIQUE")
    graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:CMF) REQUIRE c.nombre IS UNIQUE")
    graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (con:Concepto) REQUIRE con.nombre IS UNIQUE")
    graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (sub:Subconcepto) REQUIRE sub.nombre IS UNIQUE")
    graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Documento) REQUIRE d.nombre IS UNIQUE")

def procesar_nodo_y_registros(df, idx_fila, graph, dict_cmfs, tipo_nodo, concepto_padre=None):
    """Extrae el concepto de la fila, crea sus registros para cada CMF y enlaza todo."""
    nombre_crudo = str(df.iloc[idx_fila, 0]).strip()
    if not nombre_crudo or nombre_crudo.lower() == 'nan': 
        return None

    # CORRECCIÓN DE NOMBRES: Evita que los subconceptos (ej. "19", "20-59") se mezclen entre consultas
    if tipo_nodo == "Subconcepto" and concepto_padre:
        nombre_final = f"{concepto_padre['nombre']} - {nombre_crudo}"
    else:
        nombre_final = nombre_crudo

    # 1. Crear o fusionar Concepto / Subconcepto
    nodo_principal = Node(tipo_nodo, nombre=nombre_final)
    graph.merge(nodo_principal, tipo_nodo, "nombre")

    if tipo_nodo == "Subconcepto" and concepto_padre:
        graph.merge(Relationship(nodo_principal, "DESGLOSE_DE", concepto_padre))

    # 2. Extraer Registros estrictamente para los 11 CMF (Columnas B a L -> índices 1 al 11)
    for col_idx in range(1, 12):
        valor = df.iloc[idx_fila, col_idx]
        if pd.notna(valor) and str(valor).strip() != "":
            registro = Node("Registro", valor=float(valor))
            graph.create(registro)
            graph.merge(Relationship(registro, "REGISTRADO_EN", dict_cmfs[col_idx]))
            graph.merge(Relationship(registro, "CORRESPONDE_A", nodo_principal))

    # 3. Guardar el Total General estrictamente (TTL/GRAL de la columna Q -> índice 16)
    ttl_gral = df.iloc[idx_fila, 16]
    if pd.notna(ttl_gral) and str(ttl_gral).strip() != "":
        nodo_principal["total_general"] = float(ttl_gral)
        graph.push(nodo_principal)

    return nodo_principal

def importar_registro_diario(ruta_excel="REGISTRO DIARIO DE GBT I ENERO 2024 xls.xlsx"):
    graph, _ = get_graph()
    print(f"Iniciando procesamiento de {ruta_excel}...")
    
    # Leer el excel sin headers para control absoluto de coordenadas (0-based index)
    df = pd.read_excel(ruta_excel, header=None)

    # --- NODO POLICLINICO ---
    # Fila 1 (idx 0), Columna A (idx 0)
    nombre_pol = str(df.iloc[0, 0]).strip()
    pol_node = Node("Policlinico", nombre=nombre_pol)
    graph.merge(pol_node, "Policlinico", "nombre")

    # --- NODOS CMF ---
    # Fila 3 (idx 2), Columnas B a L (idx 1 a 11)
    cmfs = {}
    for i in range(1, 12):
        nombre_cmf = str(df.iloc[2, i]).strip()
        if nombre_cmf and nombre_cmf.lower() != 'nan':
            cmf_node = Node("CMF", nombre=nombre_cmf)
            graph.merge(cmf_node, "CMF", "nombre")
            graph.merge(Relationship(cmf_node, "PERTENECE_A", pol_node))
            cmfs[i] = cmf_node

    # --- MAPEO DE ESTRUCTURA DICTADA ---
    jerarquia = {
        3: [4, 5, 6],           
        7: [8, 9, 10],          
        11: [12, 13, 14],       
        15: [16, 17, 18],       
        19: [20, 21, 22],       
        23: [24, 25, 26],       
        39: list(range(40, 52)),
        58: [59, 60, 61],       
        62: [63, 64, 65],       
        66: [67, 68, 69],       
        70: [71, 72, 73],       
        77: [78, 79, 80],       
        81: [82, 83, 84],       
        85: [86, 87, 88],       
        91: [92, 93, 94],       
        95: list(range(96, 101)),   
        101: list(range(102, 107)), 
        109: list(range(110, 115)), 
        115: list(range(116, 121)), 
        121: list(range(122, 127)), 
        127: list(range(128, 133)), 
        143: list(range(144, 151)), 
        180: [181, 182, 183],       
        184: list(range(185, 190)), 
        190: list(range(191, 196)), 
        197: [198, 199, 200]        
    }

    # Filas que van solas
    solas = (
        list(range(27, 39)) + list(range(52, 56)) + [57] + list(range(74, 77)) + 
        [89, 90] + list(range(133, 141)) + [142] + list(range(151, 177)) + 
        list(range(202, 211))
    )

    # Procesar Jerarquías (Conceptos con Subconceptos)
    for idx_padre, idxs_hijos in jerarquia.items():
        nodo_padre = procesar_nodo_y_registros(df, idx_padre, graph, cmfs, "Concepto")
        for idx_hijo in idxs_hijos:
            procesar_nodo_y_registros(df, idx_hijo, graph, cmfs, "Subconcepto", nodo_padre)

    # Procesar Filas Solas
    for idx_sola in solas:
        procesar_nodo_y_registros(df, idx_sola, graph, cmfs, "Concepto")

    print("Importación a Neo4j finalizada con éxito.")

# --- MÉTODOS DE DOCUMENTOS ---
def save_document_node(graph, nombre, ruta, contenido):
    doc = Node("Documento", nombre=nombre, ruta=ruta)
    graph.merge(doc, "Documento", "nombre")
    return doc

def list_document_nodes(matcher):
    graph, _ = get_graph()
    res = graph.run("MATCH (d:Documento) RETURN d.nombre AS nombre, d.ruta AS ruta, id(d) AS id").data()
    for r in res:
        r["id"] = str(r["id"])
    return res

def delete_document_node(graph, matcher, id_str):
    try:
        graph.run("MATCH (d) WHERE id(d)=$id DETACH DELETE d", id=int(id_str))
        return True
    except Exception:
        return False