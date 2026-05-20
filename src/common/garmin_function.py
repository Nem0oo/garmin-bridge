from datetime import datetime, timedelta
from .config import GARMIN_DB, GARMIN_ACTIVITIES, GARMIN_SUMMARY_DB
from .connection_helper import db_connection
from .tools import time_to_hours, time_to_minutes

def get_last_activity_id():
    query = """
    SELECT activity_id, start_time
    FROM activities
    ORDER BY start_time DESC
    LIMIT 1
    """
    with db_connection(GARMIN_ACTIVITIES) as conn:
        row = conn.execute(query).fetchone()
    return {"activity_id": row["activity_id"] if row else None}

def get_activity_name(activity_id):
    query = """
    SELECT name
    FROM activities
    WHERE activity_id = ?
    """
    with db_connection(GARMIN_ACTIVITIES) as conn:
        row = conn.execute(query, (activity_id,)).fetchone()
    return {"name": row["name"] if row else None}

def get_sleep_details(n_days=7):
    start_date = (datetime.now() - timedelta(days=n_days)).strftime("%Y-%m-%d")
    
    query = """
    SELECT day, start, end, total_sleep, deep_sleep, light_sleep, rem_sleep, awake,
           avg_spo2, avg_rr, avg_stress, score, qualifier
    FROM sleep
    WHERE day >= ?
    ORDER BY day DESC
    """
    with db_connection(GARMIN_DB) as conn:
        rows = conn.execute(query, (start_date,)).fetchall()

    sleep_data = []
    for row in rows:
        sleep_data.append({
            "date": row["day"],
            "start": row["start"],
            "end": row["end"],
            "total_hours": time_to_hours(row["total_sleep"]),
            "deep_hours": time_to_hours(row["deep_sleep"]),
            "light_hours": time_to_hours(row["light_sleep"]),
            "rem_hours": time_to_hours(row["rem_sleep"]),
            "awake_hours": time_to_hours(row["awake"]),
            "avg_spo2": row["avg_spo2"],
            "avg_rr": row["avg_rr"],
            "avg_stress": row["avg_stress"],
            "score": row["score"],
            "qualifier": row["qualifier"]
        })

    return sleep_data

def get_activity_summary(n_days=30):
    start_date = (datetime.now() - timedelta(days=n_days)).strftime("%Y-%m-%d")

    query = """
    SELECT activity_id, name, type, start_time, elapsed_time, distance, calories,
           avg_hr, max_hr, ascent, training_effect, anaerobic_training_effect,
           self_eval_feel, self_eval_effort
    FROM activities
    WHERE DATE(start_time) >= ?
    ORDER BY start_time DESC
    """
    with db_connection(GARMIN_ACTIVITIES) as conn:
        rows = conn.execute(query, (start_date,)).fetchall()

    activities = []
    for row in rows:
        activities.append({
            "activity_id": row["activity_id"],
            "name": row["name"],
            "type": row["type"],
            "start_time": row["start_time"],
            "duration_min": time_to_minutes(row["elapsed_time"]),
            "distance_km": round(row["distance"] / 1000, 2) if row["distance"] else None,
            "calories": row["calories"],
            "avg_hr": row["avg_hr"],
            "max_hr": row["max_hr"],
            "elevation_gain_m": row["ascent"],
            "training_effect": row["training_effect"],
            "anaerobic_effect": row["anaerobic_training_effect"],
            "self_eval_feel": row["self_eval_feel"],
            "self_eval_effort": row["self_eval_effort"]
        })

    return activities

def get_daily_metrics(n_days=7):
    start_date = (datetime.now() - timedelta(days=n_days)).strftime("%Y-%m-%d")

    with db_connection(GARMIN_SUMMARY_DB) as summary_con:
        summary_rows = summary_con.execute("""
            SELECT * FROM days_summary
            WHERE day >= ?
            ORDER BY day ASC
        """, (start_date,)).fetchall()

    results = []
    for row in summary_rows:
        day_str = row["day"]

        # Sommeil
        with db_connection(GARMIN_DB) as garmin_con:
            sleep = garmin_con.execute("SELECT * FROM sleep WHERE day = ?", (day_str,)).fetchone()

            # Poids
            weight_row = garmin_con.execute("""
                SELECT weight FROM weight
                WHERE day <= ?
                ORDER BY day DESC LIMIT 1
            """, (day_str,)).fetchone()

        result = {
            "date": day_str,
            "resting_hr": row["rhr_avg"],
            "average_hr": row["hr_avg"],
            "max_hr": row["hr_max"],
            "steps": row["steps"],
            "calories": row["calories_avg"],
            "stress_level": row["stress_avg"],
            "weight": weight_row["weight"] if weight_row else None,
            "sleep": {
                "duration_hours": time_to_hours(sleep["total_sleep"]) if sleep else None,
                "deep_hours": time_to_hours(sleep["deep_sleep"]) if sleep else None,
                "light_hours": time_to_hours(sleep["light_sleep"]) if sleep else None,
                "rem_hours": time_to_hours(sleep["rem_sleep"]) if sleep else None,
                "awake_hours": time_to_hours(sleep["awake"]) if sleep else None,
                "start": sleep["start"] if sleep else None,
                "end": sleep["end"] if sleep else None,
                "score": sleep["score"] if sleep else None,
                "qualifier": sleep["qualifier"] if sleep else None,
            },
            "body_battery": {
                "min": row["bb_min"],
                "max": row["bb_max"]
            },
            "hydration_intake": row["hydration_intake"],
            "spo2_avg": row["spo2_avg"],
            "rr_waking_avg": row["rr_waking_avg"]
        }

        results.append(result)
    return results