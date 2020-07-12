import typing as t

import argparse
from jgns.subcommand import register_subcommands, invoke_subcommand
from jgns.randomize_drive import RandomizeDrive
from jgns.install_user import InstallUser
from jgns.deploy_nixos import DeployNixos
from jgns.deploy_dotfiles import DeployDotfiles
from jgns.update_user import UpdateUser
from jgns.update_system import UpdateSystem
from jgns.format_drive import FormatDrive
from pathlib import Path
from jgns import config
import sys


def make_path(spath: t.Optional[str]) -> t.Optional[Path]:
    if spath is None:
        return None
    else:
        return Path(spath)


def main() -> int:
    parser = argparse.ArgumentParser(description="Various utility scripts")
    parser.add_argument(
        "--config-file",
        help=f"Path to configuration file. Defaults to {config.DEFAULT_PATH}",
    )
    parser.add_argument(
        "--no-sudo-user",
        help=f"Do not use the SUDO_USER environment variable to resolve ~ in paths",
        action="store_true",
    )
    register_subcommands(
        parser,
        title="cmd",
        subcommands=[
            RandomizeDrive(),
            InstallUser(),
            DeployNixos(),
            DeployDotfiles(),
            UpdateUser(),
            UpdateSystem(),
            FormatDrive(),
        ],
    )
    args = parser.parse_args()

    config_options = config.get(make_path(args.config_file), not args.no_sudo_user)
    if config_options is None:
        print(f"Error reading configuration file: {args.config_file}")
        return 1

    for key, value in config_options.items():
        if hasattr(args, key):
            setattr(args, key, value)

    return invoke_subcommand("cmd", args)


def wrapper() -> None:
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
