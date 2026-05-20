from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException, Depends, FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi import Path as FPath
import json
from .plot_activity import generate_activity_plot
from common.json_activity import generate_activity_json
from common.security import verify_api_key
from common.config import LOCK_FILE, STATUS_FILE
from common.garmin_function import get_daily_metrics, get_activity_summary, get_sleep_details, get_last_activity_id, get_activity_name
from common.sync import trigger_sync

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/available_endpoints")
def available_endpoints(_: str = Depends(verify_api_key)):
    return JSONResponse([
        {
            "name": "Dailymetrics",
            "url": "https://garmin.gcourtot.fr/dailymetrics",
            "param": "days",
            "default": "7"
        },
        {
            "name": "Activity Summary",
            "url": "https://garmin.gcourtot.fr/activitysummary",
            "param": "days",
            "default": "30"
        },
        {
            "name": "Sleep Details",
            "url": "https://garmin.gcourtot.fr/sleepdetails",
            "param": "days",
            "default": "7"
        },
        {
            "name": "Sync",
            "url": "https://garmin.gcourtot.fr/sync",
            "param": "",
            "default": ""
        },
        {
            "name": "Sync status",
            "url": "https://garmin.gcourtot.fr/status",
            "param": "",
            "default": ""
        }
    ])

@app.post("/sync")
def sync_data(_: str = Depends(verify_api_key)):
    try:
        result = trigger_sync()
        if result["already_running"]:
            return JSONResponse(status_code=409, content={"message": "Synchronisation déjà en cours."})
        return {"message": "Synchronisation lancée"}
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"error": f"Erreur inattendue: {str(e)}"})

@app.get("/status")
def get_sync_status(_: str = Depends(verify_api_key)):
    if LOCK_FILE.exists():
        return {"status": "running"}

    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text())
        except Exception as e:
            print(e)
            return {"status": "unknown", "error": "Impossible de lire le fichier de statut"}

    return {"status": "idle"}

@app.get("/dailymetrics")
def dailymetrics(days: int = Query(7, ge=1, le=90), _: str = Depends(verify_api_key)):
    return get_daily_metrics(days)

@app.get("/activitysummary")
def activitysummary(days: int = Query(30, ge=1, le=365), _: str = Depends(verify_api_key)):
    return get_activity_summary(days)

@app.get("/sleepdetails")
def sleepdetails(days: int = Query(7, ge=1, le=90), _: str = Depends(verify_api_key)):
    return get_sleep_details(days)

@app.get("/activities/{activity_id}/plot")
def plot_activity(activity_id: str = FPath(..., description="ID de l'activité Garmin"), _: str = Depends(verify_api_key)):
    try:
        return generate_activity_plot(activity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/activities/{activity_id}/json")
def activity_json(activity_id: str = FPath(..., description="ID de l'activité Garmin"), _: str = Depends(verify_api_key)):
    try:
        return generate_activity_json(activity_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/last_activity")
def last_activity(_: str = Depends(verify_api_key)):
    try:
        return get_last_activity_id()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/last_activity_name/{activity_id}")
def last_activity_name(activity_id: str = FPath(..., description="ID de l'activité Garmin"), _: str = Depends(verify_api_key)):
    try:
        return get_activity_name(activity_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"ok": True, "service": "garmin-api"}