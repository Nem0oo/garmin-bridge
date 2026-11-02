import os

# Key protecting the MCP endpoint, sent by clients as `Authorization: Bearer <key>`.
API_KEY = os.getenv("GARMIN_API_KEY", "").strip()
if not API_KEY:
    raise ValueError("GARMIN_API_KEY environment variable is required")
if len(API_KEY) < 32:
    raise ValueError("GARMIN_API_KEY must be at least 32 characters")
DOMAIN = os.getenv("LETSENCRYPT_HOST")
# Default path kept for existing deployments that mount their token folder at ~/.GarminDb
GARMIN_TOKEN_STORE = os.getenv("GARMIN_TOKEN_STORE", os.path.expanduser("~/.GarminDb/garmin_tokens.json"))
