import typing as t
from pathlib import Path


def sample_block_device(path: Path, width: int) -> t.Tuple[int, int]:
    with open(path, "rb") as x:
        start = sum(x.read(width))
        x.seek(-width, 2)
        end = sum(x.read(width))
        return start, end


def is_zero(path: Path) -> bool:
    return sample_block_device(path, 1024) == (0, 0)


def is_random(path: Path) -> bool:
    # The probability that 1024 random bytes are 0 is 2**(-13)
    return 0 not in sample_block_device(path, 1024)
