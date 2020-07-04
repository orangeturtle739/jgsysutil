from jgns.subcommand import Subcommand
import argparse
import typing as t
import subprocess
from pathlib import Path
from jgns.commands import stow


class DeployDotfiles(Subcommand):
    def name(self) -> str:
        return "deploy-dotfiles"

    def help(self) -> str:
        return "Deploy dotfiles"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--dotfiles-dir", help="Directory with dotfiles",
        )

    def run(self, args: t.Any) -> int:
        if args.dotfiles_dir is None:
            print("--dotfiles-dir required")
            return 1
        dotfiles_dir = Path(args.dotfiles_dir).expanduser()
        if not dotfiles_dir.is_dir():
            print(f"Not a directory: {dotfiles_dir}")
            return 1
        return subprocess.run(
            [stow, "-vv", "-t", Path("~").expanduser(), "."], cwd=dotfiles_dir
        ).returncode
