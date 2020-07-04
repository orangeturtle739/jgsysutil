from jgns.subcommand import Subcommand
import argparse
import typing as t
import subprocess
from jgns.commands import nix_env


class InstallUser(Subcommand):
    def name(self) -> str:
        return "install-user"

    def help(self) -> str:
        return "Install the user nix setup"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, args: t.Any) -> int:
        return subprocess.run(
            [
                nix_env,
                "--show-trace",
                "--install",
                "--remove-all",
                "--attr",
                "nixpkgs.my",
            ]
        ).returncode
