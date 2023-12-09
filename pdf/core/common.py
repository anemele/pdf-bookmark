from datetime import datetime
from functools import wraps
from pathlib import Path

from pikepdf import Pdf

from ..log import logger


def require_exists(n: int = 1):
    """require the first n arguments are pathlib.Path and exist"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kw):
            for i in range(n):
                path = args[i]
                if not path.exists():
                    logger.error(f'no such file: {path}')
                    exit()
            return func(*args, **kw)

        return wrapper

    return decorator


def new_path_with_timestamp(path: Path, ext: str | None = None):
    now = f'-{datetime.now():%y%m%d%H%M%S}'

    return path.with_name(path.stem + now + (ext or path.suffix))


def save_as(ext: str | None = None):
    """save the output file automatically
    `ext` requires starting with dot `.`, such as `.txt`
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ret = func(*args, **kwargs)

            if ret is None:
                return

            path: Path
            sth: Pdf | str
            path, sth = ret

            out_path = new_path_with_timestamp(path, ext)

            if isinstance(sth, Pdf):
                sth.save(out_path)
            elif isinstance(sth, str):
                out_path.write_text(sth, encoding='utf-8')

            logger.info(f'save as\n{out_path}')

        return wrapper

    return decorator
