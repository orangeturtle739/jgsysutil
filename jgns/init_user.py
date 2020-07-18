from jgns.subcommand import Subcommand
import argparse
import typing as t
import subprocess
import os
from pathlib import Path
from jgns.commands import nix_channel, nix_shell
from jgns.expanduser import expanduser
from xdg import XDG_CONFIG_HOME

nixpkgs_config = XDG_CONFIG_HOME / "nixpkgs"


class InitUser(Subcommand):
    def name(self) -> str:
        return "init-user"

    def help(self) -> str:
        return "Initialize a user account"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--nixpkgs-config", help=f"Directory to symlink to {nixpkgs_config}",
        )
        parser.add_argument(
            "--stable-channel", help="Channel to use as stable (e.g. 20.03)"
        )
        overwrite_options = parser.add_mutually_exclusive_group()
        overwrite_options.add_argument(
            "--overwrite-channels",
            action="store_true",
            help="overwrite existing channels",
        )
        overwrite_options.add_argument(
            "--clear-channels",
            action="store_true",
            help="remove existing channels first",
        )

    def run(self, args: t.Any) -> int:
        if args.nixpkgs_config is None:
            print("--nixpkgs-config required")
            return 1
        if args.stable_channel is None:
            print("--stable-channel required")
            return 1

        src_nixpkgs_config = expanduser(
            Path(args.nixpkgs_config), not args.no_sudo_user
        )
        if not src_nixpkgs_config.is_dir():
            print(f"Not a directory: {src_nixpkgs_config}")
            return 1
        src_nixpkgs_config = src_nixpkgs_config.resolve(strict=True)

        if nixpkgs_config.exists():
            if nixpkgs_config.resolve(strict=True) == src_nixpkgs_config:
                print(f"{nixpkgs_config} already installed")
            else:
                print(f"{nixpkgs_config} exists! Please remove then run script again.")
                return 1
        else:
            nixpkgs_config.symlink_to(src_nixpkgs_config)
            print(f"{nixpkgs_config} linked to {src_nixpkgs_config}")

        def split2(x: str) -> t.Tuple[str, str]:
            a, b = x.split()
            return a, b

        current_channels: t.Dict[str, str] = dict(
            map(
                split2,
                subprocess.run(
                    [nix_channel, "--list"],
                    text=True,
                    check=True,
                    stdout=subprocess.PIPE,
                ).stdout.splitlines(),
            )
        )
        print("Current channels:")
        for cname, curl in current_channels.items():
            print(f"    {cname} {curl}")

        print("Target channels:")
        target_channels = {
            "home-manager": f"https://github.com/rycee/home-manager/archive/release-{args.stable_channel}.tar.gz",
            "nixpkgs-unstable": f"https://nixos.org/channels/nixos-unstable",
            "nixpkgs": f"https://nixos.org/channels/nixos-{args.stable_channel}",
        }
        for cname, curl in target_channels.items():
            print(f"    {cname} {curl}")

        overlap = current_channels.keys() & target_channels.keys()
        if args.clear_channels:
            for cname in current_channels.keys():
                subprocess.run([nix_channel, "--remove", cname], check=True)
        elif args.overwrite_channels:
            for cname in overlap:
                subprocess.run([nix_channel, "--remove", cname], check=True)
        elif overlap:
            conflicts = {}
            for cname in overlap:
                if target_channels[cname] != current_channels[cname]:
                    conflicts[cname] = (target_channels[cname], current_channels[cname])
            if conflicts:
                print(
                    f"Error: would clobber existing channels: {conflicts}. Specify --overwrite-channels or --clear-channels."
                )
                return 1

        for cname, curl in target_channels.items():
            subprocess.run([nix_channel, "--add", curl, cname], check=True)
        nix_path = os.getenv("NIX_PATH")
        if nix_path:
            nix_path = f"{os.pathsep}{nix_path}"
        defexpr = Path.home() / ".nix-defexpr" / "channels"
        new_env = {**os.environ, "NIX_PATH": f"{defexpr}{nix_path}"}
        subprocess.run(
            [nix_channel, "--update"], check=True, env=new_env,
        )

        subprocess.run([nix_shell, "<home-manager>", "-A", "install"], check=True)

        return 0
