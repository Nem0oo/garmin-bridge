import os

API_KEY = os.getenv("GARMIN_API_KEY")
if not API_KEY:
    raise ValueError("GARMIN_API_KEY environment variable is required")
DOMAIN = os.getenv("LETSENCRYPT_HOST")
# Default path kept for existing deployments that mount their token folder at ~/.GarminDb
GARMIN_TOKEN_STORE = os.getenv("GARMIN_TOKEN_STORE", os.path.expanduser("~/.GarminDb/garmin_tokens.json"))
