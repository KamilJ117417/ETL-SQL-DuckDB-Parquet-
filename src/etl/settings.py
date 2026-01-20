"""Settings, enums, and configuration."""

from enum import Enum
from typing import Literal

# ETL Modes
class ETLMode(str, Enum):
    STRICT = "strict"
    QUARANTINE = "quarantine"


# Library layouts
class LibraryLayout(str, Enum):
    SINGLE = "SINGLE"
    PAIRED = "PAIRED"


# Platform types
class Platform(str, Enum):
    ILLUMINA = "ILLUMINA"
    NANOPORE = "NANOPORE"
    PACBIO = "PACBIO"
    ION_TORRENT = "ION_TORRENT"


# Log levels
class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# Valid ranges for QC metrics
VALID_RANGES = {
    "q30_rate": (0.0, 1.0),
    "gc_percent": (0.0, 100.0),
    "duplication_rate": (0.0, 1.0),
}

# Valid enums for categorical fields
VALID_ENUMS = {
    "library_layout": {e.value for e in LibraryLayout},
    "platform": {e.value for e in Platform},
}
