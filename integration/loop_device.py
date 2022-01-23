import subprocess
import tempfile
import typing as t
from contextlib import contextmanager
from pathlib import Path

from jgsysutil.commands import dd, losetup


@contextmanager
def loop_device(size_mb: int) -> t.Iterator[Path]:
    disk_file_path: t.Optional[Path] = None
    loop: t.Optional[Path] = None

    try:
        disk_file = tempfile.NamedTemporaryFile(delete=False)
        disk_file_path = Path(disk_file.name)
        disk_file.close()
        subprocess.run(
            [dd, "if=/dev/zero", f"of={disk_file_path}", "bs=1M", f"count={size_mb}"],
            check=True,
            capture_output=True,
        )
        loop = Path(
            subprocess.run(
                [losetup, "--find", "--show", "--partscan", disk_file_path],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        yield loop
    finally:
        if loop is not None:
            subprocess.run(
                [losetup, "--detach", loop],
                check=True,
            )
            active = subprocess.run(
                [losetup, "-a"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()
            for a in active:
                path = a.split(":")[0]
                if path == str(loop):
                    raise RuntimeError(f"Unable to detach loop device: {loop}")
        if disk_file_path is not None:
            disk_file_path.unlink()
