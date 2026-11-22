"""Capa gold: modelo estrella a partir de silver.

fact_viajes + dim_fecha, dim_estacion y dim_usuario. Uso los ids naturales como claves.
"""
import pandas as pd

from src import silver

GOLD = silver.SILVER.parent / "gold"

# armo el nombre del dia a mano para no depender del locale de la compu
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def construir_dim_fecha(viajes: pd.DataFrame) -> pd.DataFrame:
    # un dia por fila, desde el primer viaje hasta el ultimo (incluye los anios sin datos)
    inicio = viajes["fecha_hora_inicio"]
    dias = pd.date_range(inicio.min().normalize(), inicio.max().normalize(), freq="D")

    dim = pd.DataFrame({"fecha": dias})
    dim["anio"] = dim["fecha"].dt.year
    dim["mes"] = dim["fecha"].dt.month
    dim["dia"] = dim["fecha"].dt.day
    dim["fecha_key"] = (dim["anio"] * 10000 + dim["mes"] * 100 + dim["dia"]).astype("int64")
    dim["dia_semana"] = dim["fecha"].dt.dayofweek.map(dict(enumerate(DIAS)))
    dim["es_fin_de_semana"] = dim["fecha"].dt.dayofweek >= 5
    return dim[["fecha_key", "fecha", "anio", "mes", "dia", "dia_semana", "es_fin_de_semana"]]


def construir_dim_estacion(viajes: pd.DataFrame) -> pd.DataFrame:
    # junto las estaciones de origen y de destino, contando cuantas veces aparece cada nombre
    partes = []
    for lado in ("origen", "destino"):
        conteo = viajes.groupby(
            [f"id_estacion_{lado}", f"nombre_estacion_{lado}", "anio_fuente"], dropna=False
        ).size()
        conteo.index.names = ["id_estacion", "nombre_estacion", "anio"]
        partes.append(conteo)
    conteo = pd.concat(partes).groupby(level=[0, 1, 2], dropna=False).sum().reset_index(name="veces")

    # nombre del anio mas reciente. Si en ese anio hubo mas de un nombre, el mas usado.
    conteo = conteo.sort_values(["id_estacion", "anio", "veces", "nombre_estacion"])
    dim = conteo.groupby("id_estacion").agg(
        nombre_estacion=("nombre_estacion", "last"),
        primer_anio=("anio", "min"),
        ultimo_anio=("anio", "max"),
    ).reset_index()
    return dim


def construir_dim_usuario(usuarios: pd.DataFrame) -> pd.DataFrame:
    dim = usuarios[["id_usuario", "genero", "edad"]].copy()
    # silver ya dejo las edades entre 16 y 90 (o nulas)
    rango = pd.cut(dim["edad"], bins=[15, 25, 35, 50, 90], labels=["16-25", "26-35", "36-50", "51+"])
    dim["rango_etario"] = rango.astype("string").fillna("DESCONOCIDO")
    dim["anio_alta"] = usuarios["fecha_alta"].dt.year
    return dim


def construir_fact_viajes(viajes: pd.DataFrame) -> pd.DataFrame:
    inicio = viajes["fecha_hora_inicio"]
    fact = pd.DataFrame({
        "id_viaje": viajes["id_viaje"],
        "fecha_key": (inicio.dt.year * 10000 + inicio.dt.month * 100 + inicio.dt.day).astype("int64"),
        "hora_inicio": inicio.dt.hour,
        "id_estacion_origen": viajes["id_estacion_origen"],
        "id_estacion_destino": viajes["id_estacion_destino"],
        "id_usuario": viajes["id_usuario"],
        "duracion_min": (viajes["duracion_seg"] / 60).round(1),
        "es_circular": (viajes["id_estacion_origen"] == viajes["id_estacion_destino"]).astype(bool),
    })
    return fact.reset_index(drop=True)


def verificar(fact, dim_fecha, dim_estacion, dim_usuario, filas_silver) -> None:
    assert len(fact) == filas_silver, "fact_viajes no tiene las mismas filas que silver/viajes"
    assert fact["fecha_key"].isin(dim_fecha["fecha_key"]).all(), "Hay fecha_key sin dim_fecha"
    for lado in ("origen", "destino"):
        assert fact[f"id_estacion_{lado}"].isin(dim_estacion["id_estacion"]).all(), f"Estacion de {lado} sin dim"

    # no es error: hay usuarios que se dieron de alta en anios que no tenemos
    anio = fact["fecha_key"] // 10000
    sin_usuario = fact["id_usuario"].isna()
    huerfano = ~sin_usuario & ~fact["id_usuario"].isin(dim_usuario["id_usuario"])
    resumen = pd.DataFrame({
        "viajes": anio.value_counts(),
        "sin_id_usuario": sin_usuario.groupby(anio).sum(),
        "usuario_fuera_de_dim": huerfano.groupby(anio).sum(),
    }).sort_index()
    print("  viajes con id_usuario que no esta en dim_usuario:", f"{huerfano.sum():,}")
    print(resumen.to_string())


def ejecutar() -> None:
    GOLD.mkdir(parents=True, exist_ok=True)
    viajes = pd.read_parquet(silver.SILVER / "viajes.parquet")
    usuarios = pd.read_parquet(silver.SILVER / "usuarios.parquet")

    tablas = {
        "dim_fecha": construir_dim_fecha(viajes),
        "dim_estacion": construir_dim_estacion(viajes),
        "dim_usuario": construir_dim_usuario(usuarios),
        "fact_viajes": construir_fact_viajes(viajes),
    }
    verificar(tablas["fact_viajes"], tablas["dim_fecha"], tablas["dim_estacion"], tablas["dim_usuario"], len(viajes))

    for nombre, tabla in tablas.items():
        tabla.to_parquet(GOLD / f"{nombre}.parquet", index=False)
        print(f"  gold/{nombre}: {len(tabla):,} filas")
