from datetime import datetime

def time_to_minutes(time_str):
    if not time_str:
        return None
    try:
        dt = datetime.strptime(time_str, "%H:%M:%S.%f")
        return round(dt.hour * 60 + dt.minute + dt.second / 60, 2)
    except ValueError:
        try:
            dt = datetime.strptime(time_str, "%H:%M:%S")
            return round(dt.hour * 60 + dt.minute + dt.second / 60, 2)
        except Exception:
            return None

def time_to_hours(time_str):
    if not time_str:
        return None
    try:
        # Essaye HH:MM:SS.microsec
        dt = datetime.strptime(time_str, "%H:%M:%S.%f")
        return round(dt.hour + dt.minute / 60 + dt.second / 3600, 2)
    except ValueError:
        try:
            # Fallback: HH:MM:SS sans microsec
            dt = datetime.strptime(time_str, "%H:%M:%S")
            return round(dt.hour + dt.minute / 60 + dt.second / 3600, 2)
        except Exception:
            return None