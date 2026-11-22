"""Reportes en CSV armados desde las tablas de gold.

La unica excepcion es calidad_por_anio, que necesita los conteos de bronze y silver.
"""
import pandas as pd

from src import bronze, gold, silver

REPORTES = gold.GOLD / "reportes"


def leer_gold(nombre: str) -> pd.DataFrame:
    return pd.read_parquet(gold.GOLD / f"{nombre}.parquet")


def viajes_por_mes(fact, dim_fecha) -> pd.DataFrame:
    df = fact[["fecha_key"]].merge(dim_fecha[["fecha_key", "anio", "mes"]], on="fecha_key")
    return df.groupby(["anio", "mes"]).size().reset_index(name="cantidad_viajes")


def top10_estaciones_por_anio(fact, dim_fecha, dim_estacion) -> pd.DataFrame:
    df = fact[["fecha_key", "id_estacion_origen"]].merge(dim_fecha[["fecha_key", "anio"]], on="fecha_key")
    conteo = df.groupby(["anio", "id_estacion_origen"]).size().reset_index(name="cantidad_viajes")

    # si hay empate en cantidad desempata el id, asi el ranking siempre sale igual
    conteo = conteo.sort_values(["anio", "cantidad_viajes", "id_estacion_origen"], ascending=[True, False, True])
    conteo["ranking"] = conteo.groupby("anio").cumcount() + 1
    top = conteo[conteo["ranking"] <= 10].merge(
        dim_estacion[["id_estacion", "nombre_estacion"]], left_on="id_estacion_origen", right_on="id_estacion"
    )
    return top[["anio", "ranking", "nombre_estacion", "cantidad_viajes"]]


def duracion_por_rango_y_genero(fact, dim_usuario) -> pd.DataFrame:
    # inner join: solo entran los viajes cuyo usuario esta en dim_usuario
    df = fact[["id_usuario", "duracion_min"]].merge(
        dim_usuario[["id_usuario", "rango_etario", "genero"]], on="id_usuario"
    )
    resultado = df.groupby(["rango_etario", "genero"]).agg(
        cantidad_viajes=("duracion_min", "size"),
        duracion_promedio_min=("duracion_min", "mean"),
    ).reset_index()
    resultado["duracion_promedio_min"] = resultado["duracion_promedio_min"].round(1)
    return resultado


def viajes_circulares(fact, dim_fecha) -> pd.DataFrame:
    df = fact[["fecha_key", "es_circular"]].merge(dim_fecha[["fecha_key", "anio"]], on="fecha_key")
    resultado = df.groupby("anio").agg(
        total_viajes=("es_circular", "size"),
        viajes_circulares=("es_circular", "sum"),
    ).reset_index()
    resultado["porcentaje_circulares"] = (resultado["viajes_circulares"] / resultado["total_viajes"] * 100).round(1)
    return resultado


def calidad_por_anio() -> pd.DataFrame:
    filas_bronze = bronze.contar_filas("recorridos")
    filas_silver = pd.read_parquet(silver.SILVER / "viajes.parquet", columns=["anio_fuente"])["anio_fuente"].value_counts()
    filas_cuarentena = pd.read_parquet(
        silver.SILVER / "viajes_cuarentena.parquet", columns=["anio_fuente"]
    )["anio_fuente"].value_counts()

    resultado = pd.DataFrame({"anio": list(filas_bronze), "filas_bronze": list(filas_bronze.values())})
    resultado["filas_silver"] = resultado["anio"].map(filas_silver).fillna(0).astype(int)
    resultado["filas_cuarentena"] = resultado["anio"].map(filas_cuarentena).fillna(0).astype(int)
    resultado["porcentaje_cuarentena"] = (resultado["filas_cuarentena"] / resultado["filas_bronze"] * 100).round(2)
    return resultado


def ejecutar() -> None:
    REPORTES.mkdir(parents=True, exist_ok=True)
    fact = leer_gold("fact_viajes")
    dim_fecha = leer_gold("dim_fecha")
    dim_estacion = leer_gold("dim_estacion")
    dim_usuario = leer_gold("dim_usuario")

    reportes = {
        "viajes_por_mes": viajes_por_mes(fact, dim_fecha),
        "top10_estaciones_por_anio": top10_estaciones_por_anio(fact, dim_fecha, dim_estacion),
        "duracion_por_rango_y_genero": duracion_por_rango_y_genero(fact, dim_usuario),
        "viajes_circulares": viajes_circulares(fact, dim_fecha),
        "calidad_por_anio": calidad_por_anio(),
    }
    for nombre, df in reportes.items():
        df.to_csv(REPORTES / f"{nombre}.csv", index=False)
        print(f"  reportes/{nombre}.csv: {len(df)} filas")
