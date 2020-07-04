from jgns.subcommand import Subcommand
import argparse
import typing as t
import subprocess
import uuid
import math
from getpass import getpass
from pathlib import Path
from jgns.commands import (
    cryptsetup,
    gdisk,
    pvcreate,
    vgcreate,
    lvcreate,
    swapon,
    free,
    mount,
    mkdir,
    mkswap,
    mkfs_ext4,
    mkfs_fat,
)


def partition_path(drive_path: Path, pnum: int) -> Path:
    parent, name = drive_path.parent, drive_path.name
    if name.startswith("sd"):
        return parent / f"{name}{pnum}"
    elif name.startswith("nvme") or name.startswith("loop"):
        return parent / f"{name}p{pnum}"
    else:
        raise ValueError(f"Unknown drive type: {drive_path}")


def total_mem() -> int:
    for line in subprocess.run(
        [free, "--gibi"], text=True, stdout=subprocess.PIPE, check=True
    ).stdout.splitlines():
        if line.startswith("Mem: "):
            return int(line.split()[1])
    raise ValueError()


def run(
    drive: Path, swap_size: t.Optional[str], mount_point: Path, passwd: str
) -> None:
    lvm_uuid = str(uuid.uuid4())
    prefix = f"{lvm_uuid}"
    luks_mapper_name = prefix
    vg_name = f"{prefix}_vg"
    swap_name = f"{prefix}_swap"
    root_name = f"{prefix}_root"

    swap_size = swap_size or f"{2**math.ceil(math.log2(total_mem()))}G"

    gdisk_commands = [
        "o",  # delete all partitions and create a new protective MBR
        "Y",  # confirm
        "n",  # new partition
        "",  # enter, default partition number 1
        "",  # enter, default start position
        "+512M",  # offset to end position
        "ef00",  # EFI System code
        "n",  # new partition
        "",  # enter, default partition number 2
        "",  # enter, default start position
        "",  # enter, default end position (rest of the drive)
        "8309",  # Linux LUKS
        "w",  # write partition table and exit
        "Y",  # confirm
        "",  # final trailing enter
    ]
    subprocess.run(
        [gdisk, drive], input="\n".join(gdisk_commands), text=True, check=True
    )
    subprocess.run([gdisk, "-l", drive], check=True)
    subprocess.run(
        [cryptsetup, "luksFormat", partition_path(drive, 2)],
        input=passwd,
        text=True,
        check=True,
    )
    subprocess.run([cryptsetup, "luksDump", partition_path(drive, 2)], check=True)
    subprocess.run(
        [cryptsetup, "luksOpen", partition_path(drive, 2), luks_mapper_name],
        input=passwd,
        text=True,
        check=True,
    )
    subprocess.run([pvcreate, f"/dev/mapper/{luks_mapper_name}"], check=True)
    subprocess.run([vgcreate, vg_name, f"/dev/mapper/{luks_mapper_name}"], check=True)
    subprocess.run([lvcreate, "-L", swap_size, "-n", swap_name, vg_name], check=True)
    subprocess.run([lvcreate, "-l", "100%FREE", "-n", root_name, vg_name], check=True)
    subprocess.run([mkfs_fat, partition_path(drive, 1)], check=True)
    subprocess.run([mkfs_ext4, "-L", "root", f"/dev/{vg_name}/{root_name}"], check=True)
    subprocess.run([mkswap, "-L", "swap", f"/dev/{vg_name}/{swap_name}"], check=True)

    subprocess.run([mkdir, "-p", f"{mount_point}"], check=True)
    subprocess.run([mount, f"/dev/{vg_name}/{root_name}", mount_point], check=True)
    subprocess.run([mkdir, "-p", f"{mount_point}/boot"], check=True)
    subprocess.run([mount, partition_path(drive, 1), f"{mount_point}/boot"], check=True)
    subprocess.run([swapon, f"/dev/{vg_name}/{swap_name}"], check=True)


class FormatDrive(Subcommand):
    def name(self) -> str:
        return "format-drive"

    def help(self) -> str:
        return "Prepare a drive for a nixos installation."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--drive", help="drive name (/dev/<whatever>)", required=True
        )
        parser.add_argument(
            "--swap-size",
            help="swap size, defaults to 2**n G where 2**n G >= total memory",
        )
        parser.add_argument("--mount", help="directory to mount system in")

    def run(self, args: t.Any) -> int:
        passwd = getpass("Password: ")
        confirm = getpass("Confirm : ")
        if passwd != confirm:
            raise ValueError("Passwords do not match")
        run(Path(args.drive), args.swap_size, Path(args.mount), passwd)
        return 0
