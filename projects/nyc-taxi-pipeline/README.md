# NYC Taxi Data Pipeline

A reproducible batch pipeline for downloading, cleaning, validating, and aggregating one month of New York yellow taxi trips.

## Objective

This project demonstrates a complete data engineering workflow:

```text
Official NYC TLC source
        |
        v
Download Parquet to raw/
        |
        v
DuckDB: raw_trips
        |
        v
DuckDB: stg_trips + quality checks
        |
        v
daily_metrics.parquet
```

The project runs locally and requires no credentials, cloud services, or external database.

## Stack

- Python 3.12.
- DuckDB.
- SQL.
- Parquet.
- `unittest` para pruebas.
- Docker opcional.

## Data source

Data comes from the [NYC Taxi and Limousine Commission Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

By default, the pipeline processes `yellow_tripdata_2024-01.parquet`, downloaded from the official TLC file URL. The dataset is not stored in GitHub; it is downloaded during execution and excluded through `.gitignore`.

## Requirements

- Python 3.12 o superior.
- Acceso a Internet durante la primera ejecución.
- Aproximadamente 1 GB de espacio temporal disponible, dependiendo de la versión del dataset y de DuckDB.

## Installation

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

## Execution

Process January 2024:

```powershell
python -m nyc_taxi_pipeline --month 2024-01
```

To download the file again:

```powershell
python -m nyc_taxi_pipeline --month 2024-01 --force-download
```

The pipeline creates locally:

```text
data/
├── raw/
│   └── yellow_tripdata_2024-01.parquet
└── processed/
    ├── daily_metrics.parquet
    ├── pipeline_summary.json
    └── nyc_taxi.duckdb
```

These artifacts are excluded from GitHub because they are reproducible and can be large.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests use temporary synthetic data and do not download the real dataset.

## Docker execution

Construir la imagen:

```powershell
docker build -t nyc-taxi-pipeline .
```

Ejecutar conservando los resultados en la carpeta local:

```powershell
docker run --rm -v "${PWD}\data:/app/data" nyc-taxi-pipeline --month 2024-01
```

## Transformations

The `stg_trips` table normalizes key fields and drops records that cannot be analyzed safely:

- Null pickup or drop-off timestamps
- Drop-off timestamps earlier than pickup timestamps
- Negative distances
- Negative total amounts

The `daily_metrics` table contains:

- Date
- Trip count
- Passenger count
- Total revenue
- Average distance
- Average amount

## Data quality

The execution summary records:

- Rows read from the source
- Rows accepted into staging
- Rows dropped
- Nulls and invalid values detected
- Number of aggregated days

The process fails if the staging table is empty or contains invalid records after cleaning.

## Last verified run

The local run against January 2024 produced:

| Metric | Result |
|---|---:|
| Rows read | 2,964,624 |
| Rows accepted | 2,929,064 |
| Rows dropped | 35,560 |
| Invalid rows after cleaning | 0 |
| Days aggregated | 35 |

All four unit tests also pass.

GitHub Actions runs these tests automatically when this project changes.

## Decisions and limitations

- DuckDB was chosen to practice analytical SQL over Parquet without managing infrastructure.
- The scope remains batch to complete a functional pipeline before adding Airflow or cloud services.
- The pipeline does not yet include a geographic zone dimension or dashboard.
- The dataset may change in size or schema; the expected schema is validated during loading.

## Next improvements

1. Add a taxi-zone dimension.
2. Add regression tests for the execution summary.
3. Publish a version using Azure Storage or BigQuery.
4. Orchestrate execution with Airflow.
