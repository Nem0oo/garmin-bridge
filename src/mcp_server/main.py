import os
from mcp.server.fastmcp import FastMCP
from common.garmin_function import get_last_activity_id, get_daily_metrics as fetch_daily_metrics
from common.json_activity import generate_activity_json
from mcp.server.fastmcp.server import TransportSecuritySettings
from common.config import DOMAIN, API_KEY
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
def status() -> str:
    """Test le mcp"""
    return "Server is up and running !"

@mcp.tool()
def get_last_activity_details() -> dict:
    """
    Return details from the last activity recorded in json.
    No args
    Returns: dict containing timestamps, distances, cadences,altitude, heart rate, rr, speed and temperature
    """
    last_run = get_last_activity_id()
    activity_id = last_run["activity_id"]
    if activity_id is None:
        return {"error": "No activity found in database"}
    result = generate_activity_json(activity_id)
    return result

@mcp.tool()
def get_daily_metrics(days : int = 2) -> dict:
    """
    Args : days is the number of days to be returned. default is 2
    Returns a dict containing details from day to day metrics, such as weight, sleep data, stress level, steps, calories...
    """
    return fetch_daily_metrics(days)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001))
    )