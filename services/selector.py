# services/selector.py
from database.neo4j import get_documents
import re

# ----------------------------
# Normalización
# ----------------------------
def normalize_text(s: str):
    return s.lower().replace("_", " ").strip()

# ----------------------------
# Extrae mes y año desde nombre archivo
# ----------------------------
def match_month_year_from_name(name: str):
    name_l = name.lower()
    meses = {
        "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
        "julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12
    }

    # Buscar mes por palabra
    for mname, mi in meses.items():
        if mname in name_l:
            ys = re.findall(r'20\d{2}', name)
            year = int(ys[0]) if ys else None
            return mi, year

    # Solo año si no detectó mes
    ys = re.findall(r'(20\d{2})', name)
    if ys:
        return None, int(ys[0])

    return None, None

# ----------------------------
# Selección simple de un documento por CMF/mes/año
# ----------------------------
def select_document(cmf=None, month=None, year=None):
    docs = get_documents()
    if not docs:
        return None

    # Normalizar mes
    if isinstance(month, str):
        try:
            month = month.strip().lower()
            meses = {
                "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
                "julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12
            }
            month = meses.get(month, None) or int(month)
        except Exception:
            month = None

    candidates = []
    for doc in docs:
        name = doc.get("nombre", "")
        rmonth, ryear = match_month_year_from_name(name)
        score = 0

        # Año exacto
        if year and ryear and int(ryear) == int(year):
            score += 3

        # Mes exacto
        if month and rmonth and int(rmonth) == int(month):
            score += 4

        # CMF en nombre
        if cmf:
            if cmf.lower() in name.lower():
                score += 5
            if any(token in name.lower() for token in cmf.lower().split()):
                score += 1

        candidates.append((score, doc))

    candidates = sorted(candidates, key=lambda x: x[0], reverse=True)
    best = candidates[0][1] if candidates and candidates[0][0] > 0 else None

    # Si no encuentra pero año coincide, devuelve último del año
    if not best and year:
        year_docs = [d for d in docs if str(year) in d.get("nombre", "")]
        if year_docs:
            return sorted(year_docs, key=lambda x: x.get("nombre", ""))[-1]

    return best

# ----------------------------------------------------
# FUNCIÓN QUE FALTABA  (para arreglar tu ERROR)
# Esta función analiza la pregunta y selecciona documentos
# ----------------------------------------------------
def select_documents_for_question(question: str, documentos: list):
    question_l = question.lower()

    # Mapas de meses
    meses = {
        "enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,
        "julio":7,"agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12
    }

    detected_month = None
    detected_year = None

    # Buscar mes en pregunta
    for mname, mid in meses.items():
        if mname in question_l:
            detected_month = mid

    # Buscar año en pregunta
    years = re.findall(r"20\d{2}", question_l)
    if years:
        detected_year = int(years[0])

    # Filtrado básico
    selected = []

    for doc in documentos:
        nombre = doc["nombre"].lower()
        score = 0

        if detected_year and str(detected_year) in nombre:
            score += 4

        if detected_month:
            for mname in meses.keys():
                if mname in nombre:
                    if meses[mname] == detected_month:
                        score += 5

        selected.append((score, doc))

    selected = sorted(selected, key=lambda x: x[0], reverse=True)

    # Retornar los mejores 1-3 documentos
    top_docs = [doc for score, doc in selected if score > 0][:3]

    # Si no encontró nada, devolver todos (fallback)
    return top_docs if top_docs else [d for _, d in selected[:3]]
