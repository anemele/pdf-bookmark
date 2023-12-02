import sys

if sys.version_info < (3, 7):
    raise NotImplementedError("pikepdf requires Python 3.7+")

from .cli import cli

cli(args=sys.argv[2:], prog_name=sys.argv[1])
