import os
from pathlib import Path

from dotenv import load_dotenv


# Load environment variables from the project root .env file.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def resolve_database_path() -> Path:
    configured_path = os.getenv(
        "DATABASE_PATH",
        "./data/permissions.db",
    )

    path = Path(configured_path)

    if not path.is_absolute():
        path = BASE_DIR / path

    return path.resolve()


APP_NAME = os.getenv(
    "APP_NAME",
    "Open Fabric Authentication and Authorization Service",
)

APP_ENV = os.getenv("APP_ENV", "development")

DATABASE_PATH = resolve_database_path()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "").strip()
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "").strip()

_configured_algorithms = os.getenv(
    "AUTH0_ALGORITHMS",
    "RS256",
)

AUTH0_ALGORITHMS = [
    algorithm.strip()
    for algorithm in _configured_algorithms.split(",")
    if algorithm.strip()
]

# Keep a secure default if the variable is empty or whitespace-only.
if not AUTH0_ALGORITHMS:
    AUTH0_ALGORITHMS = ["RS256"]