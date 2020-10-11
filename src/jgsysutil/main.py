import click

from jgsysutil.prepare_drive import prepare_drive
from jgsysutil.randomize_drive import randomize_drive


@click.group()
@click.version_option()
def main() -> None:
    """
    Assorted system administration utility scripts
    """
    pass


main.add_command(prepare_drive)
main.add_command(randomize_drive)
