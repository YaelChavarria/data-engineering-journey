# Data Engineering Journey

Ruta personal de aprendizaje para fortalecer mis habilidades como Data Engineer y construir un portafolio técnico reproducible.

## Objetivo

Documentar, con transparencia, el proceso de aprendizaje en:

- Python y SQL.
- Docker y Git.
- Cloud y almacenamiento de datos.
- Modelado y transformaciones con dbt.
- Orquestación con Airflow.
- Procesamiento con PySpark.
- Calidad, observabilidad y CI/CD para datos.

Este repositorio contiene mis notas, decisiones, bitácoras y proyectos propios. No es una copia ni un repositorio espejo de los cursos utilizados como referencia.

## Estado actual

- Primera etapa: configuración del entorno y fundamentos.
- Primer hito registrado: entorno de desarrollo preparado y verificado.
- Segundo hito completado: primer pipeline batch funcional con Python, DuckDB y SQL.
- Tercer hito completado: lakehouse local de e-commerce con arquitectura Medallion.
- Próximo hito: añadir dbt y una validación automatizada de modelos analiticos.

El progreso se actualizará a medida que cada entregable esté terminado y probado.

## Estructura

```text
.
├── learning-log/       # Bitácora de aprendizaje
├── notes/              # Notas técnicas resumidas y sanitizadas
├── projects/           # Proyectos propios
├── roadmap/            # Plan de aprendizaje
├── resources.md        # Recursos externos utilizados
└── ATTRIBUTION.md      # Fuentes y atribuciones
```

## Ruta principal

Consulta [roadmap/30-day-plan.md](roadmap/30-day-plan.md) para ver el plan de trabajo y sus entregables.

## Proyectos

Cada proyecto propio tendrá su propio README con:

- Problema que resuelve.
- Arquitectura.
- Fuentes y licencia de los datos.
- Tecnologías utilizadas.
- Instrucciones de ejecución.
- Pruebas y validaciones.
- Resultados, costes y limitaciones.

La plantilla está en [projects/README.md](projects/README.md).

## Fuentes de aprendizaje

Las fuentes externas están documentadas en [resources.md](resources.md) y [ATTRIBUTION.md](ATTRIBUTION.md). Sus autores y licencias originales se mantienen intactos.

## Privacidad y reproducibilidad

No se publican credenciales, tokens, archivos `.env`, rutas personales, configuraciones privadas ni datasets grandes. Los datos se descargan desde su fuente oficial cuando sea necesario.

## Licencia

La licencia de este repositorio se definirá cuando se publique la primera versión estable. Los materiales de terceros conservan sus propias licencias y no quedan cubiertos por una futura licencia de mis notas o código.

## Primer proyecto

[NYC Taxi Data Pipeline](projects/nyc-taxi-pipeline/) es un pipeline batch reproducible que descarga datos públicos, los valida y genera métricas diarias con DuckDB.

## Segundo proyecto

[E-Commerce Lakehouse](projects/ecommerce-lakehouse/) es un lakehouse local reproducible que genera datos sinteticos de una tienda online y los transforma en capas Bronze, Silver y Gold con DuckDB y Parquet.
