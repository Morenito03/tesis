# services/parser.py
from database.neo4j import get_graph, importar_registro_diario, save_document_node

graph, _ = get_graph()

def parse_and_insert_consolidado(file_path, documento_nombre=None):
    """
    Delega la lectura y extracción a la función especializada de neo4j.py
    que ya conoce la jerarquía exacta de Conceptos, CMFs y Totales.
    """
    try:
        # Llamar al motor de ingesta que ya creamos y funciona perfecto
        importar_registro_diario(file_path)
        
        # Registrar el documento en el grafo para tener la trazabilidad
        if not documento_nombre:
            documento_nombre = file_path.split("/")[-1]
            
        save_document_node(graph, documento_nombre, file_path, "")
        
        return True
    except Exception as e:
        print(f"Error parseando el consolidado: {e}")
        return False