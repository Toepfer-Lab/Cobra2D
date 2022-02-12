from sys import path
from pathlib import Path

path.append(str(Path(__file__).parent))

from duplication import _main_placeholder, __version__

__all__ = ["_main_placeholder"]
__version__
