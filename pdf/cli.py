from pathlib import Path
from typing import Optional

import click

from .get import get as _get
from .log import logger
from .set import set as _set


@click.group()
def cli():
    """set/get PDF bookmark"""


@cli.command()
@click.argument('pdf', type=Path)
@click.argument('bookmark', type=Path, required=False)
def get(pdf: Path, bookmark: Optional[Path]):
    logger.debug(f'{pdf=}')
    logger.debug(f'{bookmark=}')

    if bookmark is None:
        bookmark = pdf.with_suffix('.txt')

    _get(pdf, bookmark)


@cli.command()
@click.argument('pdf', type=Path)
@click.argument('bookmark', type=Path)
@click.argument('offset', type=int)
def set(pdf: Path, bookmark: Path, offset: int):
    logger.debug(f'{pdf=}')
    logger.debug(f'{bookmark=}')
    logger.debug(f'{offset=}')

    _set(pdf, bookmark, offset)
