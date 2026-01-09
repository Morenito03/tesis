from py2neo import Graph, Node, NodeMatcher
import logging
import uuid


# ------------------------------
#  CONEXIÓN A NEO4J
# ------------------------------
def get_graph():
    try:
        graph = Graph("bolt://localhost:7687")
        matcher = NodeMatcher(graph)
        logging.info("✅ Conectado a Neo4j")
        return graph, matcher
    except Exception as e:
        logging.error(f"❌ Error conectando a Neo4j: {e}")
        raise


# ------------------------------
#  GUARDAR DOCUMENTO
# ------------------------------
def save_document_node(graph, filename, path, content):
    doc_id = str(uuid.uuid4())  # ID único

    node = Node(
        "Documento",
        id=doc_id,
        nombre=filename,
        ruta=path,
        contenido=content
    )
    graph.create(node)

    return doc_id


# ------------------------------
#  LISTAR DOCUMENTOS
# ------------------------------
def list_document_nodes(matcher):
    docs = []
    for doc in matcher.match("Documento"):
        docs.append({
            "id": doc.get("id"),
            "nombre": doc.get("nombre"),
            "ruta": doc.get("ruta")
        })
    return docs


# ------------------------------
#  ELIMINAR DOCUMENTO
# ------------------------------
def delete_document_node(graph, matcher, doc_id):
    node = matcher.match("Documento", id=doc_id).first()

    if not node:
        return False
    
    graph.delete(node)
    return True


# ------------------------------
#  OBTENER DOCUMENTOS (para selector)
# ------------------------------
def get_documents():
    """
    Devuelve lista de documentos en formato:
    [
        { "id": "...", "nombre": "archivo.xls", "ruta": "/uploads/...", "contenido": "texto" },
        ...
    ]
    """
    try:
        graph = Graph("bolt://localhost:7687")
        matcher = NodeMatcher(graph)

        docs = []
        for doc in matcher.match("Documento"):
            docs.append({
                "id": doc.get("id"),
                "nombre": doc.get("nombre"),
                "ruta": doc.get("ruta"),
                "contenido": doc.get("contenido", "")
            })
        return docs
    except Exception as e:
        logging.error(f"❌ Error obteniendo documentos: {e}")
        return []
