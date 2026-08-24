# E-Commerce Lakehouse

Lakehouse local y reproducible para analizar las ventas de una tienda online. El proyecto implementa una arquitectura Medallion con datos sinteticos, DuckDB y Parquet.

## Problema de negocio

El equipo de negocio necesita una fuente confiable para conocer ingresos, pedidos completados, productos mas vendidos y valor de vida de los clientes. Las fuentes operacionales estan separadas en clientes, productos, pedidos, lineas de pedido y pagos.

## Arquitectura

```text
CSV source system
       |
       v
Bronze: raw CSV -> Parquet, sin cambios de negocio
       |
       v
Silver: tipado, normalizacion y filtros de registros invalidos
       |
       v
Gold: dimensiones, hechos y metricas para analisis
       |
       v
Dashboard futuro: Metabase o Streamlit
```

DuckDB mantiene el catalogo local y consulta Parquet. Esto permite practicar patrones de lakehouse sin requerir una cuenta cloud ni un cluster.

## Capas y modelos

- `bronze_*`: copia tipada por DuckDB de cada archivo de origen.
- `silver_*`: datos normalizados con fechas, importes y claves con tipos explicitos.
- `gold_dim_customer`: dimension de clientes.
- `gold_dim_product`: dimension de productos.
- `gold_fact_order`: una fila por pedido con importe y estado de finalizacion.
- `gold_daily_sales`: pedidos, ingresos y ticket medio por dia.
- `gold_category_sales`: unidades e ingresos por categoria.
- `gold_customer_sales`: pedidos y lifetime value por cliente.

Los pedidos cancelados permanecen en el hecho para conservar trazabilidad, pero no se incluyen en las metricas de ingresos.

## Requisitos

- Python 3.12 o superior.
- Internet no es necesario: la fuente de demostracion se genera localmente.

## Instalacion y ejecucion

Desde esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m ecommerce_lakehouse
```

La ejecucion genera datos sinteticos deterministas y crea:

```text
data/
├── source/              # CSV de entrada, generado localmente
├── bronze/              # Parquet raw
├── silver/              # Parquet limpio
├── gold/                # Parquet analitico
├── warehouse/
│   └── ecommerce.duckdb
└── pipeline_summary.json
```

Para procesar CSV existentes:

```powershell
python -m ecommerce_lakehouse --skip-generate
```

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan un directorio temporal, comprueban las tres capas, validan las relaciones entre tablas y verifican que los pedidos cancelados no generen ingresos.

## Docker

```powershell
docker build -t ecommerce-lakehouse .
docker run --rm -v "${PWD}\data:/app/data" ecommerce-lakehouse
```

## Calidad de datos

El pipeline comprueba:

- Ausencia de claves duplicadas en clientes y productos.
- Ausencia de pedidos sin cliente.
- Ausencia de lineas sin pedido o producto.
- Cantidades positivas e importes no negativos.
- Estados de pedido pertenecientes al dominio esperado.

La ejecucion falla si alguna validacion referencial produce resultados.

## Decisiones y siguientes pasos

- Se usa una fuente sintetica pequena para que el proyecto sea barato y reproducible.
- DuckDB sustituye inicialmente a un warehouse gestionado y facilita la ejecucion local.
- La siguiente iteracion puede incorporar dbt, MinIO, cargas incrementales y un dashboard.
- Una version cloud puede mover Bronze a Azure Blob o S3 y Gold a Snowflake, BigQuery o Databricks.
