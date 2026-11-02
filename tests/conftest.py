import os

# common/config.py reads these at import time, so they must be set before any project import.
# Assigned (not setdefault) so values exported in the developer's shell can't change the tests.
os.environ.update(
    GARMIN_API_KEY="k" * 32,
    LETSENCRYPT_HOST="testserver",
)

import pytest  # noqa: E402

API_KEY = os.environ["GARMIN_API_KEY"]


@pytest.fixture
def anyio_backend():
    return "asyncio"
