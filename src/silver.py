"""Capa silver: un esquema unico para todos los anios, tipos correctos y controles de calidad.

Lo que no pasa los controles no se borra, va a una tabla de cuarentena con el motivo.
"""
import pandas as pd

from src import bronze

SILVER = bronze.DATA / "silver"

# --- Todo lo que cambia entre anios esta aca ---

# Si un anio no trae una columna (o la trae en otra unidad) no va en el mapeo y se calcula despues.
MAPEO_VIAJES = {
    2016: {
        # 2016 no trae id de viaje ni id de usuario.
        # La duracion viene como "0 days 00:16:29" y no coincide con fin - inicio, la recalculo.
        "fecha_origen_recorrido": "fecha_hora_inicio",
        "fecha_destino_recorrido": "fecha_hora_fin",
        "id_estacion_origen": "id_estacion_origen",
        "nombre_estacion_origen": "nombre_estacion_origen",
        "id_estacion_destino": "id_estacion_destino",
        "nombre_estacion_destino": "nombre_estacion_destino",
    },
    2019: {
        "Id_recorrido": "id_viaje",
        "fecha_origen_recorrido": "fecha_hora_inicio",
        "fecha_destino_recorrido": "fecha_hora_fin",
        "duracion_recorrido": "duracion_seg",
        "id_estacion_origen": "id_estacion_origen",
        "nombre_estacion_origen": "nombre_estacion_origen",
        "id_estacion_destino": "id_estacion_destino",
        "nombre_estacion_destino": "nombre_estacion_destino",
        "id_usuario": "id_usuario",
    },
    2024: {
        "id_recorrido": "id_viaje",
        "fecha_origen_recorrido": "fecha_hora_inicio",
        "fecha_destino_recorrido": "fecha_hora_fin",
        "duracion_recorrido": "duracion_seg",
        "id_estacion_origen": "id_estacion_origen",
        "nombre_estacion_origen": "nombre_estacion_origen",
        "id_estacion_destino": "id_estacion_destino",
        "nombre_estacion_destino": "nombre_estacion_destino",
        "id_usuario": "id_usuario",
    },
}
FORMATO_FECHA_VIAJES = "%Y-%m-%d %H:%M:%S"  # es el mismo en los 3 anios

MAPEO_USUARIOS = {
    2016: {
        "id_usuario": "id_usuario",
        "genero_usuario": "genero",
        "edad_usuario": "edad",
        "fecha_alta": "fecha_alta",
        "hora_alta": "hora_alta",
    },
    2019: {
        "ID_usuario": "id_usuario",  # en 2019 viene en mayuscula
        "genero_usuario": "genero",
        "edad_usuario": "edad",
        "fecha_alta": "fecha_alta",
        "hora_alta": "hora_alta",
    },
    2024: {
        "id_usuario": "id_usuario",
        "genero_usuario": "genero",
        "edad_usuario": "edad",
        "fecha_alta": "fecha_alta",
        "hora_alta": "hora_alta",
    },
}
# fecha_alta y hora_alta vienen separadas, las junto antes de convertir
FORMATO_FECHA_USUARIOS = {
    2016: "%d-%m-%y %I:%M:%S %p",  # 01-01-16 3:45:19 AM
    2019: "%Y-%m-%d %H:%M:%S",
    2024: "%Y-%m-%d %H:%M:%S",
}

# solo los valores que aparecen en los archivos (value_counts), el resto queda DESCONOCIDO
MAPEO_GENERO = {
    "F": "F",
    "FEMALE": "F",
    "M": "M",
    "MALE": "M",
    "OTHER": "OTRO",
}

# --- Esquema canonico ---

ESQUEMA_VIAJES = {
    "id_viaje": "string",
    "fecha_hora_inicio": "datetime64[ns]",
    "fecha_hora_fin": "datetime64[ns]",
    "duracion_seg": "Int64",
    "id_estacion_origen": "Int64",
    "nombre_estacion_origen": "string",
    "id_estacion_destino": "Int64",
    "nombre_estacion_destino": "string",
    "id_usuario": "string",
    "anio_fuente": "Int64",
}

ESQUEMA_USUARIOS = {
    "id_usuario": "string",
    "genero": "string",
    "edad": "Int64",
    "fecha_alta": "datetime64[ns]",
    "anio_fuente": "Int64",
}


def validar_esquema(df: pd.DataFrame, esquema: dict) -> None:
    """Corta el pipeline si las columnas o los tipos no son exactamente los del esquema."""
    columnas_esperadas = list(esquema)
    columnas_esperadas += [c for c in df.columns if c == "motivo"]  # las cuarentenas tienen una columna mas
    if list(df.columns) != columnas_esperadas:
        raise ValueError(f"Columnas distintas al esquema: {list(df.columns)}")
    for columna, tipo in esquema.items():
        if str(df[columna].dtype) != tipo:
            raise ValueError(f"{columna}: tipo {df[columna].dtype}, se esperaba {tipo}")


# --- Funciones de limpieza ---

def renombrar(df: pd.DataFrame, mapeo: dict) -> pd.DataFrame:
    df = df.rename(columns=mapeo)
    return df[list(mapeo.values())]  # descarta lo que no esta en el mapeo


def limpiar_id(serie: pd.Series) -> pd.Series:
    # 2019 trae "1234BAEcobici" y 2024 trae el id de usuario como float ("992557.0")
    serie = serie.astype("string").str.strip().str.replace(r"BAEcobici$|\.0$", "", regex=True)
    return serie.replace("", pd.NA)


def a_fecha(serie: pd.Series, formato: str) -> pd.Series:
    # pandas 3 devuelve datetime64[us], el esquema pide [ns]
    return pd.to_datetime(serie, format=formato, errors="coerce").astype("datetime64[ns]")


