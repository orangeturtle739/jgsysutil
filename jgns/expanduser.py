from pathlib import Path
import os
import pwd


def expanduser(path: Path, use_sudo_user: bool) -> Path:
    if len(path.parts) < 1:
        return path
    head, *tail = path.parts
    if head == "~":
        sudo_uid = os.getenv("SUDO_UID")
        if sudo_uid is not None and use_sudo_user:
            uid = int(sudo_uid)
        else:
            uid = os.getuid()
        return Path(pwd.getpwuid(uid).pw_dir) / Path(*tail)
    else:
        return path
