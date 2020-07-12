import toml
import typing as t
from pathlib import Path
from jgns.expanduser import expanduser

DEFAULT_PATH = Path("~/.config/jgns/config.toml")


def get(path: t.Optional[Path], use_sudo_user: bool) -> t.Optional[t.Any]:
    expanded_default = expanduser(DEFAULT_PATH, use_sudo_user)
    if path is not None or expanded_default.exists():
        path = path or expanded_default
        try:
            with path.open("r") as config:
                return toml.load(config)
        except OSError:
            return None
    else:
        return {}
