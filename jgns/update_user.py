from jgns.subcommand import Subcommand
import argparse
import typing as t
import subprocess
from jgns.commands import nix_env, nix_channel


class UpdateUser(Subcommand):
    def name(self) -> str:
        return "update-user"

    def help(self) -> str:
        return "Update the user channels and packages"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        pass

    def run(self, args: t.Any) -> int:
        status = subprocess.run([nix_channel, "--update"]).returncode
        if status != 0:
            return status
        return subprocess.run([nix_env, "--upgrade"]).returncode
