import dataclasses
import math
import re
import subprocess
import typing as t
import uuid
from pathlib import Path

import click

from jgsysutil.commands import (
    cryptsetup,
    free,
    gdisk,
    lvcreate,
    mkdir,
    mkfs_ext4,
    mkfs_fat,
    mkswap,
    mount,
    pvcreate,
    swapon,
    vgcreate,
)
from jgsysutil.randomize_drive import randomize_drive_lib
from jgsysutil.typing import assert_never


def partition_path(drive_path: Path, pnum: int) -> Path:
    parent, name = drive_path.parent, drive_path.name
    separator = "p" if re.match(r".*\d", name) else ""
    return parent / f"{name}{separator}{pnum}"


def total_mem() -> int:
    for line in subprocess.run(
        [free], text=True, stdout=subprocess.PIPE, check=True
    ).stdout.splitlines():
        if line.startswith("Mem: "):
            return int(line.split()[1])
    raise ValueError("Unable to determine total memory")


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

    if swap_size is None:
        x = total_mem()
        # Round up to at least 1G of swap
        swap_size = f"{2**math.ceil(math.log2(max(1024 * 1024, x) / 1024 / 1024))}G"
    if randomize:
        randomize_drive_lib(partitions.root)
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
    subprocess.run([pvcreate, "-y", f"/dev/mapper/{luks_mapper_name}"], check=True)
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


blkdevice = click.Path(
    exists=True, file_okay=True, dir_okay=False, writable=True, resolve_path=True
)


@click.command()
@click.option(
    "--drive",
    type=blkdevice,
    help="drive to parition and then use (/dev/whatever)",
)
@click.option(
    "--boot",
    type=blkdevice,
    help="The boot partition",
)
@click.option(
    "--root",
    type=blkdevice,
    help="The boot partition",
)
@click.option(
    "--randomize/--no-randomize",
    default=False,
    help="Randomize the root partition before encrypting",
)
@click.option(
    "--swap-size", help="swap size, defaults to 2**n G where 2**n G >= total memory"
)
@click.option(
    "--mount",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help="directory to mount new the the system in",
    required=True,
)
@click.password_option()
@click.confirmation_option(prompt="Are you sure?")
def prepare_drive(
    drive: t.Optional[str],
    boot: t.Optional[str],
    root: t.Optional[str],
    randomize: bool,
    swap_size: t.Optional[str],
    mount: str,
    password: str,
) -> None:
    """
    Prepare a drive for a nixos installation.

    The drive can be specified with either --drive or both --root and --boot.
    --drive expects an entire block device, and will create a new GPT partition table
    on the device. --root and --boot both expect partitions.

    If --randomize is set, then the root partition is randomized.
    """
    dst: t.Union[str, PartitionScheme]
    if drive is not None:
        if boot is not None or root is not None:
            raise click.UsageError(
                "--boot and --root must not be used when --drive is set"
            )
        dst = drive
    elif boot is not None and root is not None:
        dst = PartitionScheme(boot=Path(boot), root=Path(root))
    elif boot is None and root is None:
        raise click.UsageError("[--drive] or [--root --boot] must be set")
    else:
        raise click.UsageError("both --root and --boot are required")

    if isinstance(dst, str):
        partitions = partition_drive(Path(dst))
    elif isinstance(dst, PartitionScheme):
        partitions = dst
    else:
        assert_never(dst)

    configure_drive(partitions, randomize, swap_size, Path(mount), password)
