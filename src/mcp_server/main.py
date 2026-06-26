import os
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field
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

_STEP_TYPE = {
    "warmup":   {"stepTypeId": 1, "stepTypeKey": "warmup",   "displayOrder": 1},
    "cooldown": {"stepTypeId": 2, "stepTypeKey": "cooldown", "displayOrder": 2},
    "interval": {"stepTypeId": 3, "stepTypeKey": "interval", "displayOrder": 3},
    "recovery": {"stepTypeId": 4, "stepTypeKey": "recovery", "displayOrder": 4},
}

# (conditionTypeId, conditionTypeKey) — from garminconnect.workout.ConditionType
_CONDITION_TYPE = {
    "lap_button":        (1,  "lap.button"),
    "time":              (2,  "time"),
    "distance":          (3,  "distance"),
    "calories":          (4,  "calories"),
    "power":             (5,  "power"),
    "heart_rate":        (6,  "heart.rate"),
    "iterations":        (7,  "iterations"),
    "fixed_rest":        (8,  "fixed.rest"),
    "fixed_repetition":  (9,  "fixed.repetition"),
    "reps":              (10, "reps"),
}

# ── Target types ──────────────────────────────────────────────────────────────

_TARGET_TYPE = {
    "no_target":      (1,  "no.target"),
    "power_zone":     (2,  "power_zone"),
    "cadence":        (3,  "cadence"),
    "heart_rate_zone":(4,  "heart_rate_zone"),
    "speed_zone":     (5,  "speed_zone"),
    "pace_zone":      (6,  "pace_zone"),
    "grade":          (7,  "grade"),
    "heart_rate_lap": (8,  "heart_rate_lap"),
    "power_lap":      (9,  "power_lap"),
    "resistance":     (15, "resistance"),
}

class TargetNone(BaseModel):
    type: Literal["no_target"]

class TargetPace(BaseModel):
    type: Literal["pace_zone"]
    allure_rapide: float = Field(description="Borne rapide en min/km (ex: 5.0 pour 5:00/km).")
    allure_lente: float = Field(description="Borne lente en min/km (ex: 5.5 pour 5:30/km).")

class TargetHeartRate(BaseModel):
    type: Literal["heart_rate_zone"]
    bpm_min: int
    bpm_max: int

class TargetCadence(BaseModel):
    type: Literal["cadence"]
    spm_min: int = Field(description="Cadence minimale en pas par minute.")
    spm_max: int = Field(description="Cadence maximale en pas par minute.")

class TargetPower(BaseModel):
    type: Literal["power_zone"]
    watts_min: int
    watts_max: int

class TargetSpeed(BaseModel):
    type: Literal["speed_zone"]
    kmh_min: float
    kmh_max: float

class TargetGrade(BaseModel):
    type: Literal["grade"]
    grade_min: float = Field(description="Pente minimale en %.")
    grade_max: float = Field(description="Pente maximale en %.")

class TargetHeartRateLap(BaseModel):
    type: Literal["heart_rate_lap"]
    bpm_min: int
    bpm_max: int

class TargetPowerLap(BaseModel):
    type: Literal["power_lap"]
    watts_min: int
    watts_max: int

class TargetResistance(BaseModel):
    type: Literal["resistance"]
    resistance_min: float
    resistance_max: float

Target = Annotated[
    Union[
        TargetNone, TargetPace, TargetHeartRate, TargetCadence, TargetPower,
        TargetSpeed, TargetGrade, TargetHeartRateLap, TargetPowerLap, TargetResistance,
    ],
    Field(discriminator="type")
]


def _target_dict(target: Target) -> dict:
    tid, tkey = _TARGET_TYPE[target.type]
    base = {"workoutTargetTypeId": tid, "workoutTargetTypeKey": tkey, "displayOrder": tid}
    range_map = {
        "pace_zone":       lambda t: (round(t.allure_rapide * 60, 1), round(t.allure_lente * 60, 1)),
        "heart_rate_zone": lambda t: (float(t.bpm_min), float(t.bpm_max)),
        "cadence":         lambda t: (float(t.spm_min), float(t.spm_max)),
        "power_zone":      lambda t: (float(t.watts_min), float(t.watts_max)),
        "speed_zone":      lambda t: (float(t.kmh_min), float(t.kmh_max)),
        "grade":           lambda t: (float(t.grade_min), float(t.grade_max)),
        "heart_rate_lap":  lambda t: (float(t.bpm_min), float(t.bpm_max)),
        "power_lap":       lambda t: (float(t.watts_min), float(t.watts_max)),
        "resistance":      lambda t: (float(t.resistance_min), float(t.resistance_max)),
    }
    if target.type in range_map:
        v1, v2 = range_map[target.type](target)
        base["targetValueOne"] = v1
        base["targetValueTwo"] = v2
    return base


# ── End condition types ───────────────────────────────────────────────────────

class EndConditionTime(BaseModel):
    type: Literal["time"]
    duree_minutes: float

class EndConditionDistance(BaseModel):
    type: Literal["distance"]
    distance_km: float

