#!/usr/bin/env python
"""
BioNet – watcher de CSV
• Vigila la carpeta input-labs
• Verifica que el archivo esté completo y que las columnas sean EXACTAS
• Mueve a /processed  o  /error
"""
import time, pathlib, shutil, hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BASE      = pathlib.Path(__file__).parent.parent
INPUT     = BASE / "input-labs"
PROCESSED = BASE / "processed"
ERROR     = BASE / "error"

for p in (INPUT, PROCESSED, ERROR):
    p.mkdir(exist_ok=True)

REQUIRED_HEADER = ["id","laboratorio_id","paciente_id",
                   "tipo_examen","resultado","fecha_examen"]

def stable_size(fp: pathlib.Path, delay=1.5, tries=3):
    """Devuelve True si el tamaño no cambia en varios intentos."""
    last = fp.stat().st_size
    for _ in range(tries):
        time.sleep(delay)
        now = fp.stat().st_size
        if now != last:
            last = now
        else:
            return True
    return False

def md5sum(fp: pathlib.Path, chunk=8192):
    h = hashlib.md5()
    with fp.open("rb") as f:
        while chunk_data := f.read(chunk):
            h.update(chunk_data)
    return h.hexdigest()

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        self.process(pathlib.Path(event.src_path))

    # Permite que podamos llamar process() desde fuera
    @staticmethod
    def process(f: pathlib.Path):
        if f.suffix.lower() != ".csv":
            return

        # Espera a que termine de copiarse
        if not stable_size(f):
            shutil.move(f, ERROR / f.name)
            print(f"[✗] {f.name} – incompleto.")
            return

        # Valida cabecera
        with f.open(encoding="utf-8") as fh:
            header = fh.readline().strip().split(",")
        if header != REQUIRED_HEADER:
            shutil.move(f, ERROR / f.name)
            print(f"[✗] {f.name} – columnas inválidas.")
            return

        # checksum opcional
        checksum = md5sum(f)
        (PROCESSED / (f.stem + ".md5")).write_text(checksum)

        # --- mover con reintentos (evita WinError 32) ---
        for attempt in range(5):
            try:
                shutil.move(f, PROCESSED / f.name)
                print(f"[✓] {f.name} validado y enviado a processed/")
                break
            except PermissionError:
                if attempt == 4:
                    shutil.move(f, ERROR / f.name)
                    print(f"[✗] {f.name} – bloqueo persistente, enviado a error/")
                else:
                    time.sleep(0.3)  # espera 300 ms y reintenta

if __name__ == "__main__":
    print("▶ Watcher activo en", INPUT)

    # --- procesa CSV que ya estuvieran ---
    for csv_file in INPUT.glob("*.csv"):
        Handler.process(csv_file)

    # --- arranca el watcher en vivo ---
    obs = Observer()
    obs.schedule(Handler(), INPUT, recursive=False)
    obs.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()
