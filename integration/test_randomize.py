import subprocess

import pytest
from block_util import is_random, is_zero
from loop_device import loop_device


def test_basic() -> None:
    with loop_device(1024) as dev:
        assert is_zero(dev)
        subprocess.run(["jgsysutil", "randomize-drive", "--yes", dev], check=True)
        assert is_random(dev)


def test_confirm_works() -> None:
    with loop_device(1024) as dev:
        with pytest.raises(Exception):
            subprocess.run(
                ["jgsysutil", "randomize-drive", dev], check=True, input="", text=True
            )
        assert is_zero(dev)

        subprocess.run(
            ["jgsysutil", "randomize-drive", dev], check=True, input="yes", text=True
        )
        assert is_random(dev)
