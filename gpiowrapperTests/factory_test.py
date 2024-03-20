import sys
import unittest
from unittest.mock import patch, MagicMock

from gpiowrapper.base import GPIOPinBarEmulator, PinAddressing
from gpiowrapper.factory import LibraryType, GPIOPinBarFactory, BoardType
from gpiowrapper.raspi import Raspi40PinBarEmulator
from gpiowrapper.raspi.rpi_gpio_library import RPiGPIOPinBar, Raspi40PinBarRPi


class GPIOPinBarFactoryTests(unittest.TestCase):
    cls_path = f'{GPIOPinBarFactory.__module__}.{GPIOPinBarFactory.__name__}'
    cls = GPIOPinBarFactory

    @patch(f'{cls_path}.{cls._new_emulator_instance.__name__}')
    def test_new_pin_bar_instance__EmulatorLibrary__CallsNewEmulatorInstance(self, mock: MagicMock):
        # Arrange
        library = LibraryType.Emulator

        # Act
        GPIOPinBarFactory.new_pin_bar_instance(library=library)

        # Assert
        mock.assert_called_once()

    @patch(f'{cls_path}.{cls._new_rpi_instance.__name__}')
    def test_new_pin_bar_instance__RPiGPIOLibrary__CallsNewRpiInstance(self, mock: MagicMock):
        # Arrange
        library = LibraryType.RPi_GPIO

        # Act
        GPIOPinBarFactory.new_pin_bar_instance(library=library)

        # Assert
        mock.assert_called_once()

    @patch(f'{GPIOPinBarEmulator.__module__}.{GPIOPinBarEmulator.__name__}')
    def test_new_emulator_instance__NoneBoard__ReturnsGPIOPinBarEmulator(self, _):
        # Arrange
        board = None
        kw_params = {
            'initial_addressing': PinAddressing.PinBar,
            'pin_assignment': [],
        }

        # Act
        instance = GPIOPinBarFactory._new_emulator_instance(board=board, **kw_params)

        # Assert
        expected_type = GPIOPinBarEmulator
        self.assertIsInstance(instance, expected_type)

    @patch(f'{Raspi40PinBarEmulator.__module__}.{Raspi40PinBarEmulator.__name__}')
    def test_new_emulator_instance__Raspi40PinHeaderBoard__ReturnsRaspi40PinBarEmulator(self, _):
        # Arrange
        board = BoardType.Raspi_40_pin_header
        kw_params = {
            'initial_addressing': PinAddressing.PinBar,
        }

        # Act
        instance = GPIOPinBarFactory._new_emulator_instance(board=board, **kw_params)

        # Assert
        expected_type = Raspi40PinBarEmulator
        self.assertIsInstance(instance, expected_type)

    @patch.dict(sys.modules, {'RPi.GPIO': MagicMock(), 'RPi': MagicMock()})
    @patch.dict(sys.modules[Raspi40PinBarRPi.__module__].__dict__, {'GPIO': MagicMock()})
    @patch(f'{RPiGPIOPinBar.__module__}.{RPiGPIOPinBar.__name__}')
    def test_new_rpi_instance__NoneBoard__ReturnsRPiGPIOPinBar(self, _):
        # Arrange
        board = None
        kw_params = {
            'initial_addressing': PinAddressing.PinBar,
            'pin_assignment': [],
        }

        # Act
        instance = GPIOPinBarFactory._new_rpi_instance(board=board, **kw_params)

        # Assert
        expected_type = RPiGPIOPinBar
        self.assertIsInstance(instance, expected_type)

    @patch.dict(sys.modules, {'RPi.GPIO': MagicMock(), 'RPi': MagicMock()})
    @patch.dict(sys.modules[Raspi40PinBarRPi.__module__].__dict__, {'GPIO': MagicMock()})
    @patch(f'{Raspi40PinBarRPi.__module__}.{Raspi40PinBarRPi.__name__}')
    def test_new_rpi_instance__Raspi40PinHeaderBoard__ReturnsRaspi40PinBarRPi(self, _):
        # Arrange
        board = BoardType.Raspi_40_pin_header
        kw_params = {
            'initial_addressing': PinAddressing.PinBar,
        }

        # Act
        instance = GPIOPinBarFactory._new_rpi_instance(board=board, **kw_params)

        # Assert
        expected_type = Raspi40PinBarRPi
        self.assertIsInstance(instance, expected_type)
