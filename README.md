# f1-spark

Proyecto para aprender PySpark con datos reales de Fórmula 1. Los datos se descargan
con [FastF1](https://docs.fastf1.dev/) y se guardan en Parquet; las transformaciones
se escriben en los notebooks.

```
data/        datos descargados (no se versiona)
  cache/     caché de FastF1
  raw/<año>/<carrera>/{laps,telemetry,results}.parquet
notebooks/   notebooks de Jupyter
src/         scripts (ingesta)
```

## Levantar el entorno

```powershell
docker compose up -d --build
```

Para obtener la URL de acceso a Jupyter (con el token incluido):

```powershell
docker exec f1-spark jupyter server list
```

Abre en el navegador la URL que aparece (`http://127.0.0.1:8888/?token=...`).
También sale en `docker compose logs jupyter`.
La Spark UI está en http://localhost:4040 mientras haya una SparkSession activa.

Parar el entorno: `docker compose down`.

## Lanzar la ingesta

Dentro del contenedor, la carpeta del proyecto es `/home/jovyan/work`:

```powershell
# Por defecto: 2024, Bahrain y Monaco, sesión de carrera (R)
docker exec -it f1-spark python src/ingest.py

# Otras carreras / temporadas / sesiones
docker exec -it f1-spark python src/ingest.py --year 2023 --races Spain "Great Britain" --session R
```

Las columnas de duración (timedelta) se guardan en segundos (float) y los timestamps
en microsegundos, para que Spark los lea sin problemas. La primera descarga de cada
carrera tarda unos minutos; después se sirve desde la caché.

Desde un notebook:

```python
df = spark.read.parquet("../data/raw/2024/bahrain/laps.parquet")
```
