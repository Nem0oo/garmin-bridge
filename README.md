# Garmin Bridge

A self-hosted MCP server to create and schedule workouts on Garmin Connect from an AI agent.

## Why

In 2025 I started running again, just for fun at first (yeah I know, fun is relative). Then I stumbled on a news about a marathon taking place in august and I thought it could be a good thing to fix an objective to my new hobbie. I had no knoledge at all about performance in running so I naturally turned to an AI to coach me. I gave it feedback by sending it screenshots of my Garmin acount. After looking around I found [GarminDB](https://github.com/tcgoetz/GarminDB) and working around it I came up with an API. And recently I added an MCP server, so no more screenshot.

Since Garmin opened an official API, reading health data is handled elsewhere. The bridge now only does what that API can't: writing workouts to Garmin Connect. The previous read tools (REST API + MCP) are available at the git tag `pre-readonly-removal`.

## What it does

MCP tools (via [garminconnect](https://github.com/cyberjunky/python-garminconnect)):

| Tool | Description |
|------|-------------|
| `server_health` | Health check |
| `push_workout` | Create a running workout (steps, targets, repeats) and schedule it on a date |
| `list_workouts` | List saved workouts |
| `get_workout` | Full detail of a saved workout |
| `schedule_existing_workout` | Schedule a saved workout on a date |
| `move_scheduled_workout` | Move a scheduled workout to another date |
| `get_scheduled_workouts` | Workouts scheduled in a given month |

## Stack

| Component  | Technology |
|------------|------------|
| MCP server | FastMCP / Uvicorn (port 8001) |
| Garmin API | garminconnect |
| CI/CD      | GitHub Actions → Docker Hub → n8n webhook |

## Run

```bash
docker build -t garmin-bridge .
docker run \
  -e GARMIN_API_KEY=<key> \
  -e LETSENCRYPT_HOST=<public host name> \
  -v /path/to/garmin_tokens_dir:/root/.GarminDb \
  -p 8001:8001 \
  garmin-bridge
```

The MCP endpoint is `/mcp?api_key=<key>`.

### Docker-compose example

```yml
services:
  garmin-bridge:
    image: garmin-bridge
    container_name: garmin-bridge
    ports:
      - "8001:8001"
    environment:
      - TZ=REPLACE_WITH_YOUR_TIME_ZONE
      - GARMIN_API_KEY=REPLACE_WITH_API_KEY
      - LETSENCRYPT_HOST=REPLACE_WITH_HOST
    volumes:
      - ./garmin_tokens:/root/.GarminDb:rw
    restart: unless-stopped
```

### Garmin login

The bridge uses saved Garmin Connect tokens and refreshes them on its own. To create them (first setup) or replace them when they stop working:

```bash
docker exec -it garmin-bridge python -m login
```

It asks for your Garmin email, password and MFA code if needed (or reads `GARMIN_EMAIL` / `GARMIN_PASSWORD`), then saves the tokens to `GARMIN_TOKEN_STORE`.

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GARMIN_API_KEY` | yes | API key expected in the `api_key` query parameter |
| `LETSENCRYPT_HOST` | yes | Host name allowed by the MCP transport security |
| `GARMIN_TOKEN_STORE` | no | Token file path (default `~/.GarminDb/garmin_tokens.json`) |
| `PORT` | no | MCP server port (default `8001`) |

### Required CI secrets

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
| `N8N_WEBHOOK_ID` | n8n webhook triggering the redeploy |
