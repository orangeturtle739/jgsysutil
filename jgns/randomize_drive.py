from jgns.subcommand import Subcommand
import argparse
import typing as t
import subprocess
from pathlib import Path
from jgns.commands import openssl, dd


def randomize_drive(drive: Path) -> int:
    print(f"Wiping {drive}")
    return subprocess.run(
        f'{openssl} enc -aes-256-ctr -pbkdf2 -iter 100000 -pass pass:"$({dd} if=/dev/urandom bs=128 count=1 2>/dev/null | base64)" -nosalt < /dev/zero | {dd} of={drive} bs=1M status=progress',
        shell=True,
    ).returncode


class RandomizeDrive(Subcommand):
    def name(self) -> str:
        return "randomize-drive"

    def help(self) -> str:
        return "randomize a drive"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--drive", required=True)

    def run(self, args: t.Any) -> int:
        return randomize_drive(Path(args.drive))
