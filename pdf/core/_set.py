import re
from pathlib import Path
from typing import List, Optional

from pikepdf import OutlineItem, Pdf

from ..log import logger
from .common import require_exists, save_as


def _set(pdf: Pdf, bookmark_txt_path: Path, page_offset: int):
    bookmark_lines = bookmark_txt_path.read_text(encoding='utf-8').strip().split('\n')

    MAX_PAGES = len(pdf.pages)

    bookmarks: List[OutlineItem] = []
    history_indent: List[int] = []

    # decide the level of each bookmark according to the relative indent size in each line
    #   no indent:          level 1
    #     small indent:     level 2
    #       larger indent:  level 3
    #   ...
    def get_parent_bookmark(
        current_indent: int, history_indent: List[int], bookmarks: List[OutlineItem]
    ) -> Optional[OutlineItem]:
        """The parent of A is the nearest bookmark whose indent is smaller than A's"""
        assert len(history_indent) == len(bookmarks)
        if current_indent == 0:
            return
        for i in range(len(history_indent) - 1, -1, -1):
            # len(history_indent) - 1   ===>   0
            if history_indent[i] < current_indent:
                return bookmarks[i]

    with pdf.open_outline() as outline:
        for line in bookmark_lines:
            line2 = re.split(r'\s+', line.strip())
            if len(line2) == 1:
                continue

            indent_size = len(line) - len(line.lstrip())
            parent = get_parent_bookmark(indent_size, history_indent, bookmarks)
            history_indent.append(indent_size)

            title, page = ' '.join(line2[:-1]), int(line2[-1]) - 1
            if page + page_offset >= MAX_PAGES:
                logger.error(
                    f"page index out of range: {page + page_offset} >= {MAX_PAGES}"
                )
                exit()

            new_bookmark = OutlineItem(title, page + page_offset)
            if parent is None:
                outline.root.append(new_bookmark)
            else:
                parent.children.append(new_bookmark)
            bookmarks.append(new_bookmark)

    return pdf


def _remove(pdf_path: Path):
    pdf = Pdf.open(pdf_path)
    with pdf.open_outline() as outline:
        outline.root.clear()

    return pdf_path, pdf


@save_as()
@require_exists(2)
def set(pdf_path: Path, bookmark_txt_path: Path, page_offset: int):
    pdf = Pdf.open(pdf_path)
    return pdf_path, _set(pdf, bookmark_txt_path, page_offset)


@save_as()
@require_exists()
def reset(pdf_path: Path, bookmark_txt_path: Path, page_offset: int):
    _, pdf = _remove(pdf_path)
    return pdf_path, _set(pdf, bookmark_txt_path, page_offset)


@save_as()
@require_exists()
def remove(pdf_path: Path):
    return _remove(pdf_path)
