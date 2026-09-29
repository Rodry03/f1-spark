FROM quay.io/jupyter/pyspark-notebook:latest

# FastF1 para descargar datos de F1; pyarrow para escribir Parquet desde pandas.
RUN pip install --no-cache-dir fastf1 pyarrow

WORKDIR /home/jovyan/work
