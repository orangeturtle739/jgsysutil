from jgns.subcommand import Subcommand
import typing as t
import argparse
import dataclasses
import subprocess
import uuid
import math
from jgns.randomize_drive import randomize_drive
from jgns.typing import assert_never
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


@dataclasses.dataclass
class PartitionScheme:
    boot: Path
    root: Path


def partition_drive(drive: Path) -> PartitionScheme:
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
    return PartitionScheme(boot=partition_path(drive, 1), root=partition_path(drive, 2))


def configure_drive(
    partitions: PartitionScheme,
    randomize: bool,
    swap_size: t.Optional[str],
    mount_point: Path,
    passwd: str,
) -> None:
    lvm_uuid = str(uuid.uuid4())
    prefix = f"{lvm_uuid}"
    luks_mapper_name = prefix
    vg_name = f"{prefix}_vg"
    swap_name = f"{prefix}_swap"
    root_name = f"{prefix}_root"

    swap_size = swap_size or f"{2**math.ceil(math.log2(total_mem()))}G"
    if randomize:
        randomize_drive(partitions.root)
    subprocess.run(
        [cryptsetup, "luksFormat", partitions.root],
        input=passwd,
        text=True,
        check=True,
    )
    subprocess.run([cryptsetup, "luksDump", partitions.root], check=True)
    subprocess.run(
        [cryptsetup, "luksOpen", partitions.root, luks_mapper_name],
        input=passwd,
        text=True,
        check=True,
    )
    subprocess.run([pvcreate, f"/dev/mapper/{luks_mapper_name}"], check=True)
    subprocess.run([vgcreate, vg_name, f"/dev/mapper/{luks_mapper_name}"], check=True)
    subprocess.run([lvcreate, "-L", swap_size, "-n", swap_name, vg_name], check=True)
    subprocess.run([lvcreate, "-l", "100%FREE", "-n", root_name, vg_name], check=True)
    subprocess.run([mkfs_fat, partitions.boot], check=True)
    subprocess.run([mkfs_ext4, "-L", "root", f"/dev/{vg_name}/{root_name}"], check=True)
    subprocess.run([mkswap, "-L", "swap", f"/dev/{vg_name}/{swap_name}"], check=True)

    subprocess.run([mkdir, "-p", f"{mount_point}"], check=True)
    subprocess.run([mount, f"/dev/{vg_name}/{root_name}", mount_point], check=True)
    subprocess.run([mkdir, "-p", f"{mount_point}/boot"], check=True)
    subprocess.run([mount, partitions.boot, f"{mount_point}/boot"], check=True)
    subprocess.run([swapon, f"/dev/{vg_name}/{swap_name}"], check=True)


def run(
    dst: t.Union[Path, PartitionScheme],
    randomize: bool,
    swap_size: t.Optional[str],
    mount_point: Path,
    passwd: str,
) -> None:
    if isinstance(dst, Path):
        partitions = partition_drive(dst)
    elif isinstance(dst, PartitionScheme):
        partitions = dst
    else:
        assert_never(dst)

    configure_drive(partitions, randomize, swap_size, mount_point, passwd)


class PrepareDrive(Subcommand):
    def name(self) -> str:
        return "prepare-drive"

    def help(self) -> str:
        return "Prepare a drive for a nixos installation."

    def configure(self, parser: argparse.ArgumentParser) -> None:
        dst_group = parser.add_mutually_exclusive_group(required=True)
        dst_group.target = "dst"
        dst_group.add_argument(
            "--drive", help="drive to parition and then use (/dev/whatever)"
        )
        dst_group.add_argument(
            "--partitions",
            nargs=2,
            metavar=("BOOT", "ROOT"),
            help="use the following partitions",
        )
        parser.add_argument(
            "--randomize",
            action="store_true",
            help="Randomize root partition before encrypting",
        )
        parser.add_argument(
            "--swap-size",
            help="swap size, defaults to 2**n G where 2**n G >= total memory",
        )
        parser.add_argument(
            "--mount", required=True, help="directory to mount system in"
        )

    def run(self, args: t.Any) -> int:
        passwd = getpass("Password: ")
        confirm = getpass("Confirm : ")
        if passwd != confirm:
            raise ValueError("Passwords do not match")
        dst: t.Union[Path, PartitionScheme]
        if args.drive is not None:
            dst = Path(args.drive)
        else:
            dst = PartitionScheme(
                boot=Path(args.partitions[0]), root=Path(args.partitions[1])
            )
        run(dst, args.randomize, args.swap_size, Path(args.mount), passwd)
        return 0