class EndConditionCalories(BaseModel):
    type: Literal["calories"]
    calories: int = Field(description="Objectif en kcal.")

class EndConditionPower(BaseModel):
    type: Literal["power"]
    watts: int

class EndConditionHeartRate(BaseModel):
    type: Literal["heart_rate"]
    bpm: int

class EndConditionLapButton(BaseModel):
    type: Literal["lap_button"]

class EndConditionIterations(BaseModel):
    type: Literal["iterations"]
    count: int

class EndConditionFixedRest(BaseModel):
    type: Literal["fixed_rest"]
    duree_minutes: float

class EndConditionFixedRepetition(BaseModel):
    type: Literal["fixed_repetition"]
    count: int

class EndConditionReps(BaseModel):
    type: Literal["reps"]
    count: int

EndCondition = Annotated[
    Union[
        EndConditionTime, EndConditionDistance, EndConditionCalories,
        EndConditionPower, EndConditionHeartRate, EndConditionLapButton,
        EndConditionIterations, EndConditionFixedRest, EndConditionFixedRepetition,
        EndConditionReps,
    ],
    Field(discriminator="type")
]

class SimpleStep(BaseModel):
    type: Literal["warmup", "interval", "recovery", "cooldown"]
    end_condition: EndCondition
    target: Target | None = Field(default=None, description="Objectif du step. Optionnel — omit for no target.")

class RepeatStep(BaseModel):
    type: Literal["repeat"]
    repetitions: int
    steps: list[SimpleStep]

WorkoutStep = Annotated[Union[SimpleStep, RepeatStep], Field(discriminator="type")]


def _end_condition_dict(ec: EndCondition) -> tuple[dict, float | None]:
    cid, ckey = _CONDITION_TYPE[ec.type]
    base = {"conditionTypeId": cid, "conditionTypeKey": ckey, "displayOrder": cid, "displayable": True}
    value_map = {
        "time":             lambda e: e.duree_minutes * 60,
        "distance":         lambda e: e.distance_km * 1000,
        "calories":         lambda e: float(e.calories),
        "power":            lambda e: float(e.watts),
        "heart_rate":       lambda e: float(e.bpm),
        "lap_button":       lambda e: None,
        "iterations":       lambda e: float(e.count),
        "fixed_rest":       lambda e: e.duree_minutes * 60,
        "fixed_repetition": lambda e: float(e.count),
        "reps":             lambda e: float(e.count),
    }
    return base, value_map[ec.type](ec)


def _estimated_seconds(s: SimpleStep) -> int:
    ec = s.end_condition
    if ec.type == "time":
        return int(ec.duree_minutes * 60)
    if ec.type == "fixed_rest":
        return int(ec.duree_minutes * 60)
    if ec.type == "distance" and isinstance(s.target, TargetPace):
        allure_moy = (s.target.allure_rapide + s.target.allure_lente) / 2
        return int(ec.distance_km * allure_moy * 60)
    return 0


def _build_steps(steps: list[WorkoutStep], start_order: int = 1):
    from garminconnect.workout import ExecutableStep, create_repeat_group

    built = []
    order = start_order
    for s in steps:
        if s.type == "repeat":
            inner, _ = _build_steps(s.steps, start_order=1)
            built.append(create_repeat_group(s.repetitions, inner, order))
        else:
            end_cond, end_val = _end_condition_dict(s.end_condition)
            built.append(ExecutableStep(
                stepOrder=order,
                stepType=_STEP_TYPE[s.type],
                endCondition=end_cond,
                endConditionValue=end_val,
                targetType=_target_dict(s.target) if s.target else None,
            ))
        order += 1
    return built, order


def _total_duration(steps: list[WorkoutStep]) -> int:
    total = 0
    for s in steps:
        if s.type == "repeat":
            total += _total_duration(s.steps) * s.repetitions
        else:
            total += _estimated_seconds(s)
    return total


@mcp.tool()
def push_workout(date: str, name: str, steps: list[WorkoutStep]) -> dict:
    """
    Push a structured running workout to Garmin Connect and schedule it.
    Args:
        date: Target date in YYYY-MM-DD format (e.g., "2026-06-27")
        name: Workout name displayed on the watch
        steps: Ordered list of workout steps. Use SimpleStep for warmup/interval/recovery/cooldown,
               and RepeatStep to loop a block of SimpleSteps N times.
    Returns:
        dict with workout_id, date, and scheduled status
    """
    from garminconnect import Garmin
    from garminconnect.workout import RunningWorkout, WorkoutSegment

    client = Garmin()
    client.login(os.path.expanduser(GARMIN_TOKEN_STORE))

    workout_steps, _ = _build_steps(steps)

    segment = WorkoutSegment(
        segmentOrder=1,
        sportType={"sportTypeId": 1, "sportTypeKey": "running", "displayOrder": 1},
        workoutSteps=workout_steps,
    )

    workout = RunningWorkout(
        workoutName=name,
        estimatedDurationInSecs=_total_duration(steps),
        workoutSegments=[segment],
    )

    result = client.upload_running_workout(workout)

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