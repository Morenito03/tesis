# services/parser.py
import pandas as pd
import os

def find_consolidado_sheet(excel_path):
    xls = pd.ExcelFile(excel_path)
    # buscar hoja que contenga 'consolid' (case-insensitive)
    for sheet in xls.sheet_names:
        if 'consolid' in sheet.lower() or 'consolida' in sheet.lower():
            return sheet
    # fallback primera hoja
    return xls.sheet_names[0]

def parse_consolidado(excel_path):
    """
    Lee la hoja consolidado y devuelve:
    {
      "nombre": "archivo",
      "ruta": "...",
      "year": 2024,
      "month": 1,
      "consultorios": {
         "CONS 10": {"TTL/GRAL": 20, "dias": {1: 2, 2:5, ...}, "conceptos": {"CONSULTA MEDICINA": {...}} },
         ...
      },
      "meta": {...}
    }
    Nota: la función intenta leer tablas por patrones.
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError(excel_path)

    sheet = find_consolidado_sheet(excel_path)
    df = pd.read_excel(excel_path, sheet_name=sheet, header=None, engine='xlrd' if excel_path.lower().endswith('.xls') else None)

    # heurística: buscar la fila donde aparece la palabra 'CONCEPTOS' o 'TOTAL GENERAL'
    text = df.astype(str).apply(lambda row: ' '.join(row.values), axis=1).str.lower()
    idx_conceptos = text[text.str.contains('conceptos')].index
    idx_ttl = text[text.str.contains('total general')].index

    result = {"ruta": excel_path, "sheet": sheet, "consultorios": {}}

    # Intento simple: si hay 'CONSULTA' y luego columnas de conceptos, leer bloque
    # (Esto necesita adaptación a tu excel exacto; aquí damos una base robusta)
    try:
        # Buscar filas con 'CONSULTA' o 'CONS'
        rows_with_cons = df[df.apply(lambda r: r.astype(str).str.contains('consulta|cons', case=False).any(), axis=1)]
        # Si no se detecta, retornamos un resumen simple (nº filas/cols)
        if rows_with_cons.empty:
            # fallback: devolver conteo de celdas no-nulas como 'total'
            total_non_null = df.count().sum()
            result["note"] = "No se detectó bloque de consultorios; revisar manualmente."
            result["fallback_total_cells"] = int(total_non_null)
            return result

        # Heurística: buscar encabezados de conceptos en la fila donde aparece 'CONCEPTOS'
        header_row_idx = idx_conceptos[0] if len(idx_conceptos) else None
        if header_row_idx is not None:
            headers = df.iloc[header_row_idx].fillna('').astype(str).tolist()
        else:
            headers = df.iloc[0].fillna('').astype(str).tolist()

        # construir mapeo de columnas de interés (buscar TTL/GRAL o Total general)
        ttl_col = None
        for i, h in enumerate(headers):
            if 'ttl' in h.lower() or 'total' in h.lower() or 'gral' in h.lower() or 'ttl / gral' in h.lower():
                ttl_col = i
                break

        # Buscar bloques por consultorio (heurística)
        # Encontrar filas que tengan nombres de consultorios (por ejemplo 'CONSULTA PEDIATRIA', 'CONSULTA MEDICINA', etc)
        for idx, row in df.iterrows():
            rstr = ' '.join(row.fillna('').astype(str)).lower()
            if 'consulta ' in rstr or 'consulta' in rstr and any(str(i) in rstr for i in range(1, 50)):
                # tomar el nombre completo de la celda más probable
                # iterar celdas para encontrar la que contiene 'consulta'
                for col_idx, val in enumerate(row):
                    if isinstance(val, str) and 'consulta' in val.lower():
                        consult_name = val.strip()
                        # buscar ttl value en la misma fila
                        ttl_value = None
                        if ttl_col is not None:
                            try:
                                ttl_value = int(df.iloc[idx, ttl_col]) if not pd.isna(df.iloc[idx, ttl_col]) else None
                            except Exception:
                                ttl_value = None
                        result["consultorios"][consult_name] = {"ttl": ttl_value}
                        break
        return result
    except Exception as e:
        return {"error": str(e), "note": "Parser necesita ajuste para este formato de Excel."}
# services/parser.py

import pandas as pd

def parse_consolidado_text(path: str) -> str:
    """
    Lee la hoja CONSOLIDADO si existe.
    Si no, toma la primera hoja.
    Devuelve un texto limpio para usar como contexto.
    """

    try:
        # Intentar cargar hoja CONSOLIDADO
        df = pd.read_excel(path, sheet_name="CONSOLIDADO")
    except Exception:
        # Fallback: primera hoja
        df = pd.read_excel(path)

    # Convertir DataFrame a texto limpio
    text = df.to_string(index=False)

    return text
