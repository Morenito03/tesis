from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from py2neo import Graph, NodeMatcher
import ollama
import os
import logging
import uuid
import threading

# Importaciones correctas según los archivos que existen
from services.selector import extract_month_year_cmf_patologia, query_aggregated
from services.parser import parse_and_insert_consolidado
from services.prompt import build_prompt
from database.neo4j import get_graph, save_document_node, list_document_nodes, delete_document_node

import pandas as pd

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión Neo4j
graph, _ = get_graph()
matcher = NodeMatcher(graph)

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

TASKS = {}  # {task_id: {status, answer, error}}

class QuestionRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return {"status": "API funcionando"}

@app.post("/ask/")
async def ask_question(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Pregunta vacía")

    task_id = str(uuid.uuid4())
    TASKS[task_id] = {"status": "pending", "answer": None, "error": None}

    thread = threading.Thread(
        target=_process_question_task,
        args=(task_id, question),
        daemon=True
    )
    thread.start()

    return {"task_id": task_id}

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        return {"status": "not_found"}
    return {
        "status": task["status"],
        "answer": task.get("answer"),
        "error": task.get("error")
    }

@app.get("/documents")
async def list_documents():
    docs = list_document_nodes(matcher)
    return {"documentos": docs}

@app.delete("/documents/{id}")
async def delete_document(id: str):
    try:
        deleted = delete_document_node(graph, matcher, id)
        if not deleted:
            return {"message": f"Documento con ID {id} no encontrado"}
        return {"message": f"Documento con ID {id} eliminado correctamente"}
    except Exception as e:
        logging.exception(f"Error al eliminar documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Guardamos el nodo Documento básico
        save_document_node(graph, file.filename, file_path, contenido="")

        # Opcional: parsear e insertar estructura en Neo4j
        try:
            parse_success = parse_and_insert_consolidado(file_path, documento_nombre=file.filename)
            if parse_success:
                logging.info(f"Archivo {file.filename} parseado e insertado en Neo4j")
        except Exception as e:
            logging.warning(f"No se pudo parsear/insertar estructura: {e}")

        return {"filename": file.filename, "message": "Archivo subido correctamente"}

    except Exception as e:
        logging.exception(f"Error al subir archivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------
# Lógica interna - procesamiento de preguntas
# ----------------------------------------------------
def _process_question_task(task_id: str, question: str):
    TASKS[task_id]["status"] = "running"
    try:
        # 1. Extraer parámetros de la pregunta
        params = extract_month_year_cmf_patologia(question)

        # 2. Obtener agregados (esto ya filtra por cmf/patologia)
        aggregated_results = query_aggregated(params)

        # 3. Seleccionar documentos (versión muy básica por ahora)
        all_docs = list(matcher.match("Documento"))
        selected_docs = []
        
        # Heurística simple: si hay cmf o patologia, filtrar documentos cuyo nombre coincida
        cmf_name = params.get("cmf")
        pat_name = params.get("concepto")
        
        for doc in all_docs:
            doc_dict = dict(doc)
            nombre = doc_dict.get("nombre", "").lower()
            if (cmf_name and cmf_name.lower() in nombre) or \
               (pat_name and pat_name in nombre):
                selected_docs.append(doc_dict)
        
        # Si no encontramos nada específico → usar todos o los más recientes
        if not selected_docs and all_docs:
            selected_docs = [dict(d) for d in all_docs[:5]]  # limitamos para no cargar demasiado

        # 4. Obtener contenido de los documentos seleccionados
        docs_contents = []
        for doc in selected_docs:
            ruta = doc.get("ruta")
            if not ruta or not os.path.exists(ruta):
                continue
                
            try:
                # Aquí usamos pandas directamente (simple y efectivo)
                df = pd.read_excel(ruta, sheet_name="CONSOLIDADO", engine="openpyxl")
                texto = df.to_string(index=False)
                docs_contents.append({
                    "nombre": doc.get("nombre"),
                    "ruta": ruta,
                    "contenido": texto[:8000]  # limitamos tamaño para el prompt
                })
            except Exception as e:
                logging.warning(f"No se pudo leer {ruta}: {e}")

        # 5. Construir prompt
        prompt_text = build_prompt(question, aggregated_results)  # usamos los agregados

        # Opcional: agregar contenido de documentos si quieres más detalle
        # if docs_contents:
        #     prompt_text += "\n\nContenido de documentos relevantes:\n"
        #     for dc in docs_contents:
        #         prompt_text += f"\n--- {dc['nombre']} ---\n{dc['contenido'][:2000]}\n"

        # 6. Consultar LLM
        respuesta = ollama.chat(
            model="gemma3",
            messages=[{"role": "user", "content": prompt_text}]
        )

        answer_text = respuesta.get("message", {}).get("content", str(respuesta))

        TASKS[task_id]["status"] = "finished"
        TASKS[task_id]["answer"] = answer_text

    except Exception as e:
        logging.exception(f"Error procesando pregunta {task_id}: {e}")
        TASKS[task_id]["status"] = "error"
        TASKS[task_id]["error"] = str(e)
        

import re

# Función auxiliar interna para extraer automáticamente el Mes y Año del nombre del archivo
def extraer_mes_anio_del_nombre(filename: str):
    filename_lower = filename.lower()
    
    # Mapa de meses comunes en los consolidados estadísticos cubanos
    meses_map = {
        "enero": "Ene", "febrero": "Feb", "marzo": "Mar", "abril": "Abr",
        "mayo": "May", "junio": "Jun", "julio": "Jul", "agosto": "Ago",
        "septiembre": "Sep", "octubre": "Oct", "noviembre": "Nov", "diciembre": "Dic"
    }
    
    mes_detectado = "Consolidado"
    for mes_es, mes_abr in meses_map.items():
        if mes_es in filename_lower:
            mes_detectado = mes_abr
            break
            
    # Si no viene en texto, busca un formato numérico de mes (01 al 12)
    if mes_detectado == "Consolidado":
        numeros_mes = re.findall(r"\b\d{2}\b", filename)
        if numeros_mes:
            num = int(numeros_mes[0])
            if 1 <= num <= 12:
                listado = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                mes_detectado = listado[num - 1]

    # Extrae el año (cualquier número de 4 dígitos que comience con 20)
    anio_match = re.search(r"20\d{2}", filename)
    anio_detectado = anio_match.group(0) if anio_match else "Actual"
    
    return mes_detectado, anio_detectado


# ----------------------------------------------------
# DASHBOARD INDICADORES MENSUALES DINÁMICO
# ----------------------------------------------------

@app.get("/dashboard")
def dashboard_data():
    # 1. Obtener el último documento registrado en el Grafo para dinamismo total
    query_ultimo_doc = "MATCH (d:Documento) RETURN d.nombre AS nombre ORDER BY d.nombre DESC LIMIT 1"
    res_doc = graph.run(query_ultimo_doc).data()
    
    # Valores por defecto en caso de que la base de datos esté vacía
    mes_actual, anio_actual = "S/D", "Actual"
    
    if res_doc:
        ultimo_archivo = res_doc[0]["nombre"]
        mes_actual, anio_actual = extraer_mes_anio_del_nombre(ultimo_archivo)

    # 2. Consulta de agregación fáctica para los Conceptos Médicos del Grafo
    query_conceptos = """
    MATCH (r:Registro)-[:CORRESPONDE_A]->(c:Concepto)
    WHERE c.nombre IN [
        'SÍNDROME FEBRIL',
        'RIESGO PRECONCEPCIONAL',
        'MUJER EDAD FERTIL',
        'CONSULTA MEDICINA',
        'ALTA INGRESO  HOGAR',
        'INGRESO HOGAR'
    ]
    RETURN
        c.nombre AS concepto,
        SUM(r.valor) AS total
    """
    result_conceptos = graph.run(query_conceptos).data()

    # 3. Consulta independiente para totalizar Consultorios (CMF) activos
    query_cmf = "MATCH (c:CMF) RETURN COUNT(c) AS total_cmf"
    result_cmf = graph.run(query_cmf).data()
    total_cmf = result_cmf[0]['total_cmf'] if result_cmf else 0

    dashboard = {}

    # 4. Empaquetado de datos estructurado exactamente como lo mapea index.js
    for row in result_conceptos:
        concepto = row["concepto"]
        dashboard[concepto] = [{
            "mes": mes_actual,       # Ej: "May", "Ene" extraído del Excel actual
            "anio": anio_actual,     # Ej: "2026" extraído del Excel actual
            "valor": row["total"]
        }]

    # Inyección limpia para la tarjeta de control institucional de CMFs
    dashboard["CMF"] = [{
        "mes": "Total",
        "anio": "Activos",
        "valor": total_cmf
    }]

    return dashboard