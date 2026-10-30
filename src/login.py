"""Interactive Garmin Connect login: saves fresh tokens to GARMIN_TOKEN_STORE.

Use for a first setup or when the saved tokens no longer work:
    docker exec -it garmin-bridge python -m login
"""
import getpass
import os
from pathlib import Path

from garminconnect import Garmin

# Read directly so the script works without GARMIN_API_KEY (common.config requires it).
TOKEN_STORE = os.getenv("GARMIN_TOKEN_STORE", os.path.expanduser("~/.GarminDb/garmin_tokens.json"))


def main() -> None:
    email = os.getenv("GARMIN_EMAIL") or input("Garmin email: ")
    password = os.getenv("GARMIN_PASSWORD") or getpass.getpass("Garmin password: ")

    client = Garmin(email, password, prompt_mfa=lambda: input("MFA code: "))
    # No tokenstore: always log in with credentials, even if stale tokens exist.
    client.login()

    path = Path(TOKEN_STORE).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    client.client.dump(str(path))
    print(f"Logged in as {client.get_full_name()}, tokens saved to {path}")


if __name__ == "__main__":
    main()
