from jgns.subcommand import Subcommand
import argparse
import typing as t
import subprocess
import os
from jgns.commands import nixos_rebuild, nix_channel


class UpdateSystem(Subcommand):
    def name(self) -> str:
        return "update-system"

    def help(self) -> str:
        return "Update the system channels and packages"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, args: t.Any) -> int:
        if os.geteuid() != 0:
            print("Must be root")
            return 1
        status = subprocess.run([nix_channel, "--update"]).returncode
        if status != 0:
            return status
        return subprocess.run([nixos_rebuild, "--upgrade", "switch"]).returncode
