class PinBarError(Exception):
    """
    General error type of PinBar.
    All PinBar related errors should be derived from this error class.
    """
    pass


class GPIOPinBarError(PinBarError):
    """
    General error type of GPIOPinBar.
    Superclass of several error types like PinTypeError and ModeIsOffError.
    More precise details must be taken from the individual error message.
    """
    pass


class PinTypeError(PinBarError):
    """
    This error is raised when an attempt is made to apply an operation to a pin that cannot be applied to the pin type.
    E.g. when an attempt is made to change the status of a ground pin.
    """
    pass


class ModeIsOffError(GPIOPinBarError):
    """
    This error is raised when an attempt is made to apply an operation to a GPIO Pin that cannot be applied to the pin
    because the mode of the pin is GPIOPinMode.OFF
    E.g. when attempting to set the state of a gpio pin which is off
    """
    pass
