# Examen P1 – Integración de Sistemas (BioNet)

> **⚠️ Nota importante**  
> El archivo PDF en `docs/Analisis_Diseno_y_Capturas_Funcionamiento_BioNet_Vargas.pdf`  
> es la **versión actualizada y completa** del informe (contiene 2-3 capturas adicionales respecto a la versión subida inicialmente a Brightspace).  
> Revise ese documento para ver el análisis, los diagramas y la evidencia de ejecución.

---

## Descripción

BioNet administra una red de laboratorios clínicos que generan archivos CSV con resultados de exámenes.  
Esta solución de integración:

1. **Monitorea** la carpeta `input-labs/` para detectar CSV nuevos.  
2. **Valida** la estructura y completitud del archivo, moviéndolo a:  
   * `processed/`  (OK)  
   * `error/`      (KO)  
3. **Ingresa** los datos validados en SQL Server 2022 (BD **BioNet**) con control de duplicados.  
4. **Audita** cada inserción/actualización mediante un trigger (`log_cambios_resultados`).  
5. **Archiva** los CSV procesados en `archive/yyyy/mm/`.

Patrones aplicados: **Transferencia de Archivos** y **Base de Datos Compartida**.

---

## Requisitos

| Componente   | Versión mínima          |
|--------------|-------------------------|
| Python       | 3.11                    |
| SQL Server   | 2022 (Express basta)    |
| ODBC Driver  | 17 o 18 for SQL Server  |
| Dependencias | ver `requirements.txt`  |

> En Windows instala el *ODBC Driver 17/18* desde la página oficial de Microsoft.

---

## Instalación

```powershell
git clone https://github.com/MartinVargas07/Examen-P1-IDS-Vargas.git
cd Examen-P1-IDS-Vargas
python -m venv .venv
. .venv\Scripts\activate      # PowerShell / CMD
pip install -r requirements.txt
```

### Despliegue de la base de datos

1. Abre **SSMS** (o `sqlcmd`) y ejecuta:

   ```sql
   sql\create_database.sql
   ```

   Esto resetea la BD `BioNet`, crea tablas, FK, trigger y carga datos maestros.

---

## Ejecución

### 1 · Watcher de archivos

```powershell
python scripts/transfer_files.py
```

Vigila `input-labs/` y mueve los archivos válidos a `processed/`.

### 2 · Ingesta en la base

En otra terminal (misma venv):

```powershell
python scripts/ingest_db.py
```

Cada CSV de `processed/` se inserta en `resultados_examenes`; al éxito se archiva.

---

## Estructura del repositorio

```
docs/
    Analisis_Diseno_y_Capturas_Funcionamiento_BioNet_Vargas.pdf
scripts/
    transfer_files.py      # watcher & validador
    ingest_db.py           # ingesta transaccional
sql/
    create_database.sql    # drop + create + datos demo
input-labs/                # punto de aterrizaje (.gitkeep)
processed/                 # CSV válidos        (.gitkeep)
error/                     # CSV con error      (.gitkeep)
archive/                   # generada en runtime (git-ignored)
requirements.txt
.gitignore
```

---

## Uso rápido (TL;DR)

```powershell
# 1) Crear la base ejecutando el script SQL
# 2) Colocar CSV en input-labs/
python scripts/transfer_files.py   # Consola 1
python scripts/ingest_db.py        # Consola 2
# 3) Consultar resultados:
#    SELECT * FROM BioNet.dbo.resultados_examenes;
```

---

## Autor

**Martín Vargas** – 9.º Semestre · Integración de Sistemas (2025)
