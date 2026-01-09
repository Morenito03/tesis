from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from py2neo import Graph, Node, NodeMatcher
import ollama
import os
import logging
import uuid
import threading
import time

from services.selector import select_documents_for_question
from services.parser import parse_consolidado_text
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

# Iniciar conexión Neo4j (usa wrapper)
graph, matcher = get_graph()

# Carpeta uploads
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Tareas en memoria: { task_id: {status: "pending|running|finished|error", answer: str, error: str}}
TASKS = {}

# Modelo de request
class QuestionRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return {"status": "API funcionando"}

# Endpoint para iniciar tarea (devuelve task_id inmediatamente)
@app.post("/ask/")
async def ask_question(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Pregunta vacía")

    task_id = str(uuid.uuid4())
    TASKS[task_id] = {"status": "pending", "answer": None, "error": None}

    # Lanzar ejecución en hilo background (no bloqueante)
    thread = threading.Thread(target=_process_question_task, args=(task_id, question), daemon=True)
    thread.start()

    return {"task_id": task_id}

# Endpoint para consultar resultado
@app.get("/result/{task_id}")
async def get_result(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        return {"status": "not_found"}
    return {"status": task["status"], "answer": task["answer"], "error": task["error"]}

# Endpoint listar documentos
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
        logging.exception(f"❌ Error al eliminar documento: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar documento: {str(e)}")

# Upload endpoint
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Guardar
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Si es Excel, intentar parsear hoja consolidado para extraer texto resumido/útil
        contenido = ""
        if file.filename.endswith((".xls", ".xlsx")):
            try:
                contenido = parse_consolidado_text(file_path)
            except Exception as e:
                logging.warning(f"No se pudo parsear Excel para contenido: {e}")
                # fallback: leer toda la primera hoja como texto
                try:
                    df = pd.read_excel(file_path)
                    contenido = df.to_string(index=False)
                except Exception:
                    contenido = ""

        # Guardar nodo en Neo4j (ruta, nombre, contenido)
        save_document_node(graph, file.filename, file_path, contenido)

        return {"filename": file.filename, "message": "Archivo subido y guardado correctamente"}
    except Exception as e:
        logging.exception(f"❌ Error al subir archivo: {e}")
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")


# ------------------------------
#  Funciones internas
# ------------------------------
def _process_question_task(task_id: str, question: str):
    TASKS[task_id]["status"] = "running"
    try:
        # 1) seleccionar documentos relevantes (selector hace heurísticas por mes/año/CMF)
        documentos = list(matcher.match("Documento"))
        selected_docs = select_documents_for_question(question, documentos)

        # 2) parsear cada documento seleccionado (leer hoja CONSOLIDADO o primer sheet)
        docs_contents = []
        for doc in selected_docs:
            ruta = doc.get("ruta")
            if ruta and os.path.exists(ruta):
                try:
                    txt = parse_consolidado_text(ruta)
                    docs_contents.append({"nombre": doc.get("nombre"), "ruta": ruta, "contenido": txt})
                except Exception as e:
                    logging.exception(f"Error parseando documento {ruta}: {e}")
            else:
                logging.warning(f"Ruta no existe o falta para doc: {doc}")

        # 3) construir prompt maestro con prompt.build_prompt
        prompt_text = build_prompt(question, docs_contents)

        # 4) llamar a ollama.chat (Gemma3) con prompt_text
        respuesta = ollama.chat(model="gemma3", messages=[{"role": "user", "content": prompt_text}])

        # 5) extraer texto respuesta (seguridad)
        answer_text = None
        try:
            answer_text = respuesta["message"]["content"]
        except Exception:
            # fallback: stringify
            answer_text = str(respuesta)

        TASKS[task_id]["status"] = "finished"
        TASKS[task_id]["answer"] = answer_text

    except Exception as e:
        logging.exception(f"❌ Error en task {task_id}: {e}")
        TASKS[task_id]["status"] = "error"
        TASKS[task_id]["error"] = str(e)
