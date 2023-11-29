# 如何给PDF文件加目录？ - Emrys的回答 - 知乎
# https://www.zhihu.com/question/344805337/answer/1116258929
from itertools import chain
import sys

if sys.version_info < (3, 7):
    raise NotImplementedError("pikepdf requires Python 3.7+")

import re
from pathlib import Path
from typing import List, Optional, Union, Tuple

from pikepdf import Array, Name, OutlineItem, Page, Pdf, String


#################
# Set bookmarks #
#################
def _get_parent_bookmark(
    current_indent: int, history_indent: List[int], bookmarks: List[OutlineItem]
) -> Optional[OutlineItem]:
    '''The parent of A is the nearest bookmark whose indent is smaller than A's'''
    assert len(history_indent) == len(bookmarks)
    if current_indent == 0:
        return None
    for i in range(len(history_indent) - 1, -1, -1):
        # len(history_indent) - 1   ===>   0
        if history_indent[i] < current_indent:
            return bookmarks[i]
    return None


def set_bookmark(pdf_path: Path, bookmark_txt_path: Path, page_offset: int):
    if not pdf_path.exists():
        return f"Error: No such file: {pdf_path}"

    if not bookmark_txt_path.exists():
        return f"Error: No such file: {bookmark_txt_path}"

    bookmark_lines = bookmark_txt_path.read_text(encoding='utf-8').strip().splitlines()

    pdf = Pdf.open(pdf_path)
    maxPages = len(pdf.pages)

    bookmarks: List[OutlineItem] = []
    history_indent: List[int] = []
    # decide the level of each bookmark according to the relative indent size in each line
    #   no indent:          level 1
    #     small indent:     level 2
    #       larger indent:  level 3
    #   ...
    with pdf.open_outline() as outline:
        for line in bookmark_lines:
            line2 = re.split(r'\s+', line.strip())
            if len(line2) == 1:
                continue

            indent_size = len(line) - len(line.lstrip())
            parent = _get_parent_bookmark(indent_size, history_indent, bookmarks)
            history_indent.append(indent_size)

            title, page = ' '.join(line2[:-1]), int(line2[-1]) - 1
            if page + page_offset >= maxPages:
                return "Error: page index out of range: %d >= %d" % (
                    page + page_offset,
                    maxPages,
                )

            new_bookmark = OutlineItem(title, page + page_offset)
            if parent is None:
                outline.root.append(new_bookmark)
            else:
                parent.children.append(new_bookmark)
            bookmarks.append(new_bookmark)

    out_path = Path(pdf_path)
    out_path = out_path.with_name(out_path.stem + "-new.pdf")
    pdf.save(out_path)

    return f"The bookmarks have been added to {out_path}"


#################
# Get bookmarks #
#################
def _get_destination_page_number(outline: OutlineItem, names) -> int:
    def find_dest(ref, names):
        resolved = None
        if isinstance(ref, Array):
            resolved = ref[0]
        else:
            for n in range(0, len(names) - 1, 2):
                if names[n] == ref:
                    if names[n + 1]._type_name == 'array':
                        named_page = names[n + 1][0]
                    elif names[n + 1]._type_name == 'dictionary':
                        named_page = names[n + 1].D[0]
                    else:
                        raise TypeError("Unknown type: %s" % type(names[n + 1]))
                    resolved = named_page
                    break
        if resolved is not None:
            return Page(resolved).index()
        return 0  # This is an append but untested return

    if outline.destination is None:
        return find_dest(outline.action.D, names)

    if isinstance(outline.destination, Array):
        # 12.3.2.2 Explicit destination
        # [raw_page, /PageLocation.SomeThing, integer parameters for viewport]
        raw_page = outline.destination[0]
        try:
            page = Page(raw_page)
            return page.index()
        except:
            return find_dest(outline.destination, names)
    elif isinstance(outline.destination, String):
        # 12.3.2.2 Named destination, byte string reference to Names
        # dest = f'<Named Destination in document .Root.Names dictionary: {outline.destination}>'
        assert names is not None
        return find_dest(outline.destination, names)
    elif isinstance(outline.destination, Name):
        # 12.3.2.2 Named desintation, name object (PDF 1.1)
        # dest = f'<Named Destination in document .Root.Dests dictionary: {outline.destination}>'
        return find_dest(outline.destination, names)
    elif isinstance(outline.destination, int):
        # Page number
        return outline.destination

    return 0  # This is an append but untested return


def _parse_outline_tree(
    outlines: Union[OutlineItem, List[OutlineItem]], level: int = 0, names=None
) -> List[Tuple[int, int, str]]:
    """Return List[Tuple[level(int), page(int), title(str)]]"""

    if isinstance(outlines, (list, tuple)):
        # contains sub-headings
        return list(
            chain.from_iterable(
                _parse_outline_tree(heading, level=level, names=names)
                for heading in outlines
            )
        )
    else:
        tmp = [
            (level, _get_destination_page_number(outlines, names) + 1, outlines.title)
        ]

        # contains sub-headings
        return list(
            chain(
                tmp,
                chain.from_iterable(
                    _parse_outline_tree(subheading, level=level + 1, names=names)
                    for subheading in outlines.children
                ),
            )
        )


def get_bookmark(pdf_path: Path, bookmark_txt_path: Path) -> str:
    # https://github.com/pikepdf/pikepdf/issues/149#issuecomment-860073511
    def has_nested_key(obj, keys):
        ok = True
        to_check = obj
        for key in keys:
            if key in to_check.keys():
                to_check = to_check[key]
            else:
                ok = False
                break
        return ok

    def get_names(pdf):
        if has_nested_key(pdf.Root, ['/Names', '/Dests']):
            obj = pdf.Root.Names.Dests
            names = []
            ks = obj.keys()
            if '/Names' in ks:
                names.extend(obj.Names)
            elif '/Kids' in ks:
                for k in obj.Kids:
                    names.extend(get_names(k))
            else:
                assert False
            return names
        else:
            return None

    if not pdf_path.exists():
        return f"Error: No such file: {pdf_path}"
    if bookmark_txt_path.exists():
        print(f"Warning: Overwritting {bookmark_txt_path}")

    pdf = Pdf.open(pdf_path)
    names = get_names(pdf)
    with pdf.open_outline() as outline:
        outlines = _parse_outline_tree(outline.root, names=names)
    if len(outlines) == 0:
        return "No bookmark is found in %s" % pdf_path
    # List[Tuple[level(int), page(int), title(str)]]
    max_length = max(len(item[-1]) + 2 * item[0] for item in outlines) + 1
    # print(outlines)
    with open(bookmark_txt_path, 'w') as f:
        for level, page, title in outlines:
            level_space = '  ' * level
            title_page_space = ' ' * (max_length - level * 2 - len(title))
            f.write("{}{}{}{}\n".format(level_space, title, title_page_space, page))
    return f"The bookmarks have been exported to {bookmark_txt_path}"


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 3:
        print("Usage: %s [pdf] [bookmark_txt] [page_offset]" % Path(args[0]).name)
    elif len(args) == 3:
        print(get_bookmark(Path(args[1]), Path(args[2])))
    else:
        print(set_bookmark(Path(args[1]), Path(args[2]), int(args[3])))
