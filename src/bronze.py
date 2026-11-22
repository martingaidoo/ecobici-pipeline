"""Capa bronze: copia fiel de los archivos de data/raw en Parquet.

No se limpia nada. Todo se lee como texto y se agregan 3 columnas de metadatos.
"""
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

DATA = Path(__file__).resolve().parent.parent / "data"
RAW = DATA / "raw"
BRONZE = DATA / "bronze"

ARCHIVOS = {
    "recorridos": {
        2016: "recorridos-realizados-2016.zip",
        2019: "recorridos-realizados-2019.zip",
        2024: "recorridos-realizados-2024.zip",
    },
    "usuarios": {
        2016: "usuarios-ecobici-2016.csv",
        2019: "usuarios_ecobici_2019.csv",
        2024: "usuarios_ecobici_2024.csv",
    },
}

# el csv de 2019 descomprimido pesa casi 2 GB, por eso leo por partes
TAMANIO_CHUNK = 500_000


def ingestar_archivo(ruta: Path, anio: int, destino: Path, fecha_ingesta: str) -> int:
    """Lee un archivo de raw tal cual viene y lo guarda en destino/anio=XXXX/data.parquet.

    keep_default_na=False para que los vacios y los "NA" queden como texto,
    igual que en el archivo original. La limpieza es trabajo de silver.
    """
    carpeta = destino / f"anio={anio}"
    carpeta.mkdir(parents=True, exist_ok=True)
    archivo_salida = carpeta / "data.parquet"

    lector = pd.read_csv(
        ruta,
        compression="infer",  # los .zip se leen directo, sin descomprimir a mano
        dtype=str,
        keep_default_na=False,
        chunksize=TAMANIO_CHUNK,
    )

    filas = 0
    writer = None
    try:
        for chunk in lector:
            chunk["_archivo_origen"] = ruta.name
            chunk["_fecha_ingesta"] = fecha_ingesta
            chunk["_anio"] = str(anio)

            tabla = pa.Table.from_pandas(chunk, preserve_index=False)
            if writer is None:
                # se abre en modo escritura: si el archivo ya existia se pisa (idempotencia)
                writer = pq.ParquetWriter(archivo_salida, tabla.schema)
            writer.write_table(tabla.cast(writer.schema))
            filas += len(chunk)
    finally:
        if writer is not None:
            writer.close()

    return filas


def ejecutar() -> dict:
    """Ingesta todos los archivos. Devuelve {(tipo, anio): filas}."""
    fecha_ingesta = datetime.now().isoformat(timespec="seconds")
    conteos = {}
    for tipo, archivos in ARCHIVOS.items():
        for anio, nombre in archivos.items():
            filas = ingestar_archivo(RAW / nombre, anio, BRONZE / tipo, fecha_ingesta)
            conteos[(tipo, anio)] = filas
            print(f"  bronze/{tipo}/anio={anio}: {filas:,} filas")
    return conteos


def contar_filas(tipo: str) -> dict:
    """Cantidad de filas por anio en bronze (lee solo la metadata del parquet)."""
    return {
        anio: pq.ParquetFile(BRONZE / tipo / f"anio={anio}" / "data.parquet").metadata.num_rows
        for anio in ARCHIVOS[tipo]
    }
