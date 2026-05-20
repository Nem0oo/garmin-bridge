import os
from pathlib import Path

API_KEY = os.getenv("GARMIN_API_KEY", "XXXXXXXXXXXXXXXXX")
GARMIN_DB = os.getenv("GARMIN_DB_PATH", "./garmin.db")
GARMIN_ACTIVITIES = os.getenv("GARMIN_ACTIVITIES_DB_PATH", "./garmin_activities.db")
LOCK_FILE = Path("/tmp/sync.lock")
STATUS_FILE = Path("/tmp/sync.status.json")
GARMIN_SUMMARY_DB = os.getenv("GARMIN_SUMMARY_DB_PATH", "./garmin_summary.db")