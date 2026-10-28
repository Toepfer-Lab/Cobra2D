from typing import Iterable, List


class IdAlreadyInUse(Exception):
    """
    Raised if an object cannot be added because its ID is already in use.
    """

    def __init__(
        self,
        id: str,
        message: str = "The ID is already used by another object of the "
        "same type. Please use a different ID.",
    ):
        self.id = (id,)
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message + " Affected ID: " + str(self.id[0])


class InvalidLabel(Exception):
    """
    Raised if a label for a sub_model is not valid.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message or "The label is invalid."


class GraphvizNotInstalled(Warning):
    """
    Warning for cases in which the Graphviz system package is missing.

    The ``graphviz`` Python package only provides the bindings; rendering
    additionally needs the Graphviz executables (``dot``), which are a
    separate, non-pip-installable dependency.
    """

    DEFAULT_MESSAGE = (
        "Rendering a graph requires the Graphviz system package. It is "
        "separate from the 'graphviz' Python package and cannot be "
        "installed via pip. Please refer to the documentation of "
        "graphviz: https://graphviz.readthedocs.io/en/stable/manual.html"
    )

    def __init__(self, message: str = ""):
        self.message = message or self.DEFAULT_MESSAGE
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class PhaseNotFound(Warning):
    """
    Raised if a phase with the requested ID does not exist.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return super().__str__()


class GenesNotLinked(Warning):
    """
    Warning for manually assigned phase models whose gene-reaction rules are
    not automatically synchronized.

    Genes of independently supplied models cannot be assumed to be
    equivalent, so their rules are left untouched. See the gene-rule section
    of the Cobra2D constraints documentation for details.
    """

    DEFAULT_MESSAGE = (
        "Gene-reaction rules of manually assigned phase models are not "
        "automatically synchronized."
    )

    DOCUMENTATION_URL = (
        "https://github.com/Toepfer-Lab/Cobra2D/blob/main/docs/source/"
        "constraints.rst#applying-phase-models-and-synchronizing-gene-rules"
    )

    def __init__(self, phases: Iterable[str] = (), message: str = "") -> None:
        self.phases: List[str] = list(phases)
        self.message = message or self.DEFAULT_MESSAGE

        if self.phases:
            self.message += " Affected phases: {}.".format(
                ", ".join(self.phases)
            )

        self.message += " See " + self.DOCUMENTATION_URL

        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class NameWarning(Warning):
    """
    Warning for cases in which a name might be unavailable.
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return super().__str__()
