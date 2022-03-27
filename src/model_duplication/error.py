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
