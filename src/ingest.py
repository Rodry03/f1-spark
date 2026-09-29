"""Descarga datos de F1 con FastF1 y los guarda en Parquet para leerlos con Spark.

Uso:
    python src/ingest.py                          # 2024, Bahrain y Monaco, carrera (R)
    python src/ingest.py --year 2023 --races Spain Italy
    python src/ingest.py --year 2024 --races Monaco --session Q

Salida: data/raw/<año>/<carrera>/{laps,telemetry,results}.parquet
"""

import argparse
import sys
import time
from pathlib import Path

import fastf1
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "cache"
RAW_DIR = ROOT / "data" / "raw"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingesta de datos de F1 con FastF1")
    parser.add_argument("--year", type=int, default=2024, help="Temporada (por defecto: 2024)")
    parser.add_argument(
        "--races",
        nargs="+",
        default=["Bahrain", "Monaco"],
        help="Nombres de carrera tal como los entiende FastF1 (por defecto: Bahrain Monaco)",
    )
    parser.add_argument("--session", default="R", help="Sesión: R, Q, S, FP1... (por defecto: R)")
    return parser.parse_args()


def slug(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def to_spark_friendly(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas timedelta a segundos (float) y devuelve un DataFrame pandas plano."""
    df = pd.DataFrame(df).reset_index(drop=True)
    for col in df.select_dtypes(include=["timedelta64[ns]"]).columns:
        df[col] = df[col].dt.total_seconds()
    return df


def save_parquet(df: pd.DataFrame, path: Path) -> None:
    # Spark no lee timestamps en nanosegundos: los guardamos en microsegundos.
    df.to_parquet(
        path,
        engine="pyarrow",
        index=False,
        coerce_timestamps="us",
        allow_truncated_timestamps=True,
    )


def build_telemetry(session) -> pd.DataFrame:
    frames = []
    for number, car_data in session.car_data.items():
        abbreviation = session.get_driver(number)["Abbreviation"]
        df = pd.DataFrame(car_data)
        df["Driver"] = abbreviation
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def ingest(year: int, race: str, session_type: str) -> dict[str, int]:
    session = fastf1.get_session(year, race, session_type)
    print(f"    Evento: {session.event['EventName']} - {session.name}")
    session.load(laps=True, telemetry=True, weather=False, messages=False)

    out_dir = RAW_DIR / str(year) / slug(race)
    out_dir.mkdir(parents=True, exist_ok=True)

    tables = {
        "laps": session.laps,
        "telemetry": build_telemetry(session),
        "results": session.results,
    }

    counts = {}
    for name, df in tables.items():
        df = to_spark_friendly(df)
        save_parquet(df, out_dir / f"{name}.parquet")
        counts[name] = len(df)
        print(f"    {name}.parquet: {len(df):,} filas")
    return counts


def main() -> int:
    args = parse_args()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(CACHE_DIR))

    failures = []
    total = len(args.races)
    # Una carrera cada vez: la API que usa FastF1 limita el número de peticiones.
    for i, race in enumerate(args.races, start=1):
        print(f"[{i}/{total}] {args.year} {race} ({args.session})")
        start = time.perf_counter()
        try:
            ingest(args.year, race, args.session)
            print(f"    OK en {time.perf_counter() - start:.1f}s")
        except Exception as exc:  # seguimos con la siguiente carrera
            print(f"    ERROR: {exc}", file=sys.stderr)
            failures.append(race)

    if failures:
        print(f"Fallaron: {', '.join(failures)}", file=sys.stderr)
        return 1
    print("Ingesta completada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
