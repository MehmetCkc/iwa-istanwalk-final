import os
from pathlib import Path


def secret_key():
    """Read SECRET_KEY from the environment, falling back to the local .env."""
    value = os.environ.get("SECRET_KEY")
    if value:
        return value

    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.is_file():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, candidate = line.split("=", 1)
            if name.strip() == "SECRET_KEY":
                value = candidate.strip().strip("\"'")
                if value:
                    return value

    raise RuntimeError(
        "SECRET_KEY is missing. Add it to the environment or a local .env file."
    )
