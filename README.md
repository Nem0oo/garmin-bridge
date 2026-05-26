# Garmin Bridge

A self-hosted bridge that syncs Garmin Connect health data locally and exposes it via a REST API and an MCP server.

## Why

In 2025 I started running again, just for fun at first (yeah I know, fun is relative). Then I stumbled on a news about a marathon taking place in august and I thought it could be a good thing to fix an objective to my new hobbie. I had no knoledge at all about performance in running so I naturally turned to an AI to coach me. I gave it feedback by sending it screenshots of my Garmin acount. After looking around I found[GarminDB](https://github.com/tcgoetz/GarminDB) and working around it I came up with an API. And recently I added an MCP server, so no more screenshot.

## What it does

- Syncs Garmin Connect data on demand (activities, daily monitoring, sleep, weight)
- Exposes health data over a REST API (daily metrics, sleep details, activity summaries, activity plots)
- Exposes the last activity as an MCP tool for AI agent consumption
- Sync runs in the background with a lock file to prevent concurrent runs; status is queryable

## Stack

| Component     | Technology |
|---------------|------------|
| REST API      | FastAPI / Uvicorn (port 8000) |
| MCP server    | FastMCP / Uvicorn (port 8001) |
| Data sync     | GarminDB (built from submodule) |
| Databases     | SQLite × 3 (monitoring, activities, summary) |
| CI/CD         | GitHub Actions |

## API endpoints

All endpoints require authentication via `Authorization: Bearer <key>` header or `?api_key=` query parameter.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Health check (no auth) |
| `GET`  | `/dailymetrics?days=7` | Daily metrics for the last N days |
| `GET`  | `/activitysummary?days=30` | Activity summaries for the last N days |
| `GET`  | `/sleepdetails?days=7` | Sleep details for the last N days |
| `GET`  | `/last_activity` | ID of the most recent activity |
| `GET`  | `/activities/{id}/json` | Full time-series data for an activity |
| `GET`  | `/activities/{id}/plot` | Matplotlib PNG plot for an activity |
| `POST` | `/sync` | Trigger a Garmin Connect sync |
| `GET`  | `/status` | Sync status (idle / running / error) |

## Run locally

```bash
git clone --recurse-submodules <repo>
docker build -t garmin-bridge .
docker run \
  -e GARMIN_API_KEY=<key> \
  -e GARMIN_DB_PATH=/data/garmin.db \
  -e GARMIN_ACTIVITIES_DB_PATH=/data/garmin_activities.db \
  -e GARMIN_SUMMARY_DB_PATH=/data/garmin_summary.db \
  -v /path/to/garmin/data:/data \
  -p 8000:8000 -p 8001:8001 \
  garmin-bridge
```

## Docker-compose example

```yml
services:
  garmin-bridge:
    image: garmin-bridge
    container_name: garmin-bridge
    ports:
      - "8000:8000"
      - "8001:8001"
    environment: 
      - TZ=REPLACE_WITH_YOUR_TIME_ZONE
      - GARMIN_DB_PATH=/app/data/garmin.db
      - GARMIN_SUMMARY_DB_PATH=/app/data/garmin_summary.db
      - GARMIN_ACTIVITIES_DB_PATH=/app/data/garmin_activities.db
      - GARMIN_API_KEY=REPLACE_WITH_API_KEY

    volumes:
      - ./garmindb_conf:/root/.GarminDb:rw
      - ./garmindb_data:/root/HealthData:rw
      - ./garmindb_data/DBs/garmin.db:/app/data/garmin.db:rw
      - ./garmindb_data/DBs/garmin_summary.db:/app/data/garmin_summary.db:rw
      - ./garmindb_data/DBs/garmin_activities.db:/app/data/garmin_activities.db:rw
      
    restart: unless-stopped
```


### Required GarminDB configuration
Please refer to [GarminDB instructions](https://github.com/tcgoetz/GarminDB#using-it) but basically : 

Mount [GarminConnectConfig.json.example](https://raw.githubusercontent.com/tcgoetz/GarminDB/master/garmindb/GarminConnectConfig.json.example) to ~/.GarminDb/GarminConnectConfig.json, edit it, and add your Garmin Connect username and password and adjust the start dates to match the dates of your data in Garmin Connect.

### Required environment variables

| Variable | Description |
|----------|-------------|
| `GARMIN_API_KEY` | API key for all protected endpoints |
| `GARMIN_DB_PATH` | Path to `garmin_monitoring.db` |
| `GARMIN_ACTIVITIES_DB_PATH` | Path to `garmin_activities.db` |
| `GARMIN_SUMMARY_DB_PATH` | Path to `garmin_summary.db` |

### Required CI secrets

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |

## Notes

- The GarminDB submodule is built into a wheel at Docker build time — no PyPI dependency on `garmindb`.
- `libfaketime` is used during the download step only (`FAKETIME="+1d"`) to work around Garmin Connect's date window filtering.
