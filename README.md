# Pipeline Ecobici - Bronze, Silver y Gold

Ejercicio de Ciencia de Datos (UTN FRVM). Pipeline en Python + pandas que toma los recorridos y
usuarios de Ecobici de 2016, 2019 y 2024 tal cual los publica la Ciudad y los lleva hasta un modelo
estrella y 5 reportes en CSV, pasando por las capas bronze, silver y gold.

**Alumno:** Martin Roberto Gaido - Legajo 15188

Las decisiones que tomé y la exploración de los archivos están en [DECISIONES.md](DECISIONES.md).

## Requisitos

- Python 3.11 o superior (yo lo corrí con Python 3.14)
- Librerías: pandas y pyarrow (versiones en `requirements.txt`)
- Unos 5 GB de RAM libres (el pico que medí fue 4,5 GB) y ~1 GB de disco para las capas

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Datos de entrada

Bajar del dataset [Bicicletas Públicas](https://data.buenosaires.gob.ar/dataset/bicicletas-publicas)
y copiar en `data/raw/` **sin descomprimir ni renombrar**:

```
data/raw/
├── recorridos-realizados-2016.zip
├── recorridos-realizados-2019.zip
├── recorridos-realizados-2024.zip
├── usuarios-ecobici-2016.csv
├── usuarios_ecobici_2019.csv
└── usuarios_ecobici_2024.csv
```

Si algún archivo tiene otro nombre hay que cambiarlo en `ARCHIVOS` dentro de `src/bronze.py`.

## Ejecución

```bash
python main.py
```

Corre todo en orden: bronze → silver → gold → reportes. En mi compu tarda un poco más de 2 minutos.
Se puede correr las veces que quieras: cada capa pisa sus archivos, no agrega datos (idempotente).

Durante la corrida se imprimen los controles: filas por archivo, la conciliación
bronze = silver + cuarentena por año y los viajes cuyo usuario no está en `dim_usuario`.
Si algún control falla el pipeline corta con un `AssertionError` o `ValueError`.

## Estructura

```
ecobici-pipeline/
├── data/
│   ├── raw/        archivos originales (no se tocan)
│   ├── bronze/     copia fiel en parquet, todo texto + metadatos
│   ├── silver/     viajes, viajes_cuarentena, usuarios, usuarios_cuarentena
│   └── gold/       dim_fecha, dim_estacion, dim_usuario, fact_viajes
│       └── reportes/   los 5 CSV
├── src/
│   ├── bronze.py
│   ├── silver.py
│   ├── gold.py
│   └── reportes.py
├── main.py
├── requirements.txt
├── DECISIONES.md
└── README.md
```

## Reportes

| Archivo | Qué tiene |
|---|---|
| `viajes_por_mes.csv` | cantidad de viajes por año y mes |
| `top10_estaciones_por_anio.csv` | las 10 estaciones con más viajes iniciados por año |
| `duracion_por_rango_y_genero.csv` | duración promedio según rango etario y género del usuario |
| `viajes_circulares.csv` | % de viajes que terminan en la misma estación donde empezaron |
| `calidad_por_anio.csv` | filas en bronze, silver y cuarentena por año |

Las carpetas `data/raw`, `data/bronze`, `data/silver` y las tablas de `data/gold` no están en el
repo porque pesan mucho; se regeneran con `python main.py`.
