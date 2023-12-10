import sys

if sys.version_info < (3, 7):
    raise NotImplementedError("pikepdf requires Python 3.7+")

from .cli import cli

cli(args=sys.argv[2:], prog_name=__package__ if len(sys.argv) == 1 else sys.argv[1])
