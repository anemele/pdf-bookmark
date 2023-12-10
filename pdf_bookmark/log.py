import logging as _logging
import sys

_logging.basicConfig(
    format='[%(levelname)s] %(message)s',
    level=_logging.INFO,
    stream=sys.stdout,
)

logger = _logging.getLogger(__package__)
