# Decisiones

## 1. Exploración de los archivos (Tarea 1)

Miré las primeras filas de cada archivo para ver columnas y formatos, y después recorrí cada archivo
completo para contar filas, vacíos y los distintos formatos de cada columna. La cantidad de filas es
la misma que después dio bronze.

### Recorridos

| Aspecto | 2016 | 2019 | 2024 |
|---|---|---|---|
| Archivo dentro del ZIP | `recorridos-realizados-2016.csv` | `trips_2019.csv` | `badata_ecobici_recorridos_realizados_2024.csv` |
| Separador | `,` | `,` (todos los valores entre comillas) | `,` (el archivo empieza con BOM) |
| Columnas | 15 (ver abajo) | 18 (ver abajo) | 17 (ver abajo) |
| Formato de fecha y hora | `2016-01-01 02:21:41` | `2019-02-27 19:44:42` | `2024-01-23 18:36:00` |
| ¿Trae duración? | Sí, como texto tipo timedelta: `0 days 00:16:29.000000000`. No coincide con fin − inicio | Sí, en segundos con coma de miles: `"2,814"` | Sí, en segundos: `568` |
| ¿Trae id de viaje? | **No** | Sí, con sufijo: `9379BAEcobici` | Sí: `20428222` |
| ¿Trae id de usuario? | **No** (solo `genero_usuario`) | Sí, con sufijo: `6243BAEcobici` | Sí, como float: `992557.0` |
| Cantidad total de filas | 596.807 | 6.217.004 | 3.559.284 |

Columnas originales:

- **2016:** `periodo, genero_usuario, fecha_origen_recorrido, id_estacion_origen, nombre_estacion_origen, long_estacion_origen, lat_estacion_origen, domicilio_estacion_origen, duracion_recorrido, fecha_destino_recorrido, id_estacion_destino, nombre_estacion_destino, long_estacion_destino, lat_estacion_destino, domicilio_estacion_destino`
- **2019:** una primera columna sin nombre (es un índice 1, 2, 3...; pandas la lee como `Unnamed: 0`), `Id_recorrido, duracion_recorrido, fecha_origen_recorrido, id_estacion_origen, nombre_estacion_origen, direccion_estacion_origen, long_estacion_origen, lat_estacion_origen, fecha_destino_recorrido, id_estacion_destino, nombre_estacion_destino, direccion_estacion_destino, long_estacion_destino, lat_estacion_destino, id_usuario, modelo_bicicleta, género`
- **2024:** `id_recorrido, duracion_recorrido, fecha_origen_recorrido, id_estacion_origen, nombre_estacion_origen, direccion_estacion_origen, long_estacion_origen, lat_estacion_origen, fecha_destino_recorrido, id_estacion_destino, nombre_estacion_destino, direccion_estacion_destino, long_estacion_destino, lat_estacion_destino, id_usuario, modelo_bicicleta, genero`

Otras cosas que vi:

- 2016: 93.555 viajes sin `fecha_destino_recorrido` (15,7%). Además, la duración original coincide
  con fin − inicio (con 1 minuto de tolerancia) solo en 18.475 de los 503.252 viajes que sí tienen fin.
- 2019: los ids de estación también traen el sufijo (`5BAEcobici`), el nombre de estación trae un
  código adelante (`005 - Plaza Italia`) y 1.760 viajes no tienen estación de destino. Las
  coordenadas de destino están corridas: `long_estacion_destino` trae la latitud y
  `lat_estacion_destino` trae `"lat,long"` juntas. Los datos arrancan el 17/02/2019.
- 2024: los nombres de estación también traen código (`308 - SAN MARTIN II`), 3.379 viajes sin fecha
  de fin y un `id_recorrido` repetido (22425357).
- En 2019 y 2024 la duración coincide con fin − inicio en el 100% de los viajes.

### Usuarios

| Aspecto | 2016 | 2019 | 2024 |
|---|---|---|---|
| Archivo | `usuarios-ecobici-2016.csv` | `usuarios_ecobici_2019.csv` | `usuarios_ecobici_2024.csv` |
| Separador | `,` | `,` (con comillas) | `,` (con BOM) |
| Columnas | `id_usuario, genero_usuario, edad_usuario, fecha_alta, hora_alta` | igual pero `ID_usuario` en mayúscula | igual que 2016 |
| Formato fecha / hora | `01-01-16` (dd-mm-yy) y `3:45:19 AM` (12 hs) | `2019-12-31` y `10:46:10` | `2024-01-18` y `09:21:02` |
| Valores de género | `M`, `F` | `MALE`, `FEMALE`, `OTHER`, vacío (857) | `MALE`, `FEMALE`, `OTHER` |
| Edades raras | ninguna (16 a 88) | 765 `"NA"` y 46 fuera de 16-90 | 94 fuera de 16-90 (mínimo 4, máximo 2021) |
| Cantidad total de filas | 39.481 | 83.600 | 197.077 |

