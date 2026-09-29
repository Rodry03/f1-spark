# Tag de fecha fijo: Spark 4.2.0, Python 3.13.15, Java 21.
# Los tags como latest o spark-4.2.0 se reconstruyen cada semana; los de fecha no.
FROM quay.io/jupyter/pyspark-notebook:2026-09-29

# FastF1 para descargar datos de F1; pyarrow para escribir Parquet desde pandas.
RUN pip install --no-cache-dir fastf1 pyarrow

WORKDIR /home/jovyan/work
