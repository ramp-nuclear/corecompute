import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import warnings


@dataclass
class SurfaceTracksResult:
    """A container that contains track information on the surface.

    Currently, this is based on a file with data.
    This is legacy code that may not be in use, and kept here until we can be
    sure we did not break a dependency.

    """
    path: Path
    timestamp: datetime
    filehash: str

    def __post_init__(self):
        warnings.warn("SurfaceTracksResult is unmaintained and deprecated. If"
                      "you use this, please contact the development team so we"
                      "can write something better to migrate this over to.",
                      DeprecationWarning)

    def check_valid(self):
        return self.compute_filehash(self.path) == self.filehash

    @classmethod
    def compute_filehash(cls,path:Path):
        filehash = hashlib.sha256()
        with open(path, 'rb') as file:
            for block in iter(lambda: file.read(128), b''):
                filehash.update(block)
        return filehash.hexdigest()

