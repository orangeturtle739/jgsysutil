import abc
import argparse
import typing as t


class Subcommand(abc.ABC):
    @abc.abstractmethod
    def name(self) -> str:
        ...

    @abc.abstractmethod
    def help(self) -> str:
        ...

    @abc.abstractmethod
    def configure(self, parser: argparse.ArgumentParser) -> None:
        ...

    @abc.abstractmethod
    def run(self, args: t.Any) -> int:
        ...


def register_subcommands(
    parser: argparse.ArgumentParser,
    *,
    title: str,
    description: str = "",
    help: str = "",
    subcommands: t.List[Subcommand]
) -> None:
    subparsers = parser.add_subparsers(
        dest=title, title=title, description=description, help=help, required=True,
    )
    for subcommand in subcommands:
        subparser = subparsers.add_parser(subcommand.name(), help=subcommand.help())
        subcommand.configure(subparser)
        subparser.set_defaults(**{title: subcommand.run})


def invoke_subcommand(title: str, args: t.Any) -> int:
    return args.__dict__[title](args)