En 2016 supe que la fecha es dd-mm-yy y no mm-dd-yy porque el primer número llega a 31 y el segundo
nunca pasa de 12. Cada archivo de usuarios tiene solo las altas de ese año.

## 2. Mapeo de columnas

### Viajes

| Columna canónica | 2016 | 2019 | 2024 |
|---|---|---|---|
| `id_viaje` | no viene, se genera | `Id_recorrido` | `id_recorrido` |
| `fecha_hora_inicio` | `fecha_origen_recorrido` | `fecha_origen_recorrido` | `fecha_origen_recorrido` |
| `fecha_hora_fin` | `fecha_destino_recorrido` | `fecha_destino_recorrido` | `fecha_destino_recorrido` |
| `duracion_seg` | se calcula fin − inicio | `duracion_recorrido` | `duracion_recorrido` |
| `id_estacion_origen` | `id_estacion_origen` | `id_estacion_origen` | `id_estacion_origen` |
| `nombre_estacion_origen` | `nombre_estacion_origen` | `nombre_estacion_origen` | `nombre_estacion_origen` |
| `id_estacion_destino` | `id_estacion_destino` | `id_estacion_destino` | `id_estacion_destino` |
| `nombre_estacion_destino` | `nombre_estacion_destino` | `nombre_estacion_destino` | `nombre_estacion_destino` |
| `id_usuario` | no viene, queda nulo | `id_usuario` | `id_usuario` |
| `anio_fuente` | se agrega | se agrega | se agrega |

### Usuarios

| Columna canónica | 2016 | 2019 | 2024 |
|---|---|---|---|
| `id_usuario` | `id_usuario` | `ID_usuario` | `id_usuario` |
| `genero` | `genero_usuario` | `genero_usuario` | `genero_usuario` |
| `edad` | `edad_usuario` | `edad_usuario` | `edad_usuario` |
| `fecha_alta` | `fecha_alta` + `hora_alta` | `fecha_alta` + `hora_alta` | `fecha_alta` + `hora_alta` |
| `anio_fuente` | se agrega | se agrega | se agrega |

### Género

| Valor original | Valor en silver |
|---|---|
| `F`, `FEMALE` | `F` |
| `M`, `MALE` | `M` |
| `OTHER` | `OTRO` |
| vacío o cualquier otro | `DESCONOCIDO` |

Puse solo los valores que aparecen en los archivos (`value_counts()`). Variantes como `Femenino` o
`X` no existen en estos datos; si apareciera algo nuevo caería en `DESCONOCIDO`.

Todo lo que cambia entre años está en `src/silver.py`: `MAPEO_VIAJES`, `MAPEO_USUARIOS`,
`FORMATO_FECHA_USUARIOS` y `MAPEO_GENERO`.

## 3. Decisiones que no estaban en el enunciado

### Bronze

1. **Leo con `keep_default_na=False` además de `dtype=str`.** Si no, pandas convierte `""` y `"NA"` en nulos y bronze deja de ser una copia fiel.
2. **Leo por partes (`chunksize=500_000`) y escribo con `pyarrow.parquet.ParquetWriter`.** El CSV de 2019 descomprimido pesa 1,9 GB y no quería cargarlo entero en memoria como texto.
3. **No uso `zipfile`.** Cada ZIP tiene un solo CSV, así que `read_csv` lo lee directo.
4. **No hago nada especial con el BOM.** pandas ya lo saca del nombre de la primera columna (lo probé con el archivo de usuarios 2024).
5. **La columna sin nombre de 2019 queda en bronze como `Unnamed: 0`.** Es el nombre que le pone pandas; en silver se descarta porque es solo un índice.
6. **Los usuarios también se guardan en `bronze/usuarios/anio=XXXX/`**, igual que los recorridos, para que la estructura sea la misma.

### Silver - viajes

