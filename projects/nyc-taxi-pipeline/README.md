# NYC Taxi Data Pipeline

Pipeline batch reproducible para descargar, limpiar, validar y agregar un mes de viajes de taxi amarillo de Nueva York.

## Objetivo

Construir una primera evidencia completa de Data Engineering:

```text
Fuente oficial NYC TLC
        |
        v
Descarga Parquet a raw/
        |
        v
DuckDB: raw_trips
        |
        v
DuckDB: stg_trips + controles de calidad
        |
        v
daily_metrics.parquet
```

El proyecto corre localmente y no necesita credenciales, servicios cloud ni una base de datos externa.

## Stack

- Python 3.12.
- DuckDB.
- SQL.
- Parquet.
- `unittest` para pruebas.
- Docker opcional.

## Fuente de datos

Los datos proceden de [NYC Taxi and Limousine Commission Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

Por defecto se procesa `yellow_tripdata_2024-01.parquet`, descargado desde la URL oficial de archivos TLC. El dataset no se incluye en GitHub; se descarga durante la ejecución y se ignora mediante `.gitignore`.

## Requisitos

- Python 3.12 o superior.
- Acceso a Internet durante la primera ejecución.
- Aproximadamente 1 GB de espacio temporal disponible, dependiendo de la versión del dataset y de DuckDB.

## Instalación

Desde esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Si PowerShell bloquea la activación, se puede ejecutar directamente:

```powershell
python -m pip install -e .
```

## Ejecución

Procesar enero de 2024:

```powershell
python -m nyc_taxi_pipeline --month 2024-01
```

Para descargar nuevamente el archivo:

```powershell
python -m nyc_taxi_pipeline --month 2024-01 --force-download
```

El pipeline crea localmente:

```text
data/
├── raw/
│   └── yellow_tripdata_2024-01.parquet
└── processed/
    ├── daily_metrics.parquet
    ├── pipeline_summary.json
    └── nyc_taxi.duckdb
```

Estos artefactos están excluidos de GitHub porque son reproducibles y pueden ser grandes.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan datos sintéticos creados temporalmente. No descargan el dataset real.

## Ejecución con Docker

Construir la imagen:

```powershell
docker build -t nyc-taxi-pipeline .
```

Ejecutar conservando los resultados en la carpeta local:

```powershell
docker run --rm -v "${PWD}\data:/app/data" nyc-taxi-pipeline --month 2024-01
```

## Transformaciones

La tabla `stg_trips` normaliza los campos principales y descarta registros que no pueden analizarse de forma segura:

- Fechas de recogida o entrega nulas.
- Entregas anteriores a la recogida.
- Distancias negativas.
- Importes totales negativos.

La tabla `daily_metrics` contiene:

- Fecha.
- Número de viajes.
- Pasajeros.
- Ingresos totales.
- Distancia media.
- Importe medio.

## Calidad de datos

El resumen de ejecución registra:

- Filas leídas de la fuente.
- Filas aceptadas en staging.
- Filas descartadas.
- Nulos y valores inválidos detectados.
- Número de días agregados.

El proceso falla si la tabla de staging queda vacía o si contiene registros inválidos después de la limpieza.

## Última ejecución verificada

La ejecución local contra enero de 2024 produjo:

| Métrica | Resultado |
|---|---:|
| Filas leídas | 2,964,624 |
| Filas aceptadas | 2,929,064 |
| Filas descartadas | 35,560 |
| Filas inválidas después de limpiar | 0 |
| Días agregados | 35 |

Las cuatro pruebas unitarias también pasan correctamente.

GitHub Actions ejecuta estas pruebas automáticamente cuando cambia este proyecto.

## Decisiones y limitaciones

- Se eligió DuckDB porque permite practicar SQL analítico sobre Parquet sin administrar infraestructura.
- Se mantiene el alcance batch para completar un pipeline funcional antes de añadir Airflow o cloud.
- El pipeline no incorpora todavía una tabla de zonas geográficas ni un dashboard.
- El dataset puede cambiar de tamaño o esquema; el esquema esperado se valida durante la carga.

## Próximas mejoras

1. Añadir dimensión de zonas de taxi.
2. Añadir tests de regresión sobre el resumen.
3. Publicar una versión en Azure Storage o BigQuery.
4. Orquestar la ejecución con Airflow.
