#!/usr/bin/env python3
"""Generate a SAF (Simple Archive Format) package from COES's working
spreadsheet ("Publicaciones web" sheet), for a flat metadata-only load
(no entities/relationships, no bitstream files yet) into a DSpace collection.

Mapping follows Mapeo_Campos_COES_DSpace.xlsx in this same folder.

Usage:
    python3 build_saf_coes.py <xlsx_path> <output_dir> [--limit N] [--start N] [--end N]
"""
import argparse
import os
import shutil
import openpyxl

COLLECTION_HANDLE = "123456789/2"  # Publicaciones

# Column positions in the "Publicaciones web" sheet (header row = row 3)
POS = dict(
    coes_id=0, numero_serie=4, titulo=9, autor=10, autor_revisar=11,
    fecha_publicacion=12, tipo_documento=13, resumen=14, palabras_clave=15,
    idioma=16, publicador=17, cita=18, fuente=19, doi=20,
    version=23, licencia=24, acceso=25, enlace_original=26,
)

DUBLIN_CORE_HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n<dublin_core schema="dc">\n'
DUBLIN_CORE_FOOTER = "</dublin_core>\n"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def dcvalue(element, qualifier, value):
    q = f' qualifier="{qualifier}"' if qualifier else ' qualifier="none"'
    return f'  <dcvalue element="{element}"{q}>{esc(value)}</dcvalue>\n'


def clean(v):
    if v is None:
        return None
    v = str(v).strip()
    return v if v else None


def build_item(row, collection_handle):
    get = lambda k: clean(row[POS[k]])

    coes_id = get("coes_id")
    titulo = get("titulo")
    fecha = get("fecha_publicacion")
    tipo = get("tipo_documento")
    if not (coes_id and titulo and fecha and tipo):
        return None  # missing a required DSpace field

    dc = DUBLIN_CORE_HEADER
    dc += dcvalue("title", None, titulo)
    dc += dcvalue("date", "issued", fecha)
    dc += dcvalue("type", None, tipo)

    autor = get("autor")
    if autor:
        for a in autor.split("||"):
            a = a.strip()
            if a:
                dc += dcvalue("contributor", "author", a)

    resumen = get("resumen")
    if resumen:
        dc += dcvalue("description", "abstract", resumen)

    idioma = get("idioma")
    if idioma:
        dc += dcvalue("language", "iso", idioma)

    publicador = get("publicador")
    if publicador:
        dc += dcvalue("publisher", None, publicador)

    fuente = get("fuente")
    if fuente:
        dc += dcvalue("source", None, fuente)

    cita = get("cita")
    if cita:
        dc += dcvalue("identifier", "citation", cita)

    doi = get("doi")
    if doi:
        dc += dcvalue("identifier", "doi", doi)

    enlace = get("enlace_original")
    if enlace:
        dc += dcvalue("identifier", "uri", enlace)

    serie = get("numero_serie")
    if serie:
        dc += dcvalue("relation", "ispartofseries", serie)

    version = get("version")
    if version:
        dc += dcvalue("description", "version", version)

    # Stable external key, kept for future incremental loads (dedup on re-import)
    dc += dcvalue("identifier", "other", coes_id)

    dc += DUBLIN_CORE_FOOTER

    collections_content = collection_handle + "\n"
    return coes_id, dc, collections_content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xlsx_path")
    parser.add_argument("output_dir")
    parser.add_argument("--collection", default=COLLECTION_HANDLE,
                         help="Destination collection handle (default: %(default)s)")
    parser.add_argument("--start", type=int, default=None,
                         help="Only include coes_id >= WEB-<start> (numeric part)")
    parser.add_argument("--end", type=int, default=None,
                         help="Only include coes_id <= WEB-<end> (numeric part)")
    args = parser.parse_args()

    wb = openpyxl.load_workbook(args.xlsx_path, data_only=True)
    ws = wb["Publicaciones web"]
    rows = [r for r in ws.iter_rows(min_row=4, values_only=True) if r[POS["coes_id"]]]

    if args.start is not None or args.end is not None:
        def in_range(row):
            cid = clean(row[POS["coes_id"]])
            try:
                n = int("".join(c for c in cid if c.isdigit()))
            except (TypeError, ValueError):
                return False
            if args.start is not None and n < args.start:
                return False
            if args.end is not None and n > args.end:
                return False
            return True
        rows = [r for r in rows if in_range(r)]

    if os.path.exists(args.output_dir):
        shutil.rmtree(args.output_dir)
    os.makedirs(args.output_dir, exist_ok=True)

    n = 0
    skipped = []
    for row in rows:
        result = build_item(row, args.collection)
        if result is None:
            skipped.append(row[POS["coes_id"]])
            continue
        coes_id, dc_xml, collections_content = result
        folder = os.path.join(args.output_dir, coes_id)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "dublin_core.xml"), "w", encoding="utf-8") as f:
            f.write(dc_xml)
        with open(os.path.join(folder, "collections"), "w", encoding="utf-8") as f:
            f.write(collections_content)
        n += 1

    print(f"Built {n} items at {args.output_dir}")
    if skipped:
        print(f"Skipped {len(skipped)} rows (missing required field): {skipped}")


if __name__ == "__main__":
    main()
