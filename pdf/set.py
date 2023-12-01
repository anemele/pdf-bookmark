import re
from pathlib import Path
from typing import List, Optional

from pikepdf import OutlineItem, Pdf

from .log import logger


def set(pdf_path: Path, bookmark_txt_path: Path, page_offset: int):
    if not pdf_path.exists():
        logger.error(f'no such file: {pdf_path}')
        exit()

    if not bookmark_txt_path.exists():
        logger.error(f'no such file: {bookmark_txt_path}')
        exit()

    bookmark_lines = bookmark_txt_path.read_text(encoding='utf-8').strip().split('\n')

    pdf = Pdf.open(pdf_path)
    max_pages = len(pdf.pages)

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
            if page + page_offset >= max_pages:
                logger.error(
                    f"page index out of range: {page + page_offset} >= {max_pages}"
                )
                exit()

            new_bookmark = OutlineItem(title, page + page_offset)
            if parent is None:
                outline.root.append(new_bookmark)
            else:
                parent.children.append(new_bookmark)
            bookmarks.append(new_bookmark)

    out_path = Path(pdf_path)
    out_path = out_path.with_name(out_path.stem + "-new.pdf")
    pdf.save(out_path)

    logger.info(f'the bookmarks have been imported to\n{out_path}')
