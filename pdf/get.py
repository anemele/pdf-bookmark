from itertools import chain
from pathlib import Path
from typing import List, Union

from pikepdf import Array, Name, OutlineItem, Page, Pdf, String


def parse_outline_tree(
    outlines: Union[OutlineItem, List[OutlineItem]], level: int = 0, names=None
) -> list:
    """Return List[Tuple[level(int), page(int), title(str)]]"""

    if isinstance(outlines, (list, tuple)):
        return list(
            chain(
                parse_outline_tree(heading, level=level, names=names)
                for heading in outlines
            )
        )
    else:
        tmp = (level, get_destiny_page_number(outlines, names) + 1, outlines.title)
        return [
            tmp,
            list(
                chain(
                    (
                        parse_outline_tree(subheading, level=level + 1, names=names)
                        for subheading in outlines.children
                    ),
                )
            ),
        ]


def get_destiny_page_number(outline: OutlineItem, names) -> int:
    def find_destiny(ref, names) -> int:
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
        return 0

    if outline.destination is None:
        return find_destiny(outline.action.D, names)

    if isinstance(outline.destination, Array):
        # 12.3.2.2 Explicit destination
        # [raw_page, /PageLocation.SomeThing, integer parameters for viewport]
        raw_page = outline.destination[0]
        try:
            return Page(raw_page).index()
        except:
            return find_destiny(outline.destination, names)
    elif isinstance(outline.destination, String):
        # 12.3.2.2 Named destination, byte string reference to Names
        # destiny = f'<Named Destination in document .Root.Names dictionary: {outline.destination}>'
        assert names is not None
        return find_destiny(outline.destination, names)
    elif isinstance(outline.destination, Name):
        # 12.3.2.2 Named destination, name object (PDF 1.1)
        # destiny = f'<Named Destination in document .Root.Dests dictionary: {outline.destination}>'
        return find_destiny(outline.destination, names)
    elif isinstance(outline.destination, int):
        # Page number
        return outline.destination

    return outline.destination


def get(pdf_path: Path, bookmark_txt_path: Path) -> str:
    # https://github.com/pikepdf/pikepdf/issues/149#issuecomment-860073511
    def has_nested_key(obj, keys):
        to_check = obj
        for key in keys:
            if key not in to_check.keys():
                return False
            to_check = to_check[key]
        return True

    def get_names(pdf: Pdf) -> List:
        if not has_nested_key(pdf.Root, ['/Names', '/Dests']):
            return []
        obj = pdf.Root.Names.Dests
        names = []
        ks = obj.keys()
        if '/Names' in ks:
            names.extend(obj.Names)  # type: ignore
        elif '/Kids' in ks:
            for k in obj.Kids:  # type: ignore
                names.extend(get_names(k))
        else:
            raise ValueError
        return names

    if not pdf_path.exists():
        return f'[Error] No such file: {pdf_path}'

    if bookmark_txt_path.exists():
        print(f'[Warning] Overwriting {bookmark_txt_path}')

    pdf = Pdf.open(pdf_path)
    names = get_names(pdf)
    with pdf.open_outline() as outline:
        outlines = parse_outline_tree(outline.root, names=names)
    if len(outlines) == 0:
        return f'[Error] No bookmark is found in {pdf_path}'

    # List[Tuple[level(int), page(int), title(str)]]
    max_length = max(len(item[-1]) + 2 * item[0] for item in outlines) + 1
    # print(outlines)
    with open(bookmark_txt_path, 'w') as f:
        for level, page, title in outlines:
            level_space = '  ' * level
            title_page_space = ' ' * (max_length - level * 2 - len(title))
            f.write(f'{level_space}{title}{title_page_space}{page}\n')

    return f'[Info] The bookmarks have been exported to\n{bookmark_txt_path}'