7. **El id de los viajes de 2016 es `"2016-<número de fila>"`** (`2016-1`, `2016-2`, ...). Sale del orden del archivo, que bronze respeta, así que da siempre lo mismo y no se pisa con los ids de 2019 (10 a 6.875.895) ni con los de 2024 (20.180.969 a 24.503.283).
8. **Saco el sufijo `BAEcobici` de los ids de 2019 y el `.0` del `id_usuario` de 2024.** Si no, no cruzan con la tabla de usuarios ni tienen el mismo formato que los otros años.
9. **En 2016 la duración se calcula como fin − inicio y no uso la columna original**, porque no coincide en el 96% de los casos y el enunciado dice que se calcule si viene en otra unidad. Me llamó la atención que en 2016 fin − inicio nunca baja de 600 segundos exactos, así que sospecho que la hora de devolución de ese año tampoco es del todo exacta, pero no hay otra fuente mejor.
10. **Los 93.555 viajes de 2016 sin fecha de fin van a cuarentena (`FECHA_INVALIDA`)**, como dice la regla. Se podría haber reconstruido el fin con inicio + duración original, pero esa columna no es confiable. Por eso 2016 tiene 15,68% de cuarentena.
11. **A los nombres de estación les saco el código del principio** (`"014 - Pacifico"` → `"PACIFICO"`), además de trim, mayúsculas y espacios. 2016 no lo trae y, sin sacarlo, la misma estación quedaba con dos nombres. Ese código no es el id (en 2024 el id 513 es `308 - SAN MARTIN II`).
12. **No saco tildes** (`PACÍFICO` en 2016 y `PACIFICO` en 2019), porque `dim_estacion` igual se queda con el nombre más reciente.
13. **Las columnas que no forman parte del esquema no pasan a silver** (coordenadas, direcciones, modelo de bici, género del viaje, periodo). Las coordenadas corridas de 2019 no las arreglé porque no se usan.
14. **Las reglas de calidad se aplican sobre los 3 años juntos** (en orden 2016, 2019, 2024), así `DUPLICADO` también detectaría ids repetidos entre años.

### Silver - usuarios

15. **Creé `silver/usuarios_cuarentena`** con el motivo (`ID_NULO` o `DUPLICADO`). El enunciado no la pide, pero la idea de la capa es no perder registros.
16. **Edad:** `"NA"` y cualquier texto quedan nulos (`errors="coerce"`); menores de 16 y mayores de 90 también, como pide el enunciado. Quedan 905 edades nulas (811 de 2019 y 94 de 2024).
17. **5.231 ids de 2016 vuelven a aparecer en el archivo de 2019.** Me quedé con el de `fecha_alta` más reciente (el de 2019), como dice el enunciado. Sospecho que son personas distintas, porque los ids de 2019 arrancan desde números chicos (hay ids de 2 y 3 dígitos). De todas formas no afecta ningún cruce, porque los viajes de 2016 no traen `id_usuario`.
18. **`fecha_alta` junta `fecha_alta` + `hora_alta`**, cada año con su formato.

### General

19. **pandas 3 convierte las fechas a `datetime64[us]`**, así que hago `astype("datetime64[ns]")` para que coincida con el esquema. `validar_esquema` controla tipos y orden de columnas antes de guardar cada tabla.
20. **Silver se guarda como un parquet por tabla** (`silver/viajes.parquet`, etc.) y no particionado por año, porque las tablas ya están unificadas.

### Gold y reportes

21. **`dim_fecha` va del primer al último día con viajes** (2016-01-01 a 2024-12-31, 3.288 días), incluyendo los años sin datos, así queda un calendario continuo.
22. **El día de la semana sale de una lista en español** y no de `day_name()`, para no depender del idioma configurado en la compu.
23. **En `dim_estacion`, si una estación tuvo más de un nombre en el año más reciente, me quedo con el más usado.**
24. **El rango etario se arma con `pd.cut`:** (15,25] → 16-25, (25,35] → 26-35, (35,50] → 36-50, (50,90] → 51+, y edad nula → `DESCONOCIDO`.
25. **Los reportes 1 a 4 toman el año de `dim_fecha`** (fecha de inicio del viaje), no `anio_fuente`. Acá da lo mismo porque cada archivo trae solo viajes de su año.
26. **En el top 10, si hay empate en cantidad gana el id más chico**, para que el ranking salga siempre igual.
27. **El reporte 3 es un inner join con `dim_usuario`:** solo entran viajes cuyo usuario está en la dimensión. Por eso 2016 no aparece ahí.
28. **Redondeo:** porcentaje de circulares con 1 decimal y de cuarentena con 2, como en los ejemplos.

## 4. Verificaciones

Todas se ejecutan dentro del pipeline (con `assert`) cada vez que se corre `python main.py`.

**Bronze:** las filas por archivo son iguales a las de la Tarea 1 (596.807 / 6.217.004 / 3.559.284 recorridos y 39.481 / 83.600 / 197.077 usuarios).

**Silver - conciliación (bronze = silver + cuarentena):**

| Año | Bronze | Silver | Cuarentena |
|---|---|---|---|
| 2016 | 596.807 | 503.252 | 93.555 |
| 2019 | 6.217.004 | 6.207.851 | 9.153 |
| 2024 | 3.559.284 | 3.555.217 | 4.067 |

Motivos de cuarentena:

| Motivo | 2016 | 2019 | 2024 |
|---|---|---|---|
| FECHA_INVALIDA | 93.555 | 0 | 3.379 |
| ESTACION_NULA | 0 | 1.760 | 0 |
| FIN_ANTERIOR_A_INICIO | 0 | 0 | 0 |
| DURACION_MAYOR_24H | 0 | 7.393 | 687 |
| DUPLICADO | 0 | 0 | 1 |

`id_viaje` es único en `silver/viajes` y los tipos coinciden con el esquema canónico.
Usuarios: 314.927 en silver y 5.231 en cuarentena (todos `DUPLICADO`).

**Gold:** `fact_viajes` tiene 10.266.320 filas, igual que `silver/viajes`. Todos los `fecha_key`
existen en `dim_fecha` y todas las estaciones de origen y destino existen en `dim_estacion`.

**Idempotencia:** corrí el pipeline dos veces seguidas. Los 5 CSV dieron el mismo md5 y todas las
tablas de silver y gold quedaron con la misma cantidad de filas.

### Viajes con usuario que no está en `dim_usuario`

| Año | Viajes | Sin `id_usuario` | Con usuario fuera de `dim_usuario` |
|---|---|---|---|
| 2016 | 503.252 | 503.252 | 0 |
| 2019 | 6.207.851 | 0 | 4.410.500 (71,0%) |
| 2024 | 3.555.217 | 0 | 1.710.135 (48,1%) |

En total son 6.120.635 viajes. No es un error: los archivos de usuarios solo tienen las personas que
se dieron de alta **en ese año**. Alguien que se registró en 2018 o en 2022 y viajó en 2019 o 2024
aparece en el viaje pero no en la tabla de usuarios, porque nos faltan los archivos de esos años.

## 5. Qué encontré en los reportes

**¿Cambia el top 10 de estaciones de un año a otro?** Sí. En 2016 la primera es PARQUE LAS HERAS;
en 2019 y 2024 la primera es CONSTITUCIÓN y la segunda PACIFICO. Las únicas que están en el top los
tres años son PACIFICO, CONGRESO y PLAZA ITALIA. En 2024 entran al top estaciones que no estaban
en los años anteriores (PLAZA DE LA SHOÁ, JULIETA LANTERI, BARRANCAS DE BELGRANO, HOSPITAL DE
CLÍNICAS).

**Un problema con los ids de estación:** en el top 2016 aparecen `ERRONEA` y `KP1808000368`. En 2016
los ids 1 y 10 eran FACULTAD DE DERECHO y PUERTO MADERO - UCA, pero en 2019 esos mismos ids
aparecen con esos nombres, y la regla de quedarse con el nombre más reciente los pisa. Pasa algo
parecido con otras estaciones: 36 ids tienen más de un nombre entre años (por ejemplo, el 34 era
GALERÍAS PACÍFICO en 2016 y EX PARQUE AVELLANEDA II en 2019). Es una limitación de usar los ids
naturales como clave: los ids no son estables entre el sistema de 2016 y el de 2019. Para
resolverlo habría que usar claves sustitutas por estación y período, pero el enunciado pide ids
naturales, así que lo dejé así y lo anoto.

**Otros datos:**
- Los viajes circulares son 12,1% en 2016, 10,2% en 2019 y 13,5% en 2024.
- En todos los rangos de edad los hombres hacen viajes más cortos en promedio (entre 21,9 y 23,2 min) que las mujeres (entre 23,4 y 26,0) y que OTRO (entre 25,4 y 26,5).
- En `viajes_por_mes`, febrero 2019 tiene pocos viajes (11.375) porque los datos arrancan el 17/02. Abril 2016 también tiene muy pocos (2.509) comparado con los meses de alrededor, y no encontré en los datos por qué.
