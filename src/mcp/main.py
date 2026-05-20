import os
from mcp.server.fastmcp import FastMCP
import subprocess
from common.garmin_function import get_last_activity_id
from common.json_activity import generate_activity_json

mcp = FastMCP("shell-server")

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
    result = generate_activity_json(activity_id)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        mcp.streamable_http_app(),
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001))
    )