from jgns.subcommand import Subcommand
import argparse
import typing as t
import subprocess
import socket
import os
from pathlib import Path
from jgns.commands import rsync, nixos_rebuild


class DeployNixos(Subcommand):
    def __init__(self) -> None:
        self.local_hostname = socket.gethostname()

    def name(self) -> str:
        return "deploy-nixos"

    def help(self) -> str:
        return "Deploy a nixos configuration"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--nixos-dir",
            help="Directory with nixos configurations in it. The configuration for a host should be hostname/configuration.nix.",
        )
        parser.add_argument(
            "--hostname",
            help=f"Hostname which specifies which configuration to install. Defaults to {self.local_hostname}",
        )

    def run(self, args: t.Any) -> int:
        if os.geteuid() != 0:
            print("Must be root")
            return 1
        if args.nixos_dir is None:
            print("--nixos-dir required")
            return 1
        nixos_dir = Path(args.nixos_dir).expanduser()
        if not nixos_dir.is_dir():
            print(f"Not a directory: {nixos_dir}")
            return 1
        hostname = args.hostname or self.local_hostname
        hostname_config_base = Path(hostname) / "configuration.nix"
        hostname_config = nixos_dir / hostname_config_base
        if not hostname_config.is_file():
            print(f"Not a file: {hostname_config}")
            return 1
        link_target_placeholder = nixos_dir / "configuration.nix"
        if link_target_placeholder.exists():
            print(f"{link_target_placeholder} should not exist")
            return 1

        rsync_status = subprocess.run(
            [
                rsync,
                "--archive",
                "--delete",
                "--exclude",
                "result",
                "--exclude",
                "nix",
                "--verbose",
                f"{nixos_dir}/",
                "/etc/nixos/",
            ]
        ).returncode
        if rsync_status != 0:
            return rsync_status
        Path("/etc/nixos/configuration.nix").symlink_to(
            Path("/etc/nixos") / hostname_config_base
        )
        return subprocess.run([nixos_rebuild, "switch", "--show-trace"]).returncode
