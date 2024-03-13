import copy
import unittest
from dataclasses import dataclass

from gpiowrapper import PinType, GPIOPinMode
from gpiowrapper.base import _Pin, _GPIOPin, PinAddressing
from gpiowrapper.raspi import Raspi40PinBarEmulator


@dataclass(frozen=True)
class RaspiPinBarTestDefaults:
    @staticmethod
    def default_pins():
        value = [
            _Pin(idx=1, type=PinType.POWER),
            _Pin(idx=2, type=PinType.POWER),
            _GPIOPin(idx=3, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.OFF),
            _Pin(idx=4, type=PinType.POWER),
            _GPIOPin(idx=5, type=PinType.GPIO, gpio_idx=3, mode=GPIOPinMode.OFF),
            _Pin(idx=6, type=PinType.GROUND),
            _GPIOPin(idx=7, type=PinType.GPIO, gpio_idx=4, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=8, type=PinType.GPIO, gpio_idx=14, mode=GPIOPinMode.OFF),
            _Pin(idx=9, type=PinType.GROUND),
            _GPIOPin(idx=10, type=PinType.GPIO, gpio_idx=15, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=11, type=PinType.GPIO, gpio_idx=17, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=12, type=PinType.GPIO, gpio_idx=18, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=13, type=PinType.GPIO, gpio_idx=27, mode=GPIOPinMode.OFF),
            _Pin(idx=14, type=PinType.GROUND),
            _GPIOPin(idx=15, type=PinType.GPIO, gpio_idx=22, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=16, type=PinType.GPIO, gpio_idx=23, mode=GPIOPinMode.OFF),
            _Pin(idx=17, type=PinType.POWER),
            _GPIOPin(idx=18, type=PinType.GPIO, gpio_idx=24, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=19, type=PinType.GPIO, gpio_idx=10, mode=GPIOPinMode.OFF),
            _Pin(idx=20, type=PinType.GROUND),
            _GPIOPin(idx=21, type=PinType.GPIO, gpio_idx=9, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=22, type=PinType.GPIO, gpio_idx=25, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=23, type=PinType.GPIO, gpio_idx=11, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=24, type=PinType.GPIO, gpio_idx=8, mode=GPIOPinMode.OFF),
            _Pin(idx=25, type=PinType.GROUND),
            _GPIOPin(idx=26, type=PinType.GPIO, gpio_idx=7, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=27, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=28, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=29, type=PinType.GPIO, gpio_idx=5, mode=GPIOPinMode.OFF),
            _Pin(idx=30, type=PinType.GROUND),
            _GPIOPin(idx=31, type=PinType.GPIO, gpio_idx=6, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=32, type=PinType.GPIO, gpio_idx=12, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=33, type=PinType.GPIO, gpio_idx=13, mode=GPIOPinMode.OFF),
            _Pin(idx=34, type=PinType.GROUND),
            _GPIOPin(idx=35, type=PinType.GPIO, gpio_idx=19, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=36, type=PinType.GPIO, gpio_idx=16, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=37, type=PinType.GPIO, gpio_idx=26, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=38, type=PinType.GPIO, gpio_idx=20, mode=GPIOPinMode.OFF),
            _Pin(idx=39, type=PinType.GROUND),
            _GPIOPin(idx=40, type=PinType.GPIO, gpio_idx=21, mode=GPIOPinMode.OFF),
        ]
        return copy.deepcopy(value)

    @staticmethod
    def default_gpio_pins(mode: GPIOPinMode = GPIOPinMode.OFF):
        value = [
            _GPIOPin(idx=27, type=PinType.GPIO, gpio_idx=0, mode=mode),
            _GPIOPin(idx=28, type=PinType.GPIO, gpio_idx=1, mode=mode),
            _GPIOPin(idx=3, type=PinType.GPIO, gpio_idx=2, mode=mode),
            _GPIOPin(idx=5, type=PinType.GPIO, gpio_idx=3, mode=mode),
            _GPIOPin(idx=7, type=PinType.GPIO, gpio_idx=4, mode=mode),
            _GPIOPin(idx=29, type=PinType.GPIO, gpio_idx=5, mode=mode),
            _GPIOPin(idx=31, type=PinType.GPIO, gpio_idx=6, mode=mode),
            _GPIOPin(idx=26, type=PinType.GPIO, gpio_idx=7, mode=mode),
            _GPIOPin(idx=24, type=PinType.GPIO, gpio_idx=8, mode=mode),
            _GPIOPin(idx=21, type=PinType.GPIO, gpio_idx=9, mode=mode),
            _GPIOPin(idx=19, type=PinType.GPIO, gpio_idx=10, mode=mode),
            _GPIOPin(idx=23, type=PinType.GPIO, gpio_idx=11, mode=mode),
            _GPIOPin(idx=32, type=PinType.GPIO, gpio_idx=12, mode=mode),
            _GPIOPin(idx=33, type=PinType.GPIO, gpio_idx=13, mode=mode),
            _GPIOPin(idx=8, type=PinType.GPIO, gpio_idx=14, mode=mode),
            _GPIOPin(idx=10, type=PinType.GPIO, gpio_idx=15, mode=mode),
            _GPIOPin(idx=36, type=PinType.GPIO, gpio_idx=16, mode=mode),
            _GPIOPin(idx=11, type=PinType.GPIO, gpio_idx=17, mode=mode),
            _GPIOPin(idx=12, type=PinType.GPIO, gpio_idx=18, mode=mode),
            _GPIOPin(idx=35, type=PinType.GPIO, gpio_idx=19, mode=mode),
            _GPIOPin(idx=38, type=PinType.GPIO, gpio_idx=20, mode=mode),
            _GPIOPin(idx=40, type=PinType.GPIO, gpio_idx=21, mode=mode),
            _GPIOPin(idx=15, type=PinType.GPIO, gpio_idx=22, mode=mode),
            _GPIOPin(idx=16, type=PinType.GPIO, gpio_idx=23, mode=mode),
            _GPIOPin(idx=18, type=PinType.GPIO, gpio_idx=24, mode=mode),
            _GPIOPin(idx=22, type=PinType.GPIO, gpio_idx=25, mode=mode),
            _GPIOPin(idx=37, type=PinType.GPIO, gpio_idx=26, mode=mode),
            _GPIOPin(idx=13, type=PinType.GPIO, gpio_idx=27, mode=mode),
        ]
        return copy.deepcopy(value)

    @staticmethod
    def gpio_pin_ids():
        value = [
                27, 28, 3, 5, 7, 29, 31, 26, 24, 21, 19, 23, 32, 33, 8,
                10, 36, 11, 12, 35, 38, 40, 15, 16, 18, 22, 37, 13
        ]
        return copy.deepcopy(value)


class Raspi40PinBarEmulatorTests(unittest.TestCase):
    class_path = f'{Raspi40PinBarEmulator.__module__}.Raspi40PinBarEmulator'

    def test_init__Always__HasCorrectPins(self):
        # Arrange
        expected_pins = RaspiPinBarTestDefaults.default_pins()

        # Act
        bar = Raspi40PinBarEmulator(initial_addressing=PinAddressing.PinBar)

        # Assert
        self.assertListEqual(bar._pins, expected_pins)

    def test_init__Always__HasCorrectGPIOPins(self):
        # Arrange
        expected_gpio_pins = RaspiPinBarTestDefaults.default_gpio_pins()

        # Act
        bar = Raspi40PinBarEmulator(initial_addressing=PinAddressing.PinBar)

        # Assert
        self.assertListEqual(bar._gpio_pins, expected_gpio_pins)
