from __future__ import annotations

import os
from pathlib import Path


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and (
        (s[0] == "'" and s[-1] == "'") or (s[0] == '"' and s[-1] == '"')
    ):
        return s[1:-1]
    return s


def load_dotenv_if_present(dotenv_path: Path) -> None:
    """Minimal .env loader (KEY=VALUE, supports single/double-quoted values).

    Only sets vars that are not already present in the environment.
    """
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_quotes(value.strip())
        if key and key not in os.environ:
            os.environ[key] = value


def find_and_load_env() -> None:
    """Load env from nearest known location.

    We keep it simple:
    - Prefer exercise/.env (repo convention for this series)
    - Also allow a local .env next to this lesson
    - Also allow CWD/.env (if you run from elsewhere)
    """
    here = Path(__file__).resolve()
    candidates = [
        here.parent / ".env",
        Path.cwd() / ".env",
    ]
    for p in candidates:
        load_dotenv_if_present(p)
