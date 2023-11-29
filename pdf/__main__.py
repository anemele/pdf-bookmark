#!/usr/bin/env python3.8
# -*- encoding: utf-8 -*-

"""Set and get PDF bookmark."""
# raise NotImplementedError('There are some errors, CANNOT use.')

import sys
from typing import Optional

if sys.version_info < (3, 7):
    raise NotImplementedError("pikepdf requires Python 3.7+")
from pathlib import Path

import fire

from .get import get as _get
from .set import set as _set


def get_bookmark(pdf_path: str, bookmark_txt_path: Optional[str] = None) -> str:
    pp = Path(pdf_path)
    if bookmark_txt_path is None:
        bp = pp.with_suffix('.txt')
    else:
        bp = Path(bookmark_txt_path)
    return _get(pp, bp)


def set_bookmark(pdf_path: str, bookmark_txt_path: str, page_offset: int) -> str:
    return _set(Path(pdf_path), Path(bookmark_txt_path), page_offset)


if __name__ == '__main__':
    fire.Fire(dict(set=set_bookmark, get=get_bookmark), name=__package__)
