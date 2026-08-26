FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY dbt ./dbt
COPY dashboard ./dashboard

RUN pip install --no-cache-dir .

VOLUME ["/app/data"]

ENTRYPOINT ["python", "-m", "ecommerce_lakehouse"]
