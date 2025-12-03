# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2025-08-18 17:33:38
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2025-08-18 20:35:14
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
import pandas as pd
from urllib.parse import urlparse, parse_qs


# ----------------------------
# Utilidades
# ----------------------------
def log(msg: str):
    print(f"[INFO] {msg}")


def warn(msg: str):
    print(f"[WARN] {msg}")


# ----------------------------
# 1) Carga de entradas
# ----------------------------
def load_inputs(input_path: str, map_path: str, sheet: str | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No se encontró el archivo de datos: {input_path}")
    if not os.path.exists(map_path):
        raise FileNotFoundError(f"No se encontró el archivo de mapeo: {map_path}")

    log(f"Cargando datos desde: {input_path}")
    actual_sheet_name = 0 if sheet is None else sheet
    
    # Intentar leer primero con header=0 (por defecto)
    df = pd.read_excel(input_path, sheet_name=actual_sheet_name, engine="openpyxl")
    
    # Si la primera columna tiene muchas columnas "Unnamed", intentar con header=1
    unnamed_count = sum(1 for col in df.columns if str(col).startswith('Unnamed:'))
    if unnamed_count > len(df.columns) * 0.7:  # Si más del 70% son Unnamed
        log("Detectado archivo con encabezados en fila 2, releyendo...")
        df = pd.read_excel(input_path, sheet_name=actual_sheet_name, engine="openpyxl", header=1)
    
    # Asegurar nombres de columnas como str
    df.columns = [str(c).strip() for c in df.columns]

    log(f"Cargando mapeo desde: {map_path}")
    map_df = pd.read_csv(map_path, dtype=str).fillna("")
    if "input" not in map_df.columns or "output" not in map_df.columns:
        raise ValueError("mapeo.csv debe tener las columnas: input, output")

    # Limpieza básica
    map_df["input"] = map_df["input"].str.strip()
    map_df["output"] = map_df["output"].str.strip()

    return df, map_df


# ----------------------------
# 2) Detección de bloques de alumnos y autorizados
# ----------------------------
def detect_student_blocks(columns: list[str]) -> dict[int, dict[str, str]]:
    """
    Devuelve un dict:
      { idx: { campo_normalizado: nombre_columna_original, ... }, ... }

    Campos normalizados que generaremos:
      alumno_nombre, alumno_apellidos, alumno_curp, alumno_nivel, alumno_grado,
      alumno_grupo, alumno_tipo_sangre, alumno_clave_instituto, alumno_info_medica,
      alumno_matricula, alumno_domicilio, alumno_foto
    """
    # Patrones por atributo con un grupo de captura para el índice (\d+)
    patterns = {
        "alumno_nombre": r"^Nombre alumno\s+(\d+)$",
        "alumno_apellidos": r"^Apellidos alumno\s+(\d+)$",
        "alumno_curp": r"^CURP alumno\s+(\d+)$",
        "alumno_nivel": r"^Nivel escolar alumno\s+(\d+)$",
        "alumno_grado": r"^Grado alumno\s+(\d+)$",
        "alumno_grupo": r"^Grupo alumno\s+(\d+)$",
        "alumno_tipo_sangre": r"^Tipo de sangre alumno\s+(\d+)$",
        "alumno_clave_instituto": r"^Clave del instituto alumno\s+(\d+)$",
        "alumno_info_medica": r"^Información medica del alumno\s+(\d+)$",
        # aceptar acento en Matrícula
        "alumno_matricula": r"^Matr[ií]cula alumno\s+(\d+)$",
        "alumno_domicilio": r"^Domicilio alumno\s+(\d+)$",
        "alumno_foto": r"^Foto del alumno\s+(\d+)$",
    }

    blocks: dict[int, dict[str, str]] = {}
    for col in columns:
        for field, pat in patterns.items():
            m = re.match(pat, col, flags=re.IGNORECASE)
            if m:
                idx = int(m.group(1))
                if idx not in blocks:
                    blocks[idx] = {}
                blocks[idx][field] = col
                break

    if not blocks:
        warn("No se detectaron columnas por patrón de 'alumno N'. "
             "Si tus encabezados difieren, ajusta los regex en detect_student_blocks().")
    else:
        log(f"Bloques de alumnos detectados: {sorted(blocks.keys())}")
    return blocks


def detect_authorized_blocks(columns: list[str]) -> dict[int, dict[str, str]]:
    """
    Detecta bloques de personas autorizadas por patrón similar a alumnos.
    
    Campos que buscamos:
      nombre_autorizado, apellidos_autorizado, foto_autorizado
    """
    patterns = {
        "nombre_autorizado": r"^Nombre autorizado\s+(\d+)$",
        "apellidos_autorizado": r"^Apellidos autorizado\s+(\d+)$",
        "foto_autorizado": r"^Foto autorizado\s+(\d+)$",
    }
    
    blocks: dict[int, dict[str, str]] = {}
    for col in columns:
        for field, pat in patterns.items():
            m = re.match(pat, col, flags=re.IGNORECASE)
            if m:
                idx = int(m.group(1))
                if idx not in blocks:
                    blocks[idx] = {}
                blocks[idx][field] = col
                break
    
    if blocks:
        log(f"Bloques de autorizados detectados: {sorted(blocks.keys())}")
    
    return blocks


def extract_file_id_from_url(url: str) -> str:
    """
    Extrae el fileID de una URL como:
    https://miescuela.net/bitforms/bitforms-file/?formID=1&entryID=77&fileID=IMG_20250716_180129_HDR.jpg
    
    Retorna el fileID o cadena vacía si no se encuentra.
    """
    if not url or pd.isna(url):
        return ""
    
    try:
        parsed = urlparse(str(url))
        query_params = parse_qs(parsed.query)
        file_id = query_params.get('fileID', [''])[0]
        return file_id
    except Exception:
        return ""


def process_authorized_data(df: pd.DataFrame, authorized_blocks: dict[int, dict[str, str]]) -> pd.DataFrame:
    """
    Procesa los datos de autorizados agregando:
    1. Columnas nombre_completo_autorizado_N (nombre + apellidos)
    2. Columnas foto_autorizado_N_normalizado (fileID extraído de URL)
    """
    df = df.copy()
    
    if not authorized_blocks:
        log("No se detectaron bloques de autorizados para procesar.")
        return df
    
    for idx in sorted(authorized_blocks.keys()):
        mapping = authorized_blocks[idx]
        
        # 1. Crear columna nombre_completo_autorizado_N
        nombre_col = mapping.get("nombre_autorizado")
        apellidos_col = mapping.get("apellidos_autorizado")
        
        if nombre_col and apellidos_col:
            nombre_completo_col = f"nombre_completo_autorizado_{idx}"
            
            # Combinar nombre y apellidos, manejando valores nulos/vacíos
            if nombre_col in df.columns and apellidos_col in df.columns:
                df[nombre_completo_col] = df.apply(
                    lambda row: combine_name_lastname(
                        row.get(nombre_col), 
                        row.get(apellidos_col)
                    ), 
                    axis=1
                )
                log(f"Creada columna: {nombre_completo_col}")
        
        # 2. Crear columna foto_autorizado_N_normalizado
        foto_col = mapping.get("foto_autorizado")
        if foto_col and foto_col in df.columns:
            foto_normalizado_col = f"foto_autorizado_{idx}_normalizado"
            df[foto_normalizado_col] = df[foto_col].apply(extract_file_id_from_url)
            log(f"Creada columna: {foto_normalizado_col}")
    
    return df


def combine_name_lastname(nombre, apellidos):
    """
    Combina nombre y apellidos manejando valores nulos/vacíos.
    """
    nombre_str = str(nombre).strip() if pd.notna(nombre) else ""
    apellidos_str = str(apellidos).strip() if pd.notna(apellidos) else ""
    
    # Si ambos están vacíos, devolver cadena vacía
    if not nombre_str and not apellidos_str:
        return ""
    
    # Combinar con espacio, eliminando espacios extra
    return f"{nombre_str} {apellidos_str}".strip()


# ----------------------------
# 3) Normalización (unpivot a filas por alumno)
# ----------------------------
def normalize_students(df: pd.DataFrame, blocks: dict[int, dict[str, str]]) -> pd.DataFrame:
    if not blocks:
        log("Sin bloques de alumnos; se devuelve el DataFrame original.")
        return df.copy()

    # Columnas implicadas en alumnos
    student_cols = set()
    for d in blocks.values():
        student_cols.update(d.values())

    # Columnas meta: todas las que NO son de alumnos
    meta_cols = [c for c in df.columns if c not in student_cols]

    # Ordenar índices de alumnos
    idxs = sorted(blocks.keys())

    normalized_rows = []
    for _, row in df.iterrows():
        for idx in idxs:
            mapping = blocks[idx]

            # Construir nueva fila: primero metadatos
            new_row = {c: row.get(c, None) for c in meta_cols}

            # Rellenar campos unificados del alumno
            fields = [
                "alumno_nombre", "alumno_apellidos", "alumno_curp", "alumno_nivel",
                "alumno_grado", "alumno_grupo", "alumno_tipo_sangre",
                "alumno_clave_instituto", "alumno_info_medica",
                "alumno_matricula", "alumno_domicilio", "alumno_foto"
            ]

            all_empty = True
            for f in fields:
                orig_col = mapping.get(f)
                val = row.get(orig_col) if orig_col in row.index else None
                # Considerar vacío si es NaN o cadena vacía tras strip
                if pd.notna(val) and str(val).strip() != "":
                    all_empty = False
                new_row[f] = val

            # Si todas las columnas del alumno están vacías, no generar fila
            if all_empty:
                continue

            new_row["alumno_index"] = idx
            normalized_rows.append(new_row)

    if not normalized_rows:
        warn("Tras la normalización no se generaron filas (quizá todos los bloques están vacíos).")
        # Devolver df original para no romper flujo
        return df.copy()

    ndf = pd.DataFrame(normalized_rows)
    log(f"Filas originales: {len(df)}  ->  Filas normalizadas: {len(ndf)}")
    return ndf


# ----------------------------
# 4) Aplicar mapeo (input/output)
# ----------------------------
def apply_mapping(df: pd.DataFrame, map_df: pd.DataFrame, preserve_student_columns: bool = False) -> pd.DataFrame:
    """
    - Si output == 'eliminar' -> descartar columna 'input' si existe.
    - Si output == '' (vacío)  -> mantener nombre original.
    - Si output != '' y != 'eliminar' -> renombrar input -> output.
    - Si preserve_student_columns=True, no eliminar columnas de alumnos para permitir unpivot posterior
    """
    df = df.copy()
    
    # Patrones de columnas de alumnos que NO debemos eliminar antes del unpivot
    student_patterns = [
        r"^Nombre alumno\s+\d+$",
        r"^Apellidos alumno\s+\d+$", 
        r"^CURP alumno\s+\d+$",
        r"^Nivel escolar alumno\s+\d+$",
        r"^Grado alumno\s+\d+$",
        r"^Grupo alumno\s+\d+$",
        r"^Tipo de sangre alumno\s+\d+$",
        r"^Clave del instituto alumno\s+\d+$",
        r"^Información medica del alumno\s+\d+$",
        r"^Matr[ií]cula alumno\s+\d+$",
        r"^Domicilio alumno\s+\d+$",
        r"^Foto del alumno\s+\d+$"
    ]
    
    def is_student_column(col_name):
        for pattern in student_patterns:
            if re.match(pattern, col_name, flags=re.IGNORECASE):
                return True
        return False

    # Primero eliminar
    to_drop = []
    for _, r in map_df.iterrows():
        src = r["input"]
        dst = r["output"]
        if dst.lower() == "eliminar":
            if src in df.columns:
                # Si estamos preservando columnas de alumnos, no las eliminamos
                if preserve_student_columns and is_student_column(src):
                    continue
                to_drop.append(src)
            else:
                warn(f"Mapa 'eliminar': columna no encontrada '{src}'")

    if to_drop:
        log(f"Eliminando columnas (mapeo): {to_drop}")
        df = df.drop(columns=[c for c in to_drop if c in df.columns], errors="ignore")

    # Luego renombrar
    rename_map = {}
    for _, r in map_df.iterrows():
        src = r["input"]
        dst = r["output"]
        if dst == "" or dst.lower() == "eliminar":
            continue
        if src not in df.columns:
            warn(f"Mapa 'renombrar': columna no encontrada '{src}' -> '{dst}'")
            continue
        if src != dst:
            rename_map[src] = dst

    if rename_map:
        log(f"Renombrando columnas: {rename_map}")
        df = df.rename(columns=rename_map)

    return df


# ----------------------------
# 5) División por clave de instituto
# ----------------------------
def guess_institute_column(columns: list[str]) -> str | None:
    """
    Intenta adivinar la columna de clave del instituto (post-mapeo).
    Prioriza nombres frecuentes; ajustar si usas otra convención.
    """
    candidates = [
        "alumno_clave_instituto",
        "Clave del instituto",
        "Clave del instituto alumno",
        "clave_instituto",
        "instituto",
        "clave",
    ]
    for name in candidates:
        if name in columns:
            return name
    return None


def split_by_institute(df: pd.DataFrame, institute_col: str | None, outdir: str):
    if institute_col is None:
        institute_col = guess_institute_column(df.columns.tolist())

    if institute_col is None or institute_col not in df.columns:
        warn("No se encontró columna de clave del instituto; no se generarán archivos por clave.")
        return

    os.makedirs(outdir, exist_ok=True)
    cleaned_institute_values = df[institute_col].astype(str).str.strip()
    uniques = sorted(set(cleaned_institute_values[cleaned_institute_values != ""].dropna().unique()))

    if not uniques:
        warn("No hay valores de clave para dividir; se omitió la exportación por clave.")
        return

    for val in uniques:
        subset = df[cleaned_institute_values == val]
        # Sanitizar nombre de archivo
        safe = re.sub(r"[^\w\-\.]+", "_", val)
        path = os.path.join(outdir, f"{safe}.xlsx")
        subset.to_excel(path, index=False, engine="openpyxl")
        log(f"Exportado: {path}  (filas={len(subset)})")


# ----------------------------
# main
# ----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Normaliza alumnos (unpivot), aplica mapeo (input/output) y divide por clave de instituto."
    )
    parser.add_argument("--input", required=True, help="Ruta a input.xlsx")
    parser.add_argument("--map", required=True, help="Ruta a mapeo.csv (columnas: input,output)")
    parser.add_argument("--outdir", default="out", help="Directorio de salida (por defecto: out)")
    parser.add_argument("--sheet", default=None, help="Nombre de la hoja a leer (por defecto, la primera)")
    args = parser.parse_args()

    # 1) Cargar
    df_raw, map_df = load_inputs(args.input, args.map, args.sheet)

    # 2) Detectar bloques de autorizados y procesar sus datos
    authorized_blocks = detect_authorized_blocks(df_raw.columns.tolist())
    df_with_authorized = process_authorized_data(df_raw, authorized_blocks)

    # 3) Aplicar mapeo inicial (eliminar/renombrar) pero preservando columnas de alumnos
    log("Aplicando mapeo inicial (preservando columnas de alumnos para unpivot)...")
    df_pre_mapped = apply_mapping(df_with_authorized, map_df, preserve_student_columns=True)

    # 4) Detectar bloques y normalizar alumnos (unpivot)
    blocks = detect_student_blocks(df_pre_mapped.columns.tolist())
    df_norm = normalize_students(df_pre_mapped, blocks)

    # 5) Aplicar mapeo final (para las columnas normalizadas de alumnos)
    log("Aplicando mapeo final...")
    df_mapped = apply_mapping(df_norm, map_df, preserve_student_columns=False)

    # 6) Export general (opcional)
    os.makedirs(args.outdir, exist_ok=True)
    full_out = os.path.join(args.outdir, "full_normalized_mapped.xlsx")
    df_mapped.to_excel(full_out, index=False, engine="openpyxl")
    log(f"Exportado dataset completo: {full_out} (filas={len(df_mapped)}, cols={len(df_mapped.columns)})")

    # 7) Dividir por clave de instituto
    split_by_institute(df_mapped, institute_col=None, outdir=args.outdir)

    log("Proceso finalizado.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
