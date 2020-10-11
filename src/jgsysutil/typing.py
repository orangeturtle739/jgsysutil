import typing as t


def assert_never(x: t.NoReturn) -> t.NoReturn:
    raise AssertionError(f"Invalid value: {x}")
