import sys
import unittest
from unittest.mock import patch, MagicMock, call, ANY

from gpiowrapper import GPIOPinMode
from gpiowrapper.base import PinAddressing, _GPIOPin, PinType, GPIOPinState
from gpiowrapper.raspi import Raspi40PinBarRPi
from gpiowrapper.raspi.rpi_gpio_library import RPiGPIOPinBar
from gpiowrapperTests.raspi.raspi_base_test import RaspiPinBarTestDefaults

global_rpi_mock = MagicMock()
GPIO = global_rpi_mock


@patch.dict(sys.modules, {'RPi.GPIO': global_rpi_mock, 'RPi': MagicMock()})
@patch.dict(sys.modules[Raspi40PinBarRPi.__module__].__dict__, {'GPIO': global_rpi_mock})
class RPiGPIOPinBarTests(unittest.TestCase):
    class_path = f'{RPiGPIOPinBar.__module__}.RPiGPIOPinBar'
    rpi_mock = global_rpi_mock

    def setUp(self):
        self.rpi_mock.reset_mock()

    def test_change_pin_modes__Always__ChangesPinModes(self):
        # Arrange
        pin_assignment = [
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
        ]
        bar = RPiGPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.IN),
        ]
        new_modes_it = iter([GPIOPinMode.OUT, GPIOPinMode.OFF, GPIOPinMode.IN])

        # Act
        bar._change_pin_modes(pins=pins, new_modes_iterator=new_modes_it)

        # Assert
        expected_modes = [GPIOPinMode.OUT, GPIOPinMode.OFF, GPIOPinMode.IN]
        actual_modes = [pin.mode for pin in pins]
        self.assertListEqual(expected_modes, actual_modes)

    def test_change_pin_modes__ChangeFromOff__NoRpiCleanupCalled(self):
        # Arrange
        cleanup_mock: MagicMock = self.rpi_mock.cleanup

        pin_assignment = [
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
        ]
        bar = RPiGPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.OFF),
        ]
        new_modes_it = iter([GPIOPinMode.OFF, GPIOPinMode.IN, GPIOPinMode.OUT])

        # Act
        bar._change_pin_modes(pins=pins, new_modes_iterator=new_modes_it)

        # Assert
        cleanup_mock.assert_not_called()

    def test_change_pin_modes__ChangeFromNotOff__CallsRpiCleanup(self):
        # Arrange
        cleanup_mock: MagicMock = self.rpi_mock.cleanup

        pin_assignment = [
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
        ]
        bar = RPiGPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.IN),
        ]
        new_modes_it = iter([GPIOPinMode.OFF, GPIOPinMode.IN, GPIOPinMode.OUT])

        # Act
        bar._change_pin_modes(pins=pins, new_modes_iterator=new_modes_it)

        # Assert
        expected_calls = [
            call(0),
            call(1),
            call(2),
        ]
        cleanup_mock.assert_has_calls(expected_calls)
        self.assertEqual(3, cleanup_mock.call_count)

    def test_change_pin_modes__NoChange__NoRpiCleanupCalled(self):
        # Arrange
        cleanup_mock: MagicMock = self.rpi_mock.cleanup

        pin_assignment = [
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
        ]
        bar = RPiGPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.IN),
        ]
        new_modes_it = iter([GPIOPinMode.OFF, GPIOPinMode.OUT, GPIOPinMode.IN])

        # Act
        bar._change_pin_modes(pins=pins, new_modes_iterator=new_modes_it)

        # Assert
        cleanup_mock.assert_not_called()

    def test_change_pin_modes__ChangeToOff__NoRpiSetupCalled(self):
        # Arrange
        setup_mock: MagicMock = self.rpi_mock.setup

        pin_assignment = [
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
        ]
        bar = RPiGPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.IN),
        ]
        new_modes_it = iter([GPIOPinMode.OFF, GPIOPinMode.OFF, GPIOPinMode.OFF])

        # Act
        bar._change_pin_modes(pins=pins, new_modes_iterator=new_modes_it)

        # Assert
        setup_mock.assert_not_called()

    def test_change_pin_modes__ChangeToNotOff__CallsRpiSetup(self):
        # Arrange
        setup_mock: MagicMock = self.rpi_mock.setup

        pin_assignment = [
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
        ]
        bar = RPiGPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.IN),
        ]
        new_modes_it = iter([GPIOPinMode.IN, GPIOPinMode.IN, GPIOPinMode.OUT])

        # Act
        bar._change_pin_modes(pins=pins, new_modes_iterator=new_modes_it)

        # Assert
        expected_calls = [
            call(0, GPIO.IN, pull_up_down=ANY),
            call(1, GPIO.IN, pull_up_down=ANY),
            call(2, GPIO.OUT, pull_up_down=ANY),
        ]
        setup_mock.assert_has_calls(expected_calls)
        self.assertEqual(3, setup_mock.call_count)

    def test_change_pin_modes__ChangeToInWithPullUpDown__CallsRpiSetupWithCorrectPullUpDownParam(self):
        # Arrange
        setup_mock: MagicMock = self.rpi_mock.setup

        pin_assignment = [
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
        ]
        bar = RPiGPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.OFF),
        ]
        new_modes_it = iter([GPIOPinMode.IN_PULL_UP, GPIOPinMode.IN, GPIOPinMode.IN_PULL_DOWN])

        # Act
        bar._change_pin_modes(pins=pins, new_modes_iterator=new_modes_it)

        # Assert
        expected_calls = [
            call(0, GPIO.IN, pull_up_down=GPIO.PUD_UP),
            call(1, GPIO.IN, pull_up_down=GPIO.PUD_OFF),
            call(2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN),
        ]
        setup_mock.assert_has_calls(expected_calls)
        self.assertEqual(3, setup_mock.call_count)

    def test_change_pin_modes__NoChange__NoRpiSetupCalled(self):
        # Arrange
        setup_mock: MagicMock = self.rpi_mock.setup

        pin_assignment = [
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
        ]
        bar = RPiGPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.IN),
        ]
        new_modes_it = iter([GPIOPinMode.OFF, GPIOPinMode.OUT, GPIOPinMode.IN])

        # Act
        bar._change_pin_modes(pins=pins, new_modes_iterator=new_modes_it)

        # Assert
        setup_mock.assert_not_called()

    def test_gpio_pin_states_iterator__Always__CallsRpiInput(self):
        # Arrange
        input_mock: MagicMock = self.rpi_mock.input

        pin_assignment = [
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
        ]
        bar = RPiGPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.IN),
        ]
        input_mock.side_effect = [GPIO.HIGH, GPIO.HIGH, GPIO.LOW]

        # Act
        _ = bar._gpio_pin_states_iterator(pins=pins)

        # Assert
        expected_calls = [call(i) for i in range(3)]
        input_mock.assert_has_calls(expected_calls)
        self.assertEqual(len(expected_calls), input_mock.call_count)

    def test_gpio_pin_states_iterator__Always__ReturnsIteratorIteratingCorrectGPIOPinStates(self):
        # Arrange
        input_mock: MagicMock = self.rpi_mock.input

        pin_assignment = [
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
        ]
        bar = RPiGPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.IN),
        ]
        input_mock.side_effect = [GPIO.HIGH, GPIO.HIGH, GPIO.LOW]

        # Act
        states_it = bar._gpio_pin_states_iterator(pins=pins)

        # Assert
        expected_states = [GPIOPinState.HIGH, GPIOPinState.HIGH, GPIOPinState.LOW]
        actual_states = [state for state in states_it]
        self.assertListEqual(expected_states, actual_states)

    def test_change_gpio_pin_states__Always__CallsRpiOutput(self):
        # Arrange
        output_mock: MagicMock = self.rpi_mock.output

        pin_assignment = [
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
        ]
        bar = RPiGPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.IN),
        ]
        new_states = [GPIOPinState.HIGH, GPIOPinState.HIGH, GPIOPinState.LOW]

        # Act
        bar._change_gpio_pin_states(pins=pins, new_states=new_states)

        # Assert
        expected_ids_param = [0, 1, 2]
        expected_states_param = [GPIO.HIGH, GPIO.HIGH, GPIO.LOW]
        output_mock.assert_called_once_with(expected_ids_param, expected_states_param)

    def test_deleter__Always__CallsCleanup(self):
        # Arrange
        pin_assignment = [
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
        ]
        bar = RPiGPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        bar._pins = bar._gpio_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.IN),
        ]

        # Act
        del bar

        # Assert
        expected_calls = [
            call(1),
            call(2),
        ]
        self.rpi_mock.cleanup.assert_has_calls(expected_calls)


@patch.dict(sys.modules, {'RPi.GPIO': global_rpi_mock, 'RPi': MagicMock()})
@patch.dict(sys.modules[Raspi40PinBarRPi.__module__].__dict__, {'GPIO': global_rpi_mock})
class Raspi40PinBarRPiTests(unittest.TestCase):
    class_path = f'{Raspi40PinBarRPi.__module__}.Raspi40PinBarRPi'
    rpi_mock = global_rpi_mock

    def setUp(self):
        self.rpi_mock.reset_mock()

    def test_init__Always__HasCorrectPins(self):
        # Arrange
        expected_pins = RaspiPinBarTestDefaults.default_pins()

        # Act
        bar = Raspi40PinBarRPi(initial_addressing=PinAddressing.GPIO)

        # Assert
        self.assertListEqual(bar._pins, expected_pins)

    def test_init__Always__HasCorrectGPIOPins(self):
        # Arrange
        expected_gpio_pins = RaspiPinBarTestDefaults.default_gpio_pins()

        # Act
        bar = Raspi40PinBarRPi(initial_addressing=PinAddressing.GPIO)

        # Assert
        self.assertListEqual(bar._gpio_pins, expected_gpio_pins)
