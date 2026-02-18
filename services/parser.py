# services/parser.py
import pandas as pd
from py2neo import Node, Relationship
from datetime import datetime
from database.neo4j import get_graph

graph, _ = get_graph()

def parse_and_insert_consolidado(file_path, documento_nombre=None):
    """
    Lee la hoja 'CONSOLIDADO' o la primera hoja y extrae:
    - columnas: consultorios (o días según el archivo)
    - filas: patologías (nombre)
    Inserta nodos: Documento, CMF, Patologia, Registro (día/cantidad) y relaciones.
    """
    # intenta cargar la hoja consolidado
    try:
        df = pd.read_excel(file_path, sheet_name="CONSOLIDADO")
    except Exception:
        df = pd.read_excel(file_path, sheet_name=0)

    # normalizar: asumimos que la primera columna es 'Patologia' (nombres)
    # y el resto columnas son consultorios o dias
    df = df.fillna(0)
    cols = list(df.columns)
    pat_col = cols[0]

    # crear nodo documento
    if not documento_nombre:
        documento_nombre = file_path.split("/")[-1]
    doc_node = Node("Documento", nombre=documento_nombre, ruta=file_path)
    graph.merge(doc_node, "Documento", "nombre")

    # detectar mes/año en filename (opcional)
    # aquí puedes parsear mes y año y setear propiedades en doc_node

    for _, row in df.iterrows():
        patologia_nombre = str(row[pat_col]).strip()
        if not patologia_nombre:
            continue
        pat_node = Node("Patologia", nombre=patologia_nombre)
        graph.merge(pat_node, "Patologia", "nombre")

        # el resto de columnas: cada columna representa un consultorio (CMF) o día
        for col in cols[1:]:
            valor = row[col]
            try:
                cantidad = int(valor)
            except Exception:
                try:
                    cantidad = float(valor)
                except Exception:
                    cantidad = 0
            if cantidad == 0:
                continue

            cmf_nombre = str(col).strip()
            cmf_node = Node("CMF", nombre=cmf_nombre)
            graph.merge(cmf_node, "CMF", "nombre")

            # crear registro con meta: cantidad, referencia a documento, fecha opcional
            registro_props = {
                "cantidad": float(cantidad),
                # opción: si col es día, setear "dia" o compute fecha completa
                # "dia": ...
            }
            reg_node = Node("Registro", **registro_props)
            graph.create(reg_node)

            # Relaciones
            graph.merge(Relationship(doc_node, "TIENE_REGISTRO", reg_node))
            graph.merge(Relationship(reg_node, "EN_CMF", cmf_node))
            graph.merge(Relationship(reg_node, "ES_PARA", pat_node))

    return True
