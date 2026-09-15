from datetime import datetime
from .garmin_function import get_activity_records, get_running_dynamics
from .tools import time_to_ms


def generate_activity_json(activity_id: str):
    rows = get_activity_records(activity_id)

    timestamps = [datetime.fromisoformat(row["timestamp"]) for row in rows]

    duration = timestamps[-1] - timestamps[0]
    total_seconds = int(duration.total_seconds())
    total_minutes = total_seconds // 60
    total_hours = total_minutes // 60
    remaining_minutes = total_minutes % 60
    duration_str = f"{total_hours}h {remaining_minutes}min" if total_hours else f"{remaining_minutes} min"

    distance_values = [row["distance"] for row in rows if row["distance"] is not None]
    total_distance_km = round(distance_values[-1], 2) if distance_values else 0

    records = []
    for row in rows:
        speed = row["speed"]
        pace_min_per_km = round(60 / speed, 2) if speed and speed > 0 else None
        # fractional_cadence holds the fractional rpm part; add it back for true instantaneous cadence.
        cadence = row["cadence"] + row["fractional_cadence"] if row["cadence"] is not None and row["fractional_cadence"] is not None else row["cadence"]

        records.append({
            "timestamp": row["timestamp"],
            "distance_km": round(row["distance"], 3) if row["distance"] is not None else None,
            "cadence": cadence,
            "altitude_m": row["altitude"],
            "hr_bpm": row["hr"],
            "rr_ms": row["rr"],
            "speed_kmh": round(speed, 2) if speed is not None else None,
            "pace_min_per_km": pace_min_per_km,
            "temperature_c": row["temperature"],
            "power_w": row["power"],
            "vertical_oscillation_mm": row["vertical_oscillation"],
            "vertical_ratio_percent": row["vertical_ratio"],
            "step_length_mm": row["step_length"],
            "ground_contact_time_ms": time_to_ms(row["ground_contact_time"]),
        })

    def build_series(key):
        values = [record[key] for record in records]
        return values if any(v is not None for v in values) else None

    result = {
        "activity_id": activity_id,
        "summary": {
            "total_distance_km": total_distance_km,
            "duration_seconds": total_seconds,
            "duration_human": duration_str,
            "record_count": len(records),
            "start_time": records[0]["timestamp"],
            "end_time": records[-1]["timestamp"],
        },
        "series": {
            "timestamps": [record["timestamp"] for record in records],
            "distance_km": build_series("distance_km"),
            "cadence": build_series("cadence"),
            "altitude_m": build_series("altitude_m"),
            "hr_bpm": build_series("hr_bpm"),
            "rr_ms": build_series("rr_ms"),
            "speed_kmh": build_series("speed_kmh"),
            "pace_min_per_km": build_series("pace_min_per_km"),
            "temperature_c": build_series("temperature_c"),
            "power_w": build_series("power_w"),
            "vertical_oscillation_mm": build_series("vertical_oscillation_mm"),
            "vertical_ratio_percent": build_series("vertical_ratio_percent"),
            "step_length_mm": build_series("step_length_mm"),
            "ground_contact_time_ms": build_series("ground_contact_time_ms"),
        }
    }

    running_dynamics = get_running_dynamics(activity_id)
    if running_dynamics:
        result["running_dynamics"] = running_dynamics

    return result
