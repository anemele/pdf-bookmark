from pathlib import Path
from typing import Optional

import click

from .core import get as _get
from .core import remove as _rm
from .core import reset as _rst
from .core import set as _set
from .log import logger


class OrderedGroup(click.Group):
    def list_commands(self, _):
        return self.commands.keys()


@click.group(cls=OrderedGroup)
def cli():
    """PDF bookmark util"""


@cli.command(name='get')
@click.argument('pdf', type=Path)
@click.argument('bookmark', type=Path, required=False)
def get_bookmark(pdf: Path, bookmark: Optional[Path]):
    """get bookmark from a PDF file"""
    logger.debug(f'{pdf=}')
    logger.debug(f'{bookmark=}')

    _get(pdf, bookmark)


@cli.command(name='set')
@click.argument('pdf', type=Path)
@click.argument('bookmark', type=Path)
@click.argument('offset', type=int, default=0)
def set_bookmark(pdf: Path, bookmark: Path, offset: int):
    """set bookmark to a PDF file from a TEXT file"""
    logger.debug(f'{pdf=}')
    logger.debug(f'{bookmark=}')
    logger.debug(f'{offset=}')

    _set(pdf, bookmark, offset)


@cli.command(name='rst')
@click.argument('pdf', type=Path)
@click.argument('bookmark', type=Path)
@click.argument('offset', type=int, default=0)
def reset_bookmark(pdf: Path, bookmark: Path, offset: int):
    """reset bookmark to a PDF file from a TEXT file"""
    logger.debug(f'{pdf=}')
    logger.debug(f'{bookmark=}')
    logger.debug(f'{offset=}')

    _rst(pdf, bookmark, offset)


@cli.command(name='rm')
@click.argument('pdf', type=Path)
def remove(pdf: Path):
    """remove bookmark from a PDF file"""
    logger.debug(f'{pdf=}')

    _rm(pdf)
