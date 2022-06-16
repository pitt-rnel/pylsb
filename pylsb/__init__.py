import os
from .internal_types import LSB, AddMessage, AddSignal
from .definition_parser import parse_file, parse_files
from .client import *

# Optionally automatically parse user defined msg defs from env var.
include_files = os.getenv("LSB_DEFS")
if include_files:
    for filename in include_files.split(sep=";"):
        parse_file(filename)
