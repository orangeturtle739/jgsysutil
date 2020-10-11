import subprocess
from pathlib import Path

import click

from jgsysutil.commands import shred


def randomize_drive_lib(drive: Path) -> None:
    # subprocess.run(
    #     f'set -euf -o pipefail; {openssl} enc -aes-256-ctr -pbkdf2 -iter 100000 -pass pass:"$({dd} if=/dev/urandom bs=128 count=1 2>/dev/null | base64)" -nosalt < /dev/zero | {dd} of={drive} bs=1M status=progress conv=noerror,sync',
    #     shell=True,
    #     check=True,
    # )
    subprocess.run([shred, "--verbose", "-n", "1", drive], check=True)


@click.command()
@click.argument(
    "drive",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, writable=True, resolve_path=True
    ),
)
@click.confirmation_option(prompt="Are you sure?")
def randomize_drive(drive: str) -> None:
    """
    Randomizes DRIVE
    """
    click.secho(f"Wiping {drive}", fg="red")
    randomize_drive_lib(Path(drive))
