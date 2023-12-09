from itertools import chain
from pathlib import Path

from pikepdf import Array, Name, OutlineItem, Page, Pdf, String

from ..log import logger
from .common import new_path_with_timestamp, require_exists


def parse_outline_tree(
    outlines: OutlineItem | list[OutlineItem], level: int = 0, names=None
) -> list[tuple[int, int, str]]:
    """Return List[Tuple[level(int), page(int), title(str)]]"""

    if isinstance(outlines, (list, tuple)):
        return list(
            chain.from_iterable(
                parse_outline_tree(heading, level=level, names=names)
                for heading in outlines
            )
        )
    else:
        tmp = [(level, get_destiny_page_number(outlines, names) + 1, outlines.title)]
        return list(
            chain(
                tmp,
                chain.from_iterable(
                    (
                        parse_outline_tree(subheading, level=level + 1, names=names)
                        for subheading in outlines.children
                    ),
                ),
            )
        )


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
            # note: is this tpye hint error? .pyi says it is a method `()->int`, but a literal `int`
            return Page(resolved).index  # type: ignore
        return 0

    if outline.destination is None:
        return find_destiny(outline.action.D, names)

    if isinstance(outline.destination, Array):
        # 12.3.2.2 Explicit destination
        # [raw_page, /PageLocation.SomeThing, integer parameters for viewport]
        raw_page = outline.destination[0]
        try:
            # note: is this tpye hint error? .pyi says it is a method `()->int`, but a literal `int`
            return Page(raw_page).index  # type: ignore
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


@require_exists()
def get(pdf_path: Path, bookmark_txt_path: Path | None):
    # https://github.com/pikepdf/pikepdf/issues/149#issuecomment-860073511
    def has_nested_key(obj, keys):
        to_check = obj
        for key in keys:
            if key not in to_check.keys():
                return False
            to_check = to_check[key]
        return True

    def get_names(pdf: Pdf) -> list:
        # 此处可能出错（可能由于PDF被其它程序编辑过）
        if not hasattr(pdf, 'Root'):
            return []
        if not has_nested_key(pdf.Root, ['/Names', '/Dests']):
            return []
        obj = pdf.Root.Names.Dests
        ks = obj.keys()
        if '/Names' in ks:
            return obj.Names  # type: ignore
        elif '/Kids' in ks:
            return list(chain.from_iterable(map(get_names, obj.Kids)))  # type: ignore
        else:
            raise ValueError

    pdf = Pdf.open(pdf_path)
    names = get_names(pdf)

    with pdf.open_outline() as outline:
        outlines = parse_outline_tree(outline.root, names=names)
    if len(outlines) == 0:
        logger.error(f'no bookmark is found in {pdf_path}')
        exit()

    # List[Tuple[level(int), page(int), title(str)]]
    max_length = max(len(title) + 2 * level for level, _, title in outlines) + 1

    def fmt(item):
        level, page, title = item
        level_space = '  ' * level
        title_page_space = ' ' * (max_length - level * 2 - len(title))
        return f'{level_space}{title}{title_page_space}{page}'

    if bookmark_txt_path is None:
        bookmark_txt_path = new_path_with_timestamp(pdf_path, '.txt')
    if bookmark_txt_path.exists():
        logger.warning(f'overwrite {bookmark_txt_path}')

    bookmark_txt_path.write_text('\n'.join(map(fmt, outlines)), encoding='utf-8')

    logger.info(f'save as\n{bookmark_txt_path}')
