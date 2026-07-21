class IdAlreadyInUse(Exception):
    """
    Exception used if an ID is already in use, preventing the addition of
    another object.
    """

    def __init__(
        self,
        id: str,
        message: str = "The ID used has already been used for another "
        "object of the same type. Please use a different ID.",
    ):
        self.id = (id,)
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message + " Concerning ID is: " + str(self.id)


class InvalidLabel(Exception):
    """
    Used if a label for a sub-model is not valid.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message or "A used label is invalid."


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
        "installed via pip, please refer to the documentation of "
        "graphviz: https://graphviz.readthedocs.io/en/stable/manual.html"
    )

    def __init__(self, message: str = ""):
        self.message = message or self.DEFAULT_MESSAGE
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class PhaseNotFound(Warning):
    """
    Raises a Warning in case that a phase is not available
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return super().__str__()


class NameWarning(Warning):
    """
    Warning for cases, in which a name might not be available
    """

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return super().__str__()