def a_entero(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce").astype("Int64")


def normalizar_nombre(serie: pd.Series) -> pd.Series:
    # "  014 - Pacifico " -> "PACIFICO". 2019 y 2024 traen un codigo adelante del nombre, 2016 no.
    serie = serie.astype("string").str.strip()
    serie = serie.str.replace(r"^\d+\s*-\s*", "", regex=True)
    serie = serie.str.upper().str.replace(r"\s+", " ", regex=True).str.strip()
    return serie.replace("", pd.NA)


# --- Viajes ---

def transformar_viajes(df: pd.DataFrame, anio: int) -> pd.DataFrame:
    df = renombrar(df, MAPEO_VIAJES[anio])

    if "id_viaje" not in df.columns:
        # 2016 no tiene id: uso el numero de fila del archivo, siempre da lo mismo
        df["id_viaje"] = [f"{anio}-{i}" for i in range(1, len(df) + 1)]
    df["id_viaje"] = limpiar_id(df["id_viaje"])

    df["fecha_hora_inicio"] = a_fecha(df["fecha_hora_inicio"], FORMATO_FECHA_VIAJES)
    df["fecha_hora_fin"] = a_fecha(df["fecha_hora_fin"], FORMATO_FECHA_VIAJES)

    if "duracion_seg" in df.columns:
        # 2019 usa coma de miles: "2,814" son 2814 segundos
        df["duracion_seg"] = a_entero(df["duracion_seg"].str.replace(",", ""))
    else:
        df["duracion_seg"] = (df["fecha_hora_fin"] - df["fecha_hora_inicio"]).dt.total_seconds().astype("Int64")

    for lado in ("origen", "destino"):
        df[f"id_estacion_{lado}"] = a_entero(limpiar_id(df[f"id_estacion_{lado}"]))
        df[f"nombre_estacion_{lado}"] = normalizar_nombre(df[f"nombre_estacion_{lado}"])

    if "id_usuario" in df.columns:
        df["id_usuario"] = limpiar_id(df["id_usuario"])
    else:
        df["id_usuario"] = pd.Series(pd.NA, index=df.index, dtype="string")

    df["anio_fuente"] = pd.Series(anio, index=df.index, dtype="Int64")
    return df[list(ESQUEMA_VIAJES)]


def separar(df: pd.DataFrame, reglas: list) -> tuple:
    """Devuelve (validos, cuarentena). Si una fila falla varias reglas queda el primer motivo."""
    motivo = pd.Series(pd.NA, index=df.index, dtype="string")
    for nombre, condicion in reglas:
        condicion = condicion.fillna(False).astype(bool)  # comparar contra nulos da NA
        motivo = motivo.mask(motivo.isna() & condicion, nombre)

    validos = df[motivo.isna()]
    cuarentena = df[motivo.notna()].assign(motivo=motivo[motivo.notna()])
    return validos, cuarentena


def aplicar_calidad_viajes(df: pd.DataFrame) -> tuple:
    reglas = [
        ("FECHA_INVALIDA", df["fecha_hora_inicio"].isna() | df["fecha_hora_fin"].isna()),
        ("ESTACION_NULA", df["id_estacion_origen"].isna() | df["id_estacion_destino"].isna()),
        ("FIN_ANTERIOR_A_INICIO", df["fecha_hora_fin"] < df["fecha_hora_inicio"]),
        ("DURACION_MAYOR_24H", df["duracion_seg"] > 86_400),
        ("DUPLICADO", df["id_viaje"].duplicated(keep="first")),
    ]
    return separar(df, reglas)


# --- Usuarios ---

def transformar_usuarios(df: pd.DataFrame, anio: int) -> pd.DataFrame:
    df = renombrar(df, MAPEO_USUARIOS[anio])

    df["id_usuario"] = limpiar_id(df["id_usuario"])
    df["genero"] = df["genero"].str.strip().str.upper().map(MAPEO_GENERO).fillna("DESCONOCIDO").astype("string")

    # edades fuera de 16-90 no se rechazan, se dejan en nulo (hay "NA", 0, 116, 2005...)
    edad = a_entero(df["edad"])
    df["edad"] = edad.mask(((edad < 16) | (edad > 90)).fillna(False))

    df["fecha_alta"] = a_fecha(df["fecha_alta"] + " " + df["hora_alta"], FORMATO_FECHA_USUARIOS[anio])
    df["anio_fuente"] = pd.Series(anio, index=df.index, dtype="Int64")
    return df[list(ESQUEMA_USUARIOS)]


def aplicar_calidad_usuarios(df: pd.DataFrame) -> tuple:
    # para los duplicados me quedo con la fecha_alta mas reciente:
    # ordeno de mas nuevo a mas viejo y marco como duplicado todo lo que no sea el primero
    orden = df.sort_values("fecha_alta", ascending=False, kind="mergesort", na_position="last")
    duplicado = orden["id_usuario"].duplicated(keep="first").reindex(df.index)

    reglas = [
        ("ID_NULO", df["id_usuario"].isna()),
        ("DUPLICADO", duplicado),
    ]
    return separar(df, reglas)


# --- Verificaciones ---

def conciliar(tipo: str, validos: pd.DataFrame, cuarentena: pd.DataFrame) -> None:
    """Filas en bronze = filas en silver + filas en cuarentena, para cada anio."""
    filas_bronze = bronze.contar_filas(tipo)
    for anio, filas in filas_bronze.items():
        ok = (validos["anio_fuente"] == anio).sum()
        malas = (cuarentena["anio_fuente"] == anio).sum()
        print(f"  {tipo} {anio}: bronze {filas:,} = silver {ok:,} + cuarentena {malas:,}")
        assert filas == ok + malas, f"Se perdieron filas de {tipo} {anio}"


def ejecutar() -> None:
    SILVER.mkdir(parents=True, exist_ok=True)

    # viajes
    partes = []
    for anio, mapeo in MAPEO_VIAJES.items():
        ruta = bronze.BRONZE / "recorridos" / f"anio={anio}" / "data.parquet"
        df = pd.read_parquet(ruta, columns=list(mapeo))  # leo solo lo que uso, el 2019 es pesado
        partes.append(transformar_viajes(df, anio))
    viajes = pd.concat(partes, ignore_index=True)
    del partes

    viajes, cuarentena = aplicar_calidad_viajes(viajes)
    conciliar("recorridos", viajes, cuarentena)
    assert viajes["id_viaje"].is_unique, "Hay id_viaje repetidos en silver"
    print("  motivos de cuarentena:", cuarentena["motivo"].value_counts().to_dict())

    validar_esquema(viajes, ESQUEMA_VIAJES)
    validar_esquema(cuarentena, ESQUEMA_VIAJES)
    viajes.to_parquet(SILVER / "viajes.parquet", index=False)
    cuarentena.to_parquet(SILVER / "viajes_cuarentena.parquet", index=False)
    del viajes, cuarentena

    # usuarios
    partes = []
    for anio, mapeo in MAPEO_USUARIOS.items():
        ruta = bronze.BRONZE / "usuarios" / f"anio={anio}" / "data.parquet"
        partes.append(transformar_usuarios(pd.read_parquet(ruta, columns=list(mapeo)), anio))
    usuarios = pd.concat(partes, ignore_index=True)

    usuarios, cuarentena_usuarios = aplicar_calidad_usuarios(usuarios)
    conciliar("usuarios", usuarios, cuarentena_usuarios)
    assert usuarios["id_usuario"].is_unique, "Hay id_usuario repetidos en silver"
    print("  motivos de cuarentena usuarios:", cuarentena_usuarios["motivo"].value_counts().to_dict())

    validar_esquema(usuarios, ESQUEMA_USUARIOS)
    validar_esquema(cuarentena_usuarios, ESQUEMA_USUARIOS)
    usuarios.to_parquet(SILVER / "usuarios.parquet", index=False)
    cuarentena_usuarios.to_parquet(SILVER / "usuarios_cuarentena.parquet", index=False)
