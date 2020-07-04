import toml
import typing as t
from pathlib import Path

DEFAULT_PATH = Path("~/.config/jgns/config.toml").expanduser()


def get(path: t.Optional[Path]) -> t.Optional[t.Any]:
    if path is not None or DEFAULT_PATH.exists():
        path = path or DEFAULT_PATH
        try:
            with path.open("r") as config:
                return toml.load(config)
        except OSError:
            return None
    else:
        return {}
