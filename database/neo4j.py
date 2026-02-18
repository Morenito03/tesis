# database/neo4j.py
from py2neo import Graph, Node, Relationship
import os

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "password")  # ajusta

_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        _ensure_constraints(_graph)
    # node matcher se pide en tu código con matcher = NodeMatcher(graph) si hace falta
    return _graph, None

def _ensure_constraints(graph):
    # crea constraints/indices si no existen (Neo4j 4+ syntax)
    graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Patologia) REQUIRE p.nombre IS UNIQUE")
    graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:CMF) REQUIRE c.nombre IS UNIQUE")
    graph.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Documento) REQUIRE d.nombre IS UNIQUE")
    # index para Registros por fecha/patologia/CMF si lo necesitas
    # graph.run("CREATE INDEX IF NOT EXISTS FOR (r:Registro) ON (r.fecha)")

def save_document_node(graph, nombre, ruta, contenido):
    doc = Node("Documento", nombre=nombre, ruta=ruta)
    graph.merge(doc, "Documento", "nombre")
    return doc

def list_document_nodes(matcher):
    # fallback simple: devolver nodos Documento con sus propiedades
    res = graph.run("MATCH (d:Documento) RETURN d.nombre AS nombre, d.ruta AS ruta, id(d) AS id").data()
    # transformar id a string
    for r in res:
        r["id"] = str(r["id"])
    return res

def delete_document_node(graph, matcher, id_str):
    try:
        # id_str proviene de id() devuelto; convertir a int
        graph.run("MATCH (d) WHERE id(d)=$id DETACH DELETE d", id=int(id_str))
        return True
    except Exception:
        return False
