import os
from mcp.server.fastmcp import FastMCP
from common.garmin_function import get_last_activity_id, get_daily_metrics as fetch_daily_metrics, get_activity_summary, get_sleep_details, get_hrv_status as fetch_hrv_status
from common.json_activity import generate_activity_json
from mcp.server.fastmcp.server import TransportSecuritySettings
from common.config import DOMAIN, API_KEY, GARMIN_TOKEN_STORE
from common.sync import trigger_sync, read_sync_status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        api_key = request.query_params.get("api_key")
        if api_key != API_KEY:
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})
        return await call_next(request)

mcp = FastMCP(
    "garmin-bridge",
    transport_security=TransportSecuritySettings(
        allowed_hosts=[DOMAIN]
    )
)
app = mcp.streamable_http_app()
app.add_middleware(ApiKeyMiddleware)

@mcp.tool()
def server_health() -> str:
    """Test the MCP server"""
    return "Server is up and running !"

@mcp.tool()
def launch_synchronisation() -> bool:
    """
    Trigger fetching garmin data
    Returns true when launched succesfully, false when the sync is already running
    """
    return not trigger_sync()["already_running"]

@mcp.tool()
def synchronisation_status() -> dict:
    """
    Returns the current synchronisation status.
    Returns 'running' when sync is in progress, the full status dict when finished, or unknown with an error message if the check failed.
    """
    status = read_sync_status()
    return status

@mcp.tool()
def get_last_activity_details() -> dict:
    """
    Return details from the last activity recorded in json.
    No args
    Returns: dict containing timestamps, distances, cadences,altitude, heart rate, rr, speed and temperature
    """
    last_run = get_last_activity_id()
    activity_id = last_run["activity_id"]
    return get_activity_details(activity_id)

@mcp.tool()
def get_activity_details(activity_id : int) -> dict:
    """
    Return details from the activity identified by the activity id.
    Args:
        activity_id: the activity id of the activity to retrieve
    Returns: dict containing timestamps, distances, cadences,altitude, heart rate, rr, speed and temperature
    """
    if activity_id is None:
        return {"error": "No activity found in database"}
    result = generate_activity_json(activity_id)
    return result

@mcp.tool()
def get_last_n_activities_summary(days : int = 10) -> list:
    """
    Return activity summarys from the last n days in json.
    Args:
        days: Number of days to retrieve (default: 10)
    Returns:
        list of activities containing activity_id, name, type, start_time, elapsed_time,
        distance, calories, avg_hr, max_hr, ascent, training_effect,
        anaerobic_training_effect,self_eval_feel, self_eval_effort
    """
    return get_activity_summary(days)

@mcp.tool()
def get_daily_metrics(days : int = 2) -> dict:
    """
    Args : days is the number of days to be returned. default is 2
    Returns a dict containing details from day to day metrics, such as weight, sleep data, stress level, steps, calories...
    """
    return fetch_daily_metrics(days)

@mcp.tool()
def get_hrv_status(days: int = 7) -> list:
    """
    Returns HRV (Heart Rate Variability) status from the monitoring database.
    Args:
        days: Number of days to retrieve (default: 7)
    Returns:
        list of HRV status entries containing timestamp, weekly_average_ms, last_night_ms,
        last_night_average_ms, baseline_low_ms, baseline_high_ms, status_raw, reading_count
    """
    return fetch_hrv_status(days)

@mcp.tool()
def get_sleep_data(days : int = 2) -> dict:
    """
    Args : days is the number of nights to be returned. default is 2
    Returns a dict containing details from sleep metrics
    """
    return get_sleep_details(days)

@mcp.tool()
def push_simple_workout(date: str, name: str, allure_min_par_km: float, duree_minutes: int) -> dict:
    """
    Push a simple constant-pace running workout to Garmin Connect and schedule it on the given date.
    Args:
        date: Target date in YYYY-MM-DD format (e.g., "2026-06-27")
        name: Workout name displayed on the watch
        allure_min_par_km: Target pace in decimal minutes per km (e.g., 5.5 for 5:30/km)
        duree_minutes: Total duration in minutes
    Returns:
        dict with workout_id, date, and scheduled status
    """
    from garminconnect import Garmin, RunningWorkout, create_interval_step

    client = Garmin()
    client.login(os.path.expanduser(GARMIN_TOKEN_STORE))

    duration_seconds = duree_minutes * 60
    # Garmin pace zone targets are in seconds per kilometer
    pace_sec_per_km = allure_min_par_km * 60

    step = create_interval_step(
        step_order=1,
        end_condition="time",
        end_condition_value=duration_seconds,
        target_type="pace.zone",
        target_value_low=round(pace_sec_per_km * 0.9),   # 10% faster bound
        target_value_high=round(pace_sec_per_km * 1.1),  # 10% slower bound
    )

    workout = RunningWorkout(workout_name=name, steps=[step])
    result = client.upload_running_workout(workout.get_workout())

    workout_id = result.get("workoutId") or result.get("detailId")
    if not workout_id:
        return {"error": "Upload succeeded but no workout_id in response", "response": result}

    client.schedule_workout(workout_id, date)
    return {"workout_id": workout_id, "date": date, "scheduled": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001))
    )