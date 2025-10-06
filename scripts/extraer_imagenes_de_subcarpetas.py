# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2025-08-08 09:33:29
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2025-10-04 21:07:18
import os
import shutil
import hashlib
import json
from datetime import datetime

# ==== Configura aquí ====
CARPETA_RAIZ = "/Users/ikioriy/Downloads/fotos_bitform_albert/1"
EXTENSIONES = (".jpg", ".jpeg", "JPG", "JPEG", ".png", ".gif", ".bmp", ".tiff", ".webp")
MANIFEST_PATH = os.path.join(CARPETA_RAIZ, "manifest_copias.json")
LOG_PATH = os.path.join(
    CARPETA_RAIZ,
    f"nuevas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
)
# ========================

def md5_de_archivo(path, chunk_size=1024 * 1024):
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def cargar_manifest():
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # Si el manifest se corrompe, empezamos de cero
            return {"hashes": {}, "archivos": []}
    return {"hashes": {}, "archivos": []}

def guardar_manifest(manifest):
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def nombre_disponible(dest_dir, nombre):
    """
    Si existe un archivo con el mismo nombre, agrega _1, _2, ... hasta encontrar disponible.
    """
    base, ext = os.path.splitext(nombre)
    candidato = os.path.join(dest_dir, nombre)
    contador = 1
    while os.path.exists(candidato):
        candidato = os.path.join(dest_dir, f"{base}_{contador}{ext}")
        contador += 1
    return candidato

def es_imagen(nombre):
    return nombre.lower().endswith(EXTENSIONES)

def main():
    os.makedirs(CARPETA_RAIZ, exist_ok=True)
    manifest = cargar_manifest()
    hashes = manifest.get("hashes", {})  # hash -> ruta_destino
    nuevas = []

    with open(LOG_PATH, "w", encoding="utf-8") as log:
        for carpeta_actual, _, archivos in os.walk(CARPETA_RAIZ):
            # saltar la raíz al listar destino para no re-procesar lo ya copiado
            # pero sí recorrer subcarpetas
            for archivo in archivos:
                ruta_origen = os.path.join(carpeta_actual, archivo)

                # No procesar archivos que ya están en la raíz (nivel 0)
                if carpeta_actual == CARPETA_RAIZ:
                    continue

                if not es_imagen(archivo):
                    continue

                try:
                    hash_archivo = md5_de_archivo(ruta_origen)
                except Exception as e:
                    print(f"⚠️  No se pudo calcular hash de: {ruta_origen} ({e})")
                    continue

                # Si ya vimos este hash antes, saltamos (ya fue copiado)
                if hash_archivo in hashes:
                    continue

                # Proponer nombre destino (con colisión-resolver)
                destino_propuesto = nombre_disponible(CARPETA_RAIZ, archivo)

                # Copiar conservando metadatos
                shutil.copy2(ruta_origen, destino_propuesto)

                # Actualizar manifest
                hashes[hash_archivo] = destino_propuesto
                manifest.setdefault("archivos", []).append({
                    "hash": hash_archivo,
                    "origen": ruta_origen,
                    "destino": destino_propuesto,
                    "fecha": datetime.now().isoformat(timespec="seconds")
                })

                # Registrar en el log
                log.write(f"{ruta_origen} -> {destino_propuesto}\n")
                nuevas.append(destino_propuesto)

        # Guardar manifest al final
        manifest["hashes"] = hashes
        guardar_manifest(manifest)

    if nuevas:
        print(f"✅ {len(nuevas)} imagen(es) nueva(s) copiadas. Log: {LOG_PATH}")
    else:
        print("ℹ️ No se encontraron imágenes nuevas. Aún así se generó el log vacío:")
        print(LOG_PATH)

if __name__ == "__main__":
    main()
