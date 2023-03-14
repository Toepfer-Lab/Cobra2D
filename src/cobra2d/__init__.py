import importlib.metadata

from model_duplication.constraints.constraints import Constraints
from model_duplication.constraints.phase import Phase, Phases
from model_duplication.constraints.linker import Linker, Linkage
from model_duplication.constraints.transfer import Transfer, Transfers

__version__ = importlib.metadata.version('Cobra2D')

__all__ = [
    "Constraints",
    "Phase",
    "Phases",
    "Linker",
    "Linkage",
    "Transfer",
    "Transfers",
]
