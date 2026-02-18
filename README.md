 API de Análisis Inteligente de Documentos con FastAPI, Neo4j y LLM

 Descripción general

Este proyecto implementa una API REST desarrollada con FastAPI cuyo objetivo es permitir la consulta inteligente de documentos (principalmente archivos Excel) utilizando modelos de lenguaje (LLM) y una base de datos orientada a grafos (Neo4j).

El sistema está diseñado para:
- Almacenar documentos subidos por el usuario.
- Analizar su contenido (especialmente hojas de tipo CONSOLIDADO).
- Seleccionar automáticamente los documentos más relevantes según una pregunta.
- Generar respuestas en lenguaje natural apoyadas en los datos reales de los documentos.

Este enfoque resulta especialmente útil en contextos académicos o institucionales donde se manejan reportes mensuales, balances, consolidados financieros o estadísticos, y se requiere una forma más natural de interactuar con ellos.

---

 Arquitectura general del sistema

El sistema combina varias tecnologías:

- FastAPI: Framework principal para la construcción de la API.
- Neo4j: Base de datos de grafos para almacenar metadatos de los documentos.
- Ollama + Gemma 3: Modelo de lenguaje utilizado para responder preguntas.
- Pandas: Procesamiento de archivos Excel.
- Multithreading: Para manejar consultas largas sin bloquear la API.

La arquitectura sigue un flujo claro:

1. El usuario sube documentos.
2. Los documentos se almacenan y registran en Neo4j.
3. El usuario formula una pregunta.
4. El sistema selecciona los documentos más relevantes.
5. Se construye un *prompt* contextual.
6. El modelo de lenguaje genera una respuesta.
7. El usuario consulta el resultado de forma asíncrona.

---
## Estructura del proyecto
- main.py Archivo principal de la API
- uploads/  Carpeta donde se almacenan los archivos subidos
- services/
- selector.py  Lógica de selección de documentos relevantes
- parser.py  Extracción de texto desde Excel
- prompt.py  Construcción del prompt para el LLM
- database/
- neo4j.py  Conexión y operaciones con Neo4j

Cuando se recibe una pregunta, el sistema ejecuta los siguientes pasos:

Selección de documentos relevantes
Se aplican heurísticas basadas en:

Meses

Años

Palabras clave

Contexto de la pregunta

Procesamiento de documentos
Se extrae texto estructurado desde los Excel seleccionados.

Construcción del prompt
Se genera un prompt contextual que incluye:

La pregunta del usuario

Fragmentos relevantes de los documentos

Consulta al modelo de lenguaje (Gemma 3)
El modelo genera una respuesta basada únicamente en la información proporcionada.

Entrega del resultado
La respuesta se almacena y queda disponible para consulta.
