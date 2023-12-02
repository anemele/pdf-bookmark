import sys

if sys.version_info < (3, 7):
    raise NotImplementedError("pikepdf requires Python 3.7+")

from .cli import cli

if __name__ == '__main__':
    cli(prog_name=__package__)
