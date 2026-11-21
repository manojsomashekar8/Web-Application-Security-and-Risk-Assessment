"""Load .env into the environment for the test run, so `make test` and direct pytest runs see the same
credentials as the stack. Existing environment variables win; .env is never printed."""
import os
import pathlib

ENV = pathlib.Path(__file__).resolve().parents[1] / ".env"

if ENV.exists():
    for line in ENV.read_text().splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key, value)
