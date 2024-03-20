from enum import Enum
from typing import List, Optional

from gpiowrapper.base import GPIOPinBar, GPIOPinBarEmulator
from gpiowrapper.raspi import Raspi40PinBarEmulator
from gpiowrapper.raspi.rpi_gpio_library import RPiGPIOPinBar, Raspi40PinBarRPi


class LibraryType(Enum):
    """ An enumeration of libraries of which implementations already exist. """

    Emulator = 'Emulator'
    """ An Emulator. No specific library is used. """
    RPi_GPIO = 'RPi.GPIO'
    """ The RPi.GPIO library for the raspberry pi boards. https://sourceforge.net/p/raspberry-gpio-python/wiki/Home/ """


class BoardType(Enum):
    """ An enumeration of board types of which implementations already exist. """

    Raspi_40_pin_header = 'Raspi_40_pin_header'
    """ A raspberry pi with a 40 pin header """


class GPIOPinBarFactory:
    """ Factory that provides a factory method to create GPIOPinBar objects. """

    @classmethod
    def new_pin_bar_instance(
            cls,
            library: LibraryType,
            board: BoardType = None,
            **kw_params,
    ) -> GPIOPinBar:
        """
        Creates a new GPIOPinBar instance for the specified library and board.

        :param library: The library the instance wraps.
        :param board: The board the instance represents or None for custom layout.
        :param kw_params: The parameters for the concrete instance construction. Matches the constructor
        of the concrete class.
        :return: An instance of a type that matches the specified library and board type.
        """
        if library is LibraryType.Emulator:
            return cls._new_emulator_instance(board, **kw_params)
        elif library is LibraryType.RPi_GPIO:
            return cls._new_rpi_instance(board, **kw_params)
        else:
            raise NotImplementedError(f'Unknown library {library}')

    @classmethod
    def _new_emulator_instance(cls, board: Optional[BoardType], **kw_params) -> GPIOPinBar:
        """ Creates a new emulator instance for the given board """
        supported_boards: List[BoardType] = [
            None,
            BoardType.Raspi_40_pin_header,
        ]

        if board is None:
            return GPIOPinBarEmulator(**kw_params)
        elif board is BoardType.Raspi_40_pin_header:
            return Raspi40PinBarEmulator(**kw_params)

        elif board not in supported_boards:
            raise ValueError(f'BoardType {board} is not supported for library {LibraryType.Emulator}')
        else:
            raise NotImplementedError(f'Unknown BoardType {board}')

    @classmethod
    def _new_rpi_instance(cls, board: Optional[BoardType], **kw_params) -> RPiGPIOPinBar:
        """ Creates a new rpi gpio pin bar instance for the given board """
        supported_boards: List[BoardType] = [
            None,
            BoardType.Raspi_40_pin_header,
        ]

        if board is None:
            return RPiGPIOPinBar(**kw_params)
        elif board is BoardType.Raspi_40_pin_header:
            return Raspi40PinBarRPi(**kw_params)

        elif board not in supported_boards:
            raise ValueError(f'BoardType {board} is not supported for library {LibraryType.RPi_GPIO}')
        else:
            raise NotImplementedError(f'Unknown BoardType {board}')
