import json
import os
import subprocess
import tempfile
import typing as t
from contextlib import contextmanager
from pathlib import Path

import pytest

from jgsysutil.commands import (
    cryptsetup,
    gdisk,
    lsblk,
    lvdisplay,
    swapoff,
    umount,
    vgchange,
)
from loop_device import loop_device

LsblkOut = t.List[t.Dict[str, t.Any]]


def lsblk_output_find(
    blockdevices_json: LsblkOut, fname: str, target: str
) -> t.Optional[str]:
    for dev in blockdevices_json:
        if dev.get(fname, None) == target:
            return dev["name"]
        x = lsblk_output_find(dev.get("children", []), fname, target)
        if x is not None:
            return x
    return None


def find_swap(blockdevices_json: LsblkOut) -> t.Optional[str]:
    return lsblk_output_find(blockdevices_json, "mountpoint", "[SWAP]")


def find_crypt(blockdevices_json: LsblkOut) -> t.Optional[str]:
    return lsblk_output_find(blockdevices_json, "type", "crypt")


def find_vg(swap_dev_name: str) -> str:
    return subprocess.run(
        [
            lvdisplay,
            f"/dev/mapper/{swap_dev_name}",
            "--columns",
            "--options",
            "vg_name",
            "--noheadings",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run_lsblk(dev: Path) -> LsblkOut:
    return json.loads(
        subprocess.run(
            [lsblk, "--json", dev], check=True, capture_output=True, text=True
        ).stdout
    )["blockdevices"]


def unmount_if_mounted(path: Path) -> None:
    if os.path.ismount(str(path)):
        subprocess.run([umount, path], check=True)


@contextmanager
def handle_resources(mountdir: Path, root_dev: Path) -> t.Iterator[None]:
    try:
        yield None
    finally:
        blockdevices = run_lsblk(root_dev)
        unmount_if_mounted(mountdir / "boot")
        unmount_if_mounted(mountdir)

        swap_dev = find_swap(blockdevices)
        if swap_dev is not None:
            subprocess.run([swapoff, f"/dev/mapper/{swap_dev}"], check=True)
            vg = find_vg(swap_dev)
            subprocess.run([vgchange, "-a", "n", vg], check=True)

        crypt_dev = find_crypt(blockdevices)
        if crypt_dev is not None:
            subprocess.run([cryptsetup, "luksClose", crypt_dev], check=True)


def make_flag(name: str, choice: bool) -> str:
    if choice:
        return f"--{name}"
    else:
        return f"--no-{name}"


def check_partitions(
    boot_info: t.Dict[str, t.Any],
    root_info: t.Dict[str, t.Any],
    mountdir: Path,
    crypt_size: str,
    root_size: str,
    swap_size: str,
) -> None:
    assert boot_info["size"] == "512M"
    assert boot_info["mountpoint"] == str(mountdir / "boot")
    assert root_info["size"] == crypt_size
    assert len(root_info["children"]) == 1
    crypt = root_info["children"][0]
    assert crypt["size"] == crypt_size
    assert crypt["type"] == "crypt"
    cc = crypt["children"]
    assert len(cc) == 2
    if cc[0]["name"].endswith("_swap"):
        swap, root = cc
    else:
        root, swap = cc
    assert swap["name"].endswith("_swap")
    assert root["name"].endswith("_root")
    assert swap["size"] == swap_size
    assert swap["type"] == "lvm"
    assert swap["mountpoint"] == "[SWAP]"
    assert root["size"] == root_size
    assert root["type"] == "lvm"
    assert root["mountpoint"] == str(mountdir)


@pytest.mark.parametrize("randomize", [True, False])
def test_basic(randomize: bool) -> None:
    with tempfile.TemporaryDirectory() as mountdir:
        with loop_device(4096) as dev:
            boot_partition = Path(f"{dev}p1")
            root_partition = Path(f"{dev}p2")

            with handle_resources(Path(mountdir), root_partition):
                subprocess.run(
                    [
                        "jgsysutil",
                        "prepare-drive",
                        "--drive",
                        dev,
                        make_flag("randomize", randomize),
                        "--mount",
                        mountdir,
                        "--yes",
                        "--password",
                        "test",
                    ],
                    check=True,
                )
                blockdevices = run_lsblk(dev)

                assert len(blockdevices) == 1
                blockroot = blockdevices[0]
                assert blockroot["name"] == dev.name
                assert blockroot["size"] == "4G"
                partitions = {
                    partition["name"]: partition for partition in blockroot["children"]
                }
                p1 = partitions[boot_partition.name]
                p2 = partitions[root_partition.name]
                assert len(partitions) == 2
                check_partitions(p1, p2, Path(mountdir), "3.5G", "2.5G", "1G")


@pytest.mark.parametrize("randomize", [True, False])
def test_explicit_partitions(randomize: bool) -> None:
    with tempfile.TemporaryDirectory() as mountdir:
        with loop_device(4096) as dev:
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
                "+512M",  # offset to end position
                "8309",  # Linux LUKS
                "n",  # new partition
                "",  # enter, default partition number 3
                "",  # enter, default start position
                "",  # enter, default end position (rest of the drive)
                "8309",  # Linux LUKS
                "w",  # write partition table and exit
                "Y",  # confirm
                "",  # final trailing enter
            ]
            subprocess.run(
                [gdisk, dev], input="\n".join(gdisk_commands), text=True, check=True
            )

            boot_partition = Path(f"{dev}p1")
            root_partition = Path(f"{dev}p3")

            with handle_resources(Path(mountdir), root_partition):
                subprocess.run(
                    [
                        "jgsysutil",
                        "prepare-drive",
                        "--boot",
                        boot_partition,
                        "--root",
                        root_partition,
                        make_flag("randomize", randomize),
                        "--mount",
                        mountdir,
                        "--yes",
                        "--password",
                        "test",
                    ],
                    check=True,
                )
                boot_info = run_lsblk(boot_partition)
                root_info = run_lsblk(root_partition)
                assert len(boot_info) == 1
                assert len(root_info) == 1
                check_partitions(
                    boot_info[0], root_info[0], Path(mountdir), "3G", "2G", "1G",
                )


def test_required_arguments() -> None:
    with tempfile.TemporaryDirectory() as mountdir:
        with loop_device(4096) as dev:
            with pytest.raises(Exception):
                subprocess.run(
                    [
                        "jgsysutil",
                        "prepare-drive",
                        "--drive",
                        dev,
                        "--boot",
                        dev,
                        "--root",
                        dev,
                        "--mount",
                        mountdir,
                        "--password",
                        "test",
                        "--yes",
                    ],
                    check=True,
                )
            with pytest.raises(Exception):
                subprocess.run(
                    [
                        "jgsysutil",
                        "prepare-drive",
                        "--drive",
                        dev,
                        "--root",
                        dev,
                        "--mount",
                        mountdir,
                        "--password",
                        "test",
                        "--yes",
                    ],
                    check=True,
                )
            with pytest.raises(Exception):
                subprocess.run(
                    [
                        "jgsysutil",
                        "prepare-drive",
                        "--drive",
                        dev,
                        "--boot",
                        dev,
                        "--mount",
                        mountdir,
                        "--password",
                        "test",
                        "--yes",
                    ],
                    check=True,
                )
            with pytest.raises(Exception):
                subprocess.run(
                    [
                        "jgsysutil",
                        "prepare-drive",
                        "--boot",
                        dev,
                        "--mount",
                        mountdir,
                        "--password",
                        "test",
                        "--yes",
                    ],
                    check=True,
                )
            with pytest.raises(Exception):
                subprocess.run(
                    [
                        "jgsysutil",
                        "prepare-drive",
                        "--root",
                        dev,
                        "--mount",
                        mountdir,
                        "--password",
                        "test",
                        "--yes",
                    ],
                    check=True,
                )


def test_prompt() -> None:
    with tempfile.TemporaryDirectory() as mountdir:
        with loop_device(4096) as dev:
            with handle_resources(Path(mountdir), Path(f"{dev}p2")):
                with pytest.raises(Exception):
                    subprocess.run(
                        [
                            "jgsysutil",
                            "prepare-drive",
                            "--drive",
                            dev,
                            "--mount",
                            mountdir,
                            "--password",
                            "test",
                        ],
                        check=True,
                        input="",
                        text=True,
                    )
                subprocess.run(
                    [
                        "jgsysutil",
                        "prepare-drive",
                        "--drive",
                        dev,
                        "--mount",
                        mountdir,
                        "--password",
                        "test",
                    ],
                    check=True,
                    input="Y",
                    text=True,
                )
