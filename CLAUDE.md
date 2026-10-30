# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

MCP server that writes workouts to Garmin Connect (create, schedule, move, list) through the
[garminconnect](https://github.com/cyberjunky/python-garminconnect) library. Reading health data is
out of scope (handled by another project using the official Garmin API). The former read tools and
GarminDB sync live at the git tag `pre-readonly-removal`.

## Running

```bash
docker build -t garmin-bridge .
docker run -e GARMIN_API_KEY=<key> -e LETSENCRYPT_HOST=<host> \
           -v <tokens dir>:/root/.GarminDb -p 8001:8001 garmin-bridge
```

Outside Docker: `cd src && python -m mcp_server.main`.

`GARMIN_API_KEY` and `LETSENCRYPT_HOST` are **required**: the server fails at startup without them.

## Architecture

- `src/common/config.py`: env vars (`GARMIN_API_KEY`, `LETSENCRYPT_HOST`, `GARMIN_TOKEN_STORE`).
- `src/mcp_server/main.py`: FastMCP app, `ApiKeyMiddleware` (checks `?api_key=`), workout models
  (steps, targets, end conditions) and the MCP tools. `_garmin_client()` logs in from the token store
  on each call.
- `src/login.py`: interactive login (`docker exec -it garmin-bridge python -m login`) that writes
  fresh tokens to `GARMIN_TOKEN_STORE`.

## Key constraints

- The default token path `~/.GarminDb/garmin_tokens.json` is kept on purpose: existing deployments
  mount their token folder there.
- garminconnect refreshes tokens and saves them back to the token store; the volume must be writable.
