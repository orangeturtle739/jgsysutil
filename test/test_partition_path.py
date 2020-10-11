from pathlib import Path

from jgsysutil.prepare_drive import partition_path


def test_partition_path() -> None:
    def helper(name: str, num: int, expected: str) -> None:
        assert partition_path(Path("/dev") / name, num) == Path(f"/dev/{expected}")

    helper("sda", 2, "sda2")
    helper("loop0", 2, "loop0p2")
    helper("nvme0", 2, "nvme0p2")
