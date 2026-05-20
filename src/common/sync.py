import subprocess
import threading
import json
from datetime import datetime
from .config import LOCK_FILE, STATUS_FILE

SYNC_COMMAND = (
    "LD_PRELOAD=/usr/lib/libfaketime.so.1 FAKETIME=\"+1d\" garmindb_cli.py --all --download --latest && "
    "garmindb_cli.py --all --import --analyze --latest"
)


def run_sync_job(command: str, log_path: str, timestamp: str):
    try:
        with open(log_path, "w") as log_file:
            subprocess.run(
                ["sh", "-c", command],
                stdout=log_file,
                stderr=log_file,
                check=True
            )

        STATUS_FILE.write_text(json.dumps({
            "status": "success",
            "finished_at": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "log_file": log_path
        }))
    except Exception as e:
        STATUS_FILE.write_text(json.dumps({
            "status": "error",
            "error": str(e),
            "finished_at": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "log_file": log_path
        }))
    finally:
        LOCK_FILE.unlink(missing_ok=True)


def trigger_sync() -> dict:
    """Lance la synchronisation GarminDB dans un thread.
    Retourne {"already_running": True} si un sync est déjà en cours,
    sinon {"already_running": False} après avoir démarré le thread.
    Lève une exception en cas d'erreur d'initialisation.
    """
    if LOCK_FILE.exists():
        return {"already_running": True}

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_path = f"/tmp/garmindb_sync_{timestamp}.log"

        LOCK_FILE.touch()
        STATUS_FILE.write_text(json.dumps({"status": "running", "started_at": timestamp}))

        thread = threading.Thread(
            target=run_sync_job,
            args=(SYNC_COMMAND, log_path, timestamp),
            daemon=True
        )
        thread.start()

        return {"already_running": False}
    except Exception as e:
        STATUS_FILE.write_text(json.dumps({
            "status": "error",
            "error": str(e),
            "finished_at": datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        }))
        LOCK_FILE.unlink(missing_ok=True)
        raise
