#!/usr/bin/env python
"""
Ingresa todos los CSV de /processed en la base de datos BioNet (SQL Server).
• Cada archivo se procesa en una transacción.
• Duplica filas: se ignoran gracias al índice UNIQUE.
• Si algo falla → ROLLBACK y se mueve el CSV a /error para revisión.
• Tras éxito → CSV pasa a /archive/yyyy/mm/.
"""
import os, csv, glob, pathlib, shutil, datetime
import pyodbc
from dotenv import load_dotenv

CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=MARTIN-ROGSTRIX\\SQLEXPRESS;"
    "DATABASE=BioNet;"
    "Trusted_Connection=yes;"
)

BASE      = pathlib.Path(__file__).parent.parent
PROCESSED = BASE / "processed"
ERROR     = BASE / "error"
ARCHIVE   = BASE / "archive"

for p in (ARCHIVE,):
    p.mkdir(exist_ok=True)

SQL_INSERT = """
INSERT INTO resultados_examenes
(laboratorio_id, paciente_id, tipo_examen, resultado, fecha_examen)
VALUES (?,?,?,?,?)
"""

def archive_path(csv_file: pathlib.Path):
    ts = datetime.datetime.now()
    dest = ARCHIVE / f"{ts.year}/{ts.month:02d}"
    dest.mkdir(parents=True, exist_ok=True)
    return dest / csv_file.name

def process_file(cursor, csv_file: pathlib.Path):
    with csv_file.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute(SQL_INSERT,
                int(row["laboratorio_id"]),
                int(row["paciente_id"]),
                row["tipo_examen"].strip().upper(),
                row["resultado"].strip(),
                row["fecha_examen"]     # ISO-8601 → T-SQL cast implícito
            )

def main():
    connection = pyodbc.connect(CONN_STR, autocommit=False)
    cursor     = connection.cursor()

    for path in glob.glob(str(PROCESSED / "*.csv")):
        csv_file = pathlib.Path(path)
        print(f"⏳  Procesando {csv_file.name} …")
        try:
            cursor.execute("BEGIN TRANSACTION;")
            process_file(cursor, csv_file)
            connection.commit()
            shutil.move(csv_file, archive_path(csv_file))
            print(f"✓   {csv_file.name} ingresado OK")
        except pyodbc.IntegrityError as e:
            connection.rollback()
            shutil.move(csv_file, ERROR / csv_file.name)
            print(f"✗   {csv_file.name} – duplicado o FK inválida: {e}")
        except Exception as e:
            connection.rollback()
            shutil.move(csv_file, ERROR / csv_file.name)
            print(f"✗   {csv_file.name} – error inesperado: {e}")

    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()
