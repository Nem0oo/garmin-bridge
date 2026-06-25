# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Exposes Garmin health data (sleep, activities, daily metrics) via a REST API and an MCP server. Data is synced locally from Garmin Connect using [GarminDB](https://github.com/tcgoetz/GarminDB), then served from three SQLite databases.

## Running

The project is designed to run inside Docker:

```bash
docker build -t garmin-bridge .
docker run -e GARMIN_API_KEY=<key> \
           -e GARMIN_DB_PATH=/data/garmin.db \
           -e GARMIN_ACTIVITIES_DB_PATH=/data/garmin_activities.db \
           -e GARMIN_SUMMARY_DB_PATH=/data/garmin_summary.db \
           -e GARMIN_MONITORING_DB_PATH=/data/garmin_monitoring.db \
           -p 8000:8000 -p 8001:8001 garmin-bridge
```

To run services individually outside Docker (requires dependencies installed):

```bash
# API (port 8000)
cd src && uvicorn api.main:app --host 0.0.0.0 --port 8000

# MCP server (port 8001)
cd src && python -m mcp_server.main
```

`GARMIN_API_KEY` is **required** — the app will raise at startup if it is missing.

## Architecture

All source code is under `src/`, structured as three layers:

- **`src/common/`** — shared logic used by both servers
  - `config.py` — env var loading (DB paths, API key, lock/status file paths)
  - `garmin_function.py` — all DB queries: `get_activity_records`, `get_daily_metrics`, `get_activity_summary`, `get_sleep_details`, etc.
  - `json_activity.py` — builds the full JSON payload for an activity (series data)
  - `sync.py` — triggers GarminDB sync in a background thread; uses an atomic lock file at `/tmp/sync.lock`
  - `security.py` — `verify_api_key` FastAPI dependency; accepts key via `Authorization: Bearer` header or `?api_key=` / `?api-key=` query param (both intentional)
  - `tools.py` — `time_to_hours`, `time_to_minutes` converters for SQLite time strings

- **`src/api/`** — FastAPI REST server (port 8000)
  - `main.py` — route definitions; all protected routes use `Depends(verify_api_key)`
  - `plot_activity.py` — generates a matplotlib PNG for an activity and streams it

- **`src/mcp_server/`** — MCP server (port 8001)
  - `main.py` — exposes `get_last_activity_details` as an MCP tool

## Data flow

Sync: `POST /sync` → `trigger_sync()` → background thread runs `garmindb_cli.py` → populates the three SQLite DBs.

The download step uses `libfaketime` with `FAKETIME="+1d"` to work around Garmin Connect's date filtering. This is set only for the download subprocess, not the whole process.

## Key constraints

- `get_activity_records` is the single source of truth for raw activity data — both `json_activity.py` and `plot_activity.py` call it. Don't duplicate the query.
- `get_daily_metrics` uses batch queries (not per-row connections). Weight lookup uses `bisect` on a sorted list to find the last known weight on or before each day.
- The altitude metric in `plot_activity.py` is intentionally commented out — the sensor produces noisy data.
