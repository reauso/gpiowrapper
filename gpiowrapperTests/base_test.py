import unittest
from typing import List
from unittest.mock import patch, MagicMock, call

from parameterized import parameterized

from gpiowrapper import GPIOPinState, GPIOPinMode, PinAddressing, PinType, GPIOPinBarEmulator
from gpiowrapper.base import PinBar, _Pin, _GPIOPin, GPIOPinBar, ModeIsOffError, PinTypeError, \
    PinBarError
from gpiowrapperTests.useful_test_util import ExtendedTestCase


@patch.multiple(PinBar, __abstractmethods__=set())
class PinBarTests(unittest.TestCase):
    class_path = f'{PinBar.__module__}.{PinBar.__name__}'

    def test_init__EmptyPinAssignment__SetEmptyPinsList(self):
        # Arrange & Act
        bar = PinBar([])

        # Assert
        self.assertListEqual([], bar._pins)
        self.assertEqual(0, len(bar))

    def test_init__MixedPinAssignment__SetAccordingPinsList(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        expected_pins = [
            _Pin(idx=0, type=PinType.POWER),
            _Pin(idx=1, type=PinType.GROUND),
            _Pin(idx=2, type=PinType.GPIO),
            _Pin(idx=3, type=PinType.GPIO),
            _Pin(idx=4, type=PinType.GPIO),
            _Pin(idx=5, type=PinType.GPIO),
            _Pin(idx=6, type=PinType.OTHER),
        ]

        # Act
        bar = PinBar(pin_assignment)

        # Assert
        self.assertListEqual(expected_pins, bar._pins)
        self.assertEqual(7, len(bar))

    def test_init__WithIndexOffset__PinIndicesAreShifted(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        expected_pins = [
            _Pin(idx=5, type=PinType.POWER),
            _Pin(idx=6, type=PinType.GROUND),
            _Pin(idx=7, type=PinType.GPIO),
            _Pin(idx=8, type=PinType.GPIO),
            _Pin(idx=9, type=PinType.GPIO),
            _Pin(idx=10, type=PinType.GPIO),
            _Pin(idx=11, type=PinType.OTHER),
        ]

        # Act
        bar = PinBar(pin_assignment, idx_offset=5)

        # Assert
        self.assertListEqual(expected_pins, bar._pins)
        self.assertEqual(7, len(bar))


@patch.multiple(GPIOPinBar, __abstractmethods__=set())
class GPIOPinBarTests(ExtendedTestCase):
    class_path = f'{GPIOPinBar.__module__}.{GPIOPinBar.__name__}'

    def test_init__EmptyPinAssignment__SetEmptyGPIOPinsList(self):
        # Arrange & Act
        bar = GPIOPinBar([], initial_addressing=PinAddressing.PinBar)

        # Assert
        self.assertListEqual([], bar.pin_assignment)
        self.assertListEqual([], bar._gpio_pins)
        self.assertEqual(0, len(bar))

    def test_init__NoGPIOPinAssignment__SetEmptyGPIOPinsList(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.OTHER,
        ]

        # Act
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Assert
        self.assertListEqual(pin_assignment, bar.pin_assignment)
        self.assertListEqual([], bar._gpio_pins)
        self.assertEqual(3, len(bar))

    def test_init__OneGPIOPinAssignment__SetOneSizedGPIOPinsList(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.OTHER,
        ]
        expected_gpio_pins = [_GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF)]

        # Act
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Assert
        self.assertListEqual(pin_assignment, bar.pin_assignment)
        self.assertListEqual(expected_gpio_pins, bar._gpio_pins)
        self.assertEqual(4, len(bar))

    def test_init__MultipleGPIOPinAssignment__SetMultipleSizedGPIOPinsList(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        expected_gpio_pins = [
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=3, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=4, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.OFF),
        ]

        # Act
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Assert
        self.assertListEqual(pin_assignment, bar.pin_assignment)
        self.assertListEqual(expected_gpio_pins, bar._gpio_pins)
        self.assertEqual(6, len(bar))

    def test_init__IncompleteGPIOOrder__RaisesValueError(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        gpio_order_by_idx = [3]

        # Act & Assert
        with self.assertRaisesRegex(ValueError, 'gpio_order_from_ids parameter is invalid! '
                                                'Check if you are missing a gpio pin or have duplicates.'):
            _ = GPIOPinBar(pin_assignment, gpio_order_from_ids=gpio_order_by_idx,
                           initial_addressing=PinAddressing.PinBar)

    def test_init__InvalidGPIOOrderValue__RaisesValueError(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        gpio_order_by_idx = [1, 2, 3]

        # Act & Assert
        with self.assertRaisesRegex(ValueError, 'gpio_order_from_ids parameter is invalid! '
                                                'Check if you are missing a gpio pin or have duplicates.'):
            _ = GPIOPinBar(pin_assignment, gpio_order_from_ids=gpio_order_by_idx,
                           initial_addressing=PinAddressing.PinBar)

    def test_init__CompleteGPIOOrder__GPIOPinArrayInCustomOrder(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        gpio_order_by_idx = [3, 2, 4]
        expected_gpio_pins = [
            _GPIOPin(idx=3, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=4, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        bar = GPIOPinBar(pin_assignment, gpio_order_from_ids=gpio_order_by_idx,
                         initial_addressing=PinAddressing.PinBar)

        self.assertListEqual(expected_gpio_pins, bar._gpio_pins)

    def test_init__GPIOOrderWithOffset__GPIOIdxWithOffset(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        gpio_order_by_idx = [3, 2, 4]
        offset = 3
        expected_gpio_pins = [
            _GPIOPin(idx=3, type=PinType.GPIO, gpio_idx=3, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=4, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=4, type=PinType.GPIO, gpio_idx=5, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        bar = GPIOPinBar(pin_assignment, gpio_order_from_ids=gpio_order_by_idx, gpio_idx_offset=offset,
                         initial_addressing=PinAddressing.PinBar)

        self.assertListEqual(expected_gpio_pins, bar._gpio_pins)

    def test_addressing_setter__PinBarAddressing__CorrectArrayAndOffsetAndArrayLength(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=5, gpio_idx_offset=0, initial_addressing=PinAddressing.GPIO)
        assert bar._addressing_array != bar._pins
        assert bar._addressing_offset != 5
        assert bar._addressing_array_length != 6

        # Act
        bar.addressing = PinAddressing.PinBar

        # Assert
        self.assertListEqual(bar._pins, bar._addressing_array)
        self.assertEqual(5, bar._addressing_offset)
        self.assertEqual(6, bar._addressing_array_length)

    def test_addressing_setter__GPIOAddressing__CorrectArrayAndOffsetAndArrayLength(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=5, gpio_idx_offset=0, initial_addressing=PinAddressing.PinBar)
        assert bar._addressing_array != bar._gpio_pins
        assert bar._addressing_offset != 0
        assert bar._addressing_array_length != 3

        # Act
        bar.addressing = PinAddressing.GPIO

        # Assert
        self.assertListEqual(bar._gpio_pins, bar._addressing_array)
        self.assertEqual(0, bar._addressing_offset)
        self.assertEqual(3, bar._addressing_array_length)

    def test_current_idx_offset__PinBarAddressing__ReturnsIdxOffset(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=5, gpio_idx_offset=2, initial_addressing=PinAddressing.PinBar)
        assert bar.addressing == PinAddressing.PinBar

        # Act
        offset = bar.current_idx_offset

        # Assert
        self.assertEqual(5, offset)
        self.assertEqual(bar.idx_offset, offset)

    def test_current_idx_offset__GPIOAddressing__ReturnsGPIOIdxOffset(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=5, gpio_idx_offset=2, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO

        # Act
        offset = bar.current_idx_offset

        # Assert
        self.assertEqual(2, offset)
        self.assertEqual(bar.gpio_idx_offset, offset)

    def test_current_num_addressable_pins__PinBarAddressing__ReturnsSelfLen(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        assert bar.addressing == PinAddressing.PinBar

        # Act
        offset = bar.current_num_addressable_pins

        # Assert
        self.assertEqual(6, offset)
        self.assertEqual(len(bar), offset)

    def test_current_num_addressable_pins__GPIOAddressing__ReturnsNumGPIOPins(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO

        # Act
        offset = bar.current_num_addressable_pins

        # Assert
        self.assertEqual(3, offset)
        self.assertEqual(bar.num_gpio_pins, offset)

    def test_reset_gpio_pins__Always__SetsAllGPIOPinModesToOFF(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.reset_gpio_pins()

        # Assert
        for pin in bar._gpio_pins:
            self.assertEqual(GPIOPinMode.OFF, pin.mode)


class GPIOPinBarIndexValidatorTests(ExtendedTestCase):
    class_path = f'{GPIOPinBar.__module__}.{GPIOPinBar.__name__}'

    @parameterized.expand([[i] for i in range(5)])
    def test_validate_index_item__IntIndexInBounds__NoIndexError(self, item: int):
        # Arrange
        offset = 0
        length = 5
        addressing = PinAddressing.PinBar

        # Act & Assert
        with self.assertNotRaised(IndexError):
            _ = GPIOPinBar._IndexValidator.validate(item, offset, length, addressing)

    def test_validate_index_item__IntIndexOutsideBounds__RaisesIndexError(self):
        # Arrange
        offset = 0
        length = 5
        addressing = PinAddressing.PinBar

        # Act & Assert
        expected_regex = rf'index out of range for {PinAddressing.__name__}.\w*'
        with self.assertRaisesRegex(IndexError, expected_regex):
            _ = GPIOPinBar._IndexValidator.validate(6, offset, length, addressing)

    @parameterized.expand([[i + 10] for i in range(5)])
    def test_validate_index_item__IntIndexInBoundsWithOffset__NoIndexError(self, item: int):
        # Arrange
        offset = 10
        length = 5
        addressing = PinAddressing.PinBar

        # Act & Assert
        with self.assertNotRaised(IndexError):
            _ = GPIOPinBar._IndexValidator.validate(item, offset, length, addressing)

    @parameterized.expand([
        [0],
        [3],
        [9],
        [15],
        [18],
    ])
    def test_validate_index_item__IntIndexOutsideBoundsWithOffset__RaisesIndexError(self, item: int):
        # Arrange
        offset = 10
        length = 5
        addressing = PinAddressing.PinBar

        # Act & Assert
        expected_regex = rf'index out of range for {PinAddressing.__name__}.\w*'
        with self.assertRaisesRegex(IndexError, expected_regex):
            _ = GPIOPinBar._IndexValidator.validate(item, offset, length, addressing)

    @parameterized.expand([
        [slice(None, None, None)],
        [slice(1, None, None)],
        [slice(None, 10, None)],
        [slice(None, None, 10)],
        [slice(1, 3, 1)],
        [slice(-4, 5, 2)],
        [slice(0, 100, 1)],
        [slice(30, 50, 3)],
        [slice(-10, -2, 1)],
        [slice(-1, -20, -1)],
    ])
    def test_validate_index_item__SliceIndexIntAndNone__AlwaysNoTypeError(self, item: slice):
        # Arrange
        offset = 0
        length = 5
        addressing = PinAddressing.PinBar

        # Act & Assert
        with self.assertNotRaised(TypeError):
            _ = GPIOPinBar._IndexValidator.validate(item, offset, length, addressing)

    @parameterized.expand([
        [slice('start', 4, 1)],
        [slice('start', 'Stop', 'Step')],
        [slice(object(), 4, 1)],
        [slice(object(), object(), object())],
        [slice(2.13, 4, 1)],
        [slice(2.13, 6.76, 1.3)],
    ])
    def test_validate_index_item__SliceIndexWithInvalidValueType__RaisesTypeError(self, item: slice):
        # Arrange
        offset = 0
        length = 5
        addressing = PinAddressing.PinBar

        # Act & Assert
        expected_regex = r'slice indices must be integers or None or have an __index__ method'
        with self.assertRaisesRegex(TypeError, expected_regex):
            _ = GPIOPinBar._IndexValidator.validate(item, offset, length, addressing)

    def test_validate_index_item__IntListIndexInBounds__NoIndexError(self):
        # Arrange
        offset = 0
        length = 5
        addressing = PinAddressing.PinBar

        # Act & Assert
        with self.assertNotRaised(IndexError):
            _ = GPIOPinBar._IndexValidator.validate([1, 3, 4], offset, length, addressing)

    def test_validate_index_item__IntListIndexOutsideBounds__RaisesIndexError(self):
        # Arrange
        offset = 0
        length = 5
        addressing = PinAddressing.PinBar

        # Act & Assert
        expected_regex = rf'index out of range for {PinAddressing.__name__}.\w* at position \d*'
        with self.assertRaisesRegex(IndexError, expected_regex):
            _ = GPIOPinBar._IndexValidator.validate([1, 3, 13, 4], offset, length, addressing)

    @parameterized.expand([[[i + 10]] for i in range(5)])
    def test_validate_index_item__IntListIndexInBoundsWithOffset__NoIndexError(self, item: List[int]):
        # Arrange
        offset = 10
        length = 5
        addressing = PinAddressing.PinBar
        assert isinstance(item, list)

        # Act & Assert
        with self.assertNotRaised(IndexError):
            _ = GPIOPinBar._IndexValidator.validate(item, offset, length, addressing)

    @parameterized.expand([
        [[0]],
        [[3]],
        [[9]],
        [[15]],
        [[18]],
    ])
    def test_validate_index_item__IntListIndexOutsideBoundsWithOffset__RaisesIndexError(self, item: List[int]):
        # Arrange
        offset = 10
        length = 5
        addressing = PinAddressing.PinBar

        # Act & Assert
        expected_regex = rf'index out of range for {PinAddressing.__name__}.\w* at position \d*'
        with self.assertRaisesRegex(IndexError, expected_regex):
            _ = GPIOPinBar._IndexValidator.validate(item, offset, length, addressing)

    def test_validate_index_item__ListIndexWithInvalidEntryType__RaisesTypeError(self):
        # Arrange
        offset = 0
        length = 5
        addressing = PinAddressing.PinBar

        # Act & Assert
        expected_regex = r'list indices must be integers or have an __index__ method. Found type \w* at position \d*'
        with self.assertRaisesRegex(TypeError, expected_regex):
            _ = GPIOPinBar._IndexValidator.validate([2, 3, 'test'], offset, length, addressing)

    @parameterized.expand([
        [None],
        ['str'],
        [object()],
        [3.45],
    ])
    def test_validate_index_item__InvalidIndexType__RaisesTypeError(self, item):
        # Arrange
        offset = 0
        length = 5
        addressing = PinAddressing.PinBar

        # Act & Assert
        expected_regex = r'index must be integer, slice or list, not \w*'
        with self.assertRaisesRegex(TypeError, expected_regex):
            _ = GPIOPinBar._IndexValidator.validate(item, offset, length, addressing)


class GPIOPinBarModeValueValidatorTests(ExtendedTestCase):
    class_path = (f'{GPIOPinBar.__module__}.{GPIOPinBar.__name__}.'
                  f'{GPIOPinBar._ModeValueValidator.__name__}')
    cls = GPIOPinBar._ModeValueValidator

    @parameterized.expand([
        [GPIOPinMode.OUT],
        [[GPIOPinMode.OUT, GPIOPinMode.IN]],
    ])
    @patch(f'{class_path}.{cls._validate_type.__name__}', wraps=cls._validate_type)
    def test_validate__Always__CallsValidateType(self, value, validator_mock: MagicMock):
        # Arrange
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]
        index_types = [int, slice, list]

        # Act
        for index_type in index_types:
            try:
                GPIOPinBar._ModeValueValidator.validate(
                    value=value, index_type=index_type, considered_pins=considered_pins)
            except (ValueError, PinTypeError, ModeIsOffError):
                pass

        # Assert
        expected_calls = [
            call(type(value)),
            call(type(value)),
            call(type(value)),
        ]
        validator_mock.assert_has_calls(expected_calls)

    @parameterized.expand([
        [GPIOPinMode.OUT],
        [[GPIOPinMode.OUT, GPIOPinMode.IN]],
    ])
    @patch(f'{class_path}.{cls._validate_for_int_index.__name__}', wraps=cls._validate_for_int_index)
    def test_validate__IntIndex__CallsValidateForIntIndex(self, value, validator_mock: MagicMock):
        # Arrange
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act
        try:
            GPIOPinBar._ModeValueValidator.validate(
                value=value, index_type=int, considered_pins=considered_pins)
        except (ValueError, PinTypeError, ModeIsOffError):
            pass

        # Assert
        validator_mock.assert_called_once_with(value=value, considered_pins=considered_pins)

    @parameterized.expand([
        [GPIOPinMode.OUT],
        [[GPIOPinMode.OUT, GPIOPinMode.IN]],
    ])
    @patch(f'{class_path}.{cls._validate_for_slice_index.__name__}', wraps=cls._validate_for_slice_index)
    def test_validate__SliceIndex__CallsValidateForSliceIndex(self, value, validator_mock: MagicMock):
        # Arrange
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act
        try:
            GPIOPinBar._ModeValueValidator.validate(
                value=value, index_type=slice, considered_pins=considered_pins)
        except (ValueError, PinTypeError, ModeIsOffError):
            pass

        # Assert
        validator_mock.assert_called_once_with(value=value, considered_pins=considered_pins)

    @parameterized.expand([
        [GPIOPinMode.OUT],
        [[GPIOPinMode.OUT, GPIOPinMode.IN]],
    ])
    @patch(f'{class_path}.{cls._validate_for_list_index.__name__}', wraps=cls._validate_for_list_index)
    def test_validate__ListIndex__CallsValidateForListIndex(self, value, validator_mock: MagicMock):
        # Arrange
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act
        try:
            GPIOPinBar._ModeValueValidator.validate(
                value=value, index_type=list, considered_pins=considered_pins)
        except (ValueError, PinTypeError, ModeIsOffError):
            pass

        # Assert
        validator_mock.assert_called_once_with(value=value, considered_pins=considered_pins)

    def test_validate_type__ValidStateType__NoTypeError(self):
        # Act & Assert
        with self.assertNotRaised(TypeError):
            GPIOPinBar._ModeValueValidator._validate_type(GPIOPinMode)
        with self.assertNotRaised(TypeError):
            GPIOPinBar._ModeValueValidator._validate_type(list)

    def test_validate_type__InvalidStateType__RaiseTypeError(self):
        # Act & Assert
        expected_regex = rf'value must be {GPIOPinMode.__name__} or list, not str'
        with self.assertRaisesRegex(TypeError, expected_regex):
            GPIOPinBar._ModeValueValidator._validate_type(str)

        expected_regex = rf'value must be {GPIOPinMode.__name__} or list, not object'
        with self.assertRaisesRegex(TypeError, expected_regex):
            GPIOPinBar._ModeValueValidator._validate_type(object)

    def test_validate_for_int_index__ValueIsState__NoValueError(self):
        # Arrange
        value = GPIOPinMode.OUT
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        with self.assertNotRaised(ValueError):
            GPIOPinBar._ModeValueValidator._validate_for_int_index(value=value, considered_pins=considered_pins)

    def test_validate_for_int_index__ValueIsList__RaisesValueError(self):
        # Arrange
        value = [GPIOPinMode.OUT, GPIOPinMode.IN]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        expected_regex = r'setting an array element with a sequence.'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._ModeValueValidator._validate_for_int_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsState__NoValueError(self):
        # Arrange
        value = GPIOPinMode.OUT
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
            _Pin(idx=2, type=PinType.GPIO),
        ]

        # Act & Assert
        with self.assertNotRaised(ValueError):
            GPIOPinBar._ModeValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithInvalidEntryType__RaisesValueError(self):
        # Arrange
        value = [GPIOPinMode.OUT, 'test']
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        expected_regex = rf'list value must be of type {GPIOPinMode.__name__}, NoneType. Found type \w* at position \d*'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._ModeValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithModeEntryAddressingGPIOPin__NoPinTypeError(self):
        # Arrange
        value = [GPIOPinMode.OUT, GPIOPinMode.IN]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        with self.assertNotRaised(TypeError):
            GPIOPinBar._ModeValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithModeEntryAddressingNotGPIOPin__RaisesPinTypeError(self):
        # Arrange
        value = [GPIOPinMode.OUT, GPIOPinMode.IN]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _Pin(idx=1, type=PinType.GROUND),
        ]

        # Act & Assert
        expected_regex = rf'unable to assign {GPIOPinMode.__name__}.\w* at position \d* to pin of type {PinType.GROUND}'
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            GPIOPinBar._ModeValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithNoneEntryAddressingGPIOPin__RaisesPinTypeError(self):
        # Arrange
        value = [GPIOPinMode.OUT, None]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        expected_regex = rf'unable to assign None at position \d* to pin of type {PinType.GPIO}'
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            GPIOPinBar._ModeValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithNoneEntryAddressingNotGPIOPin__NoPinTypeError(self):
        # Arrange
        value = [GPIOPinMode.OUT, None]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _Pin(idx=1, type=PinType.GROUND),
        ]

        # Act & Assert
        with self.assertNotRaised(TypeError):
            GPIOPinBar._ModeValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithLesserSize__RaisesValueError(self):
        # Arrange
        value = [GPIOPinMode.OUT, GPIOPinMode.IN]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
            _Pin(idx=2, type=PinType.GROUND),
        ]

        # Act & Assert
        expected_regex = rf'could not broadcast input array from size 2 into size 3'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._ModeValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithGreaterSize__RaisesValueError(self):
        # Arrange
        value = [GPIOPinMode.OUT, GPIOPinMode.IN]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        expected_regex = rf'could not broadcast input array from size 2 into size 1'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._ModeValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_list_index__ValueIsState__NoValueError(self):
        # Arrange
        value = GPIOPinMode.OUT
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        with self.assertNotRaised(ValueError):
            GPIOPinBar._ModeValueValidator._validate_for_list_index(value=value, considered_pins=considered_pins)

    def test_validate_for_list_index__ValueIsListWithInvalidEntryType__RaisesValueError(self):
        # Arrange
        value = [GPIOPinMode.OUT, 'test']
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        expected_regex = rf'list value must be of type {GPIOPinMode.__name__}. Found type \w* at position \d*'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._ModeValueValidator._validate_for_list_index(value=value, considered_pins=considered_pins)

    def test_validate_for_list_index__ValueIsListWithOnlyModeEntries__NoValueError(self):
        # Arrange
        value = [GPIOPinMode.OUT, GPIOPinMode.IN]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        with self.assertNotRaised(ValueError):
            GPIOPinBar._ModeValueValidator._validate_for_list_index(value=value, considered_pins=considered_pins)

    def test_validate_for_list_index__ValueIsListWithNoneEntry__RaisesValueError(self):
        # Arrange
        value = [GPIOPinMode.OUT, None]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        expected_regex = rf'list value must be of type {GPIOPinMode.__name__}. Found type \w* at position \d*'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._ModeValueValidator._validate_for_list_index(value=value, considered_pins=considered_pins)

    def test_validate_for_list_index__ValueIsListWithLesserSize__RaisesValueError(self):
        # Arrange
        value = [GPIOPinMode.OUT, GPIOPinMode.IN]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        expected_regex = rf'could not broadcast input array from size 2 into size 3'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._ModeValueValidator._validate_for_list_index(value=value, considered_pins=considered_pins)

    def test_validate_for_list_index__ValueIsListWithGreaterSize__RaisesValueError(self):
        # Arrange
        value = [GPIOPinMode.OUT, GPIOPinMode.IN]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        expected_regex = rf'could not broadcast input array from size 2 into size 1'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._ModeValueValidator._validate_for_list_index(value=value, considered_pins=considered_pins)


class GPIOPinBarStateValueValidatorTests(ExtendedTestCase):
    class_path = (f'{GPIOPinBar.__module__}.{GPIOPinBar.__name__}.'
                  f'{GPIOPinBar._StateValueValidator.__name__}')
    cls = GPIOPinBar._StateValueValidator

    @parameterized.expand([
        [GPIOPinState.LOW],
        [[GPIOPinState.LOW, GPIOPinState.HIGH]],
    ])
    @patch(f'{class_path}.{cls._validate_type.__name__}', wraps=cls._validate_type)
    def test_validate__Always__CallsValidateType(self, value, validator_mock: MagicMock):
        # Arrange
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]
        index_types = [int, slice, list]

        # Act
        for index_type in index_types:
            try:
                GPIOPinBar._StateValueValidator.validate(
                    value=value, index_type=index_type, considered_pins=considered_pins)
            except (ValueError, PinTypeError, ModeIsOffError):
                pass

        # Assert
        expected_calls = [
            call(type(value)),
            call(type(value)),
            call(type(value)),
        ]
        validator_mock.assert_has_calls(expected_calls)

    @parameterized.expand([
        [GPIOPinState.LOW],
        [[GPIOPinState.LOW, GPIOPinState.HIGH]],
    ])
    @patch(f'{class_path}.{cls._validate_for_int_index.__name__}', wraps=cls._validate_for_int_index)
    def test_validate__IntIndex__CallsValidateForIntIndex(self, value, validator_mock: MagicMock):
        # Arrange
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act
        try:
            GPIOPinBar._StateValueValidator.validate(
                value=value, index_type=int, considered_pins=considered_pins)
        except (ValueError, PinTypeError, ModeIsOffError):
            pass

        # Assert
        validator_mock.assert_called_once_with(value=value, considered_pins=considered_pins)

    @parameterized.expand([
        [GPIOPinState.LOW],
        [[GPIOPinState.LOW, GPIOPinState.HIGH]],
    ])
    @patch(f'{class_path}.{cls._validate_for_slice_index.__name__}', wraps=cls._validate_for_slice_index)
    def test_validate__SliceIndex__CallsValidateForSliceIndex(self, value, validator_mock: MagicMock):
        # Arrange
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act
        try:
            GPIOPinBar._StateValueValidator.validate(
                value=value, index_type=slice, considered_pins=considered_pins)
        except (ValueError, PinTypeError, ModeIsOffError):
            pass

        # Assert
        validator_mock.assert_called_once_with(value=value, considered_pins=considered_pins)

    @parameterized.expand([
        [GPIOPinState.LOW],
        [[GPIOPinState.LOW, GPIOPinState.HIGH]],
    ])
    @patch(f'{class_path}.{cls._validate_for_list_index.__name__}', wraps=cls._validate_for_list_index)
    def test_validate__ListIndex__CallsValidateForListIndex(self, value, validator_mock: MagicMock):
        # Arrange
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act
        try:
            GPIOPinBar._StateValueValidator.validate(
                value=value, index_type=list, considered_pins=considered_pins)
        except (ValueError, PinTypeError, ModeIsOffError):
            pass

        # Assert
        validator_mock.assert_called_once_with(value=value, considered_pins=considered_pins)

    def test_validate_type__ValidStateType__NoTypeError(self):
        # Act & Assert
        with self.assertNotRaised(TypeError):
            GPIOPinBar._StateValueValidator._validate_type(GPIOPinState)
        with self.assertNotRaised(TypeError):
            GPIOPinBar._StateValueValidator._validate_type(list)

    def test_validate_type__InvalidStateType__RaiseTypeError(self):
        # Act & Assert
        expected_regex = rf'value must be {GPIOPinState.__name__} or list, not str'
        with self.assertRaisesRegex(TypeError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_type(str)

        expected_regex = rf'value must be {GPIOPinState.__name__} or list, not object'
        with self.assertRaisesRegex(TypeError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_type(object)

    def test_validate_for_int_index__ValueIsState__NoValueError(self):
        # Arrange
        value = GPIOPinState.LOW
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        with self.assertNotRaised(ValueError):
            GPIOPinBar._StateValueValidator._validate_for_int_index(value=value, considered_pins=considered_pins)

    def test_validate_for_int_index__ValueIsList__RaisesValueError(self):
        # Arrange
        value = [GPIOPinState.LOW, GPIOPinState.HIGH]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        expected_regex = r'setting an array element with a sequence.'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_for_int_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsState__NoValueError(self):
        # Arrange
        value = GPIOPinState.LOW
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
            _Pin(idx=2, type=PinType.GPIO),
        ]

        # Act & Assert
        with self.assertNotRaised(ValueError):
            GPIOPinBar._StateValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithInvalidEntryType__RaisesValueError(self):
        # Arrange
        value = [GPIOPinState.LOW, 'test']
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
        ]

        # Act & Assert
        expected_regex = rf'list value must be of type {GPIOPinState.__name__}, NoneType. Found type \w* at position \d*'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithModeEntryAddressingGPIOPinWithModeNotOff__NoPinTypeError(self):
        # Arrange
        value = [GPIOPinState.LOW, GPIOPinState.HIGH]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
        ]

        # Act & Assert
        with self.assertNotRaised(PinTypeError):
            GPIOPinBar._StateValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithModeEntryAddressingGPIOPinWithModeOff__RaisesModeIsOffError(self):
        # Arrange
        value = [GPIOPinState.LOW, GPIOPinState.HIGH]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        expected_regex = (rf'unable to assign {GPIOPinState.__name__}.\w* at position \d* to pin of type '
                          rf'{PinType.GPIO} with {GPIOPinMode.OFF}')
        with self.assertRaisesRegex(ModeIsOffError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithModeEntryAddressingNotGPIOPin__RaisesPinTypeError(self):
        # Arrange
        value = [GPIOPinState.LOW, GPIOPinState.HIGH]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _Pin(idx=1, type=PinType.GROUND),
        ]

        # Act & Assert
        expected_regex = rf'unable to assign {GPIOPinState.__name__}.\w* at position \d* to pin of type {PinType.GROUND}'
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithNoneEntryAddressingGPIOPinWithModeNotOff__RaisesValueError(
            self):
        # Arrange
        value = [GPIOPinState.LOW, None]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
        ]

        # Act & Assert
        expected_regex = rf'unable to assign None at position \d* to pin of type {PinType.GPIO} with {GPIOPinMode.IN}'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithNoneEntryAddressingGPIOPinWithModeOff__NoModeIsOffError(self):
        # Arrange
        value = [GPIOPinState.LOW, None]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        with self.assertNotRaised(ModeIsOffError):
            GPIOPinBar._StateValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithNoneEntryAddressingNotGPIOPin__NoPinTypeError(self):
        # Arrange
        value = [GPIOPinState.LOW, None]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _Pin(idx=1, type=PinType.GROUND),
        ]

        # Act & Assert
        with self.assertNotRaised(PinTypeError):
            GPIOPinBar._StateValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithLesserSize__RaisesValueError(self):
        # Arrange
        value = [GPIOPinState.LOW, GPIOPinState.HIGH]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
            _Pin(idx=2, type=PinType.GROUND),
        ]

        # Act & Assert
        expected_regex = rf'could not broadcast input array from size 2 into size 3'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_slice_index__ValueIsListWithGreaterSize__RaisesValueError(self):
        # Arrange
        value = [GPIOPinState.LOW, GPIOPinState.HIGH]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
        ]

        # Act & Assert
        expected_regex = rf'could not broadcast input array from size 2 into size 1'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_for_slice_index(value=value, considered_pins=considered_pins)

    def test_validate_for_list_index__ValueIsState__NoValueError(self):
        # Arrange
        value = GPIOPinState.LOW
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OFF),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.OFF),
        ]

        # Act & Assert
        with self.assertNotRaised(ValueError):
            GPIOPinBar._StateValueValidator._validate_for_list_index(value=value, considered_pins=considered_pins)

    def test_validate_for_list_index__ValueIsListWithInvalidEntryType__RaisesValueError(self):
        # Arrange
        value = [GPIOPinState.LOW, 'test']
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
        ]

        # Act & Assert
        expected_regex = rf'list value must be of type {GPIOPinState.__name__}. Found type \w* at position \d*'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_for_list_index(value=value, considered_pins=considered_pins)

    def test_validate_for_list_index__ValueIsListWithOnlyModeEntries__NoValueError(self):
        # Arrange
        value = [GPIOPinState.LOW, GPIOPinState.HIGH]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
        ]

        # Act & Assert
        with self.assertNotRaised(ValueError):
            GPIOPinBar._StateValueValidator._validate_for_list_index(value=value, considered_pins=considered_pins)

    def test_validate_for_list_index__ValueIsListWithNoneEntry__RaisesValueError(self):
        # Arrange
        value = [GPIOPinState.LOW, None]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
        ]

        # Act & Assert
        expected_regex = rf'list value must be of type {GPIOPinState.__name__}. Found type \w* at position \d*'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_for_list_index(value=value, considered_pins=considered_pins)

    def test_validate_for_list_index__ValueIsListWithLesserSize__RaisesValueError(self):
        # Arrange
        value = [GPIOPinState.LOW, GPIOPinState.HIGH]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=1, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.IN),
        ]

        # Act & Assert
        expected_regex = rf'could not broadcast input array from size 2 into size 3'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_for_list_index(value=value, considered_pins=considered_pins)

    def test_validate_for_list_index__ValueIsListWithGreaterSize__RaisesValueError(self):
        # Arrange
        value = [GPIOPinState.LOW, GPIOPinState.HIGH]
        considered_pins = [
            _GPIOPin(idx=0, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
        ]

        # Act & Assert
        expected_regex = rf'could not broadcast input array from size 2 into size 1'
        with self.assertRaisesRegex(ValueError, expected_regex):
            GPIOPinBar._StateValueValidator._validate_for_list_index(value=value, considered_pins=considered_pins)


@patch.multiple(GPIOPinBar, __abstractmethods__=set())
class GPIOPinBarModeTests(ExtendedTestCase):
    class_path = f'{GPIOPinBar.__module__}.{GPIOPinBar.__name__}'

    @parameterized.expand([
        [2],
        [50],
        [slice(0, 30, 1)],
        [[1, 2]],
        [[2, 4, 30]],
        ['test'],
    ])
    @patch(f'{class_path}.{GPIOPinBar._IndexValidator.__name__}', wraps=GPIOPinBar._IndexValidator)
    def test_modes_getter__Always__CallsValidateIndexItem(self, item, index_validator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        try:
            _ = bar.modes[item]
        except (IndexError, TypeError):
            pass

        # Assert
        expected_parameters = {
            'item': item,
            'offset': bar._addressing_offset,
            'length': bar._addressing_array_length,
            'addressing': bar.addressing,
        }
        index_validator_mock.validate.assert_called_once_with(**expected_parameters)

    def test_modes_getter__IntIndexAddressingNotGPIOPin__ReturnsNone(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        mode_power = bar.modes[0]
        mode_ground = bar.modes[1]
        mode_other = bar.modes[5]

        # Assert
        self.assertIsNone(mode_power)
        self.assertIsNone(mode_ground)
        self.assertIsNone(mode_other)

    def test_modes_getter__IntIndexAddressingGPIOPin__ReturnsPinMode(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        mode = bar.modes[3]

        # Assert
        self.assertEqual(GPIOPinMode.OFF, mode)

    def test_modes_getter__IntIndexWithGPIOAddressing__ReturnsCorrectGPIOPinMode(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO
        bar._gpio_pins[0].mode = GPIOPinMode.OFF
        bar._gpio_pins[1].mode = GPIOPinMode.OUT
        bar._gpio_pins[2].mode = GPIOPinMode.IN

        # Act
        modes = bar.modes[2]

        # Assert
        expected = GPIOPinMode.IN
        self.assertEqual(expected, modes)

    def test_modes_getter__IntIndexWithOffset__ReturnsCorrectGPIOPinMode(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.PinBar)
        bar._gpio_pins[0].mode = GPIOPinMode.OFF
        bar._gpio_pins[1].mode = GPIOPinMode.OUT
        bar._gpio_pins[2].mode = GPIOPinMode.IN

        # Act
        modes = bar.modes[13]

        # Assert
        expected = GPIOPinMode.OUT
        self.assertEqual(expected, modes)

    def test_modes_getter__IntIndexWithOffsetAndGPIOAddressing__ReturnsCorrectGPIOPinMode(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO
        bar._gpio_pins[0].mode = GPIOPinMode.OFF
        bar._gpio_pins[1].mode = GPIOPinMode.OUT
        bar._gpio_pins[2].mode = GPIOPinMode.IN

        # Act
        modes = bar.modes[6]

        # Assert
        expected = GPIOPinMode.IN
        self.assertEqual(expected, modes)

    def test_modes_getter__SliceIndexAddressingNotGPIOPins__ReturnsNoneForNotGPIOPins(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        modes = bar.modes[:]

        # Assert
        expected = [None, None, GPIOPinMode.OFF, GPIOPinMode.OFF, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, modes)

    def test_modes_getter__SliceIndexWithGPIOAddressing__ReturnsOnlyCorrectGPIOPinModes(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO
        bar._gpio_pins[0].mode = GPIOPinMode.OFF
        bar._gpio_pins[1].mode = GPIOPinMode.OUT
        bar._gpio_pins[2].mode = GPIOPinMode.IN

        # Act
        modes = bar.modes[:]

        # Assert
        expected = [GPIOPinMode.OFF, GPIOPinMode.OUT, GPIOPinMode.IN]
        self.assertListEqual(expected, modes)

    def test_modes_getter__SliceIndexWithOffset__ReturnsCorrectGPIOPinModes(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.PinBar)
        bar._gpio_pins[0].mode = GPIOPinMode.OFF
        bar._gpio_pins[1].mode = GPIOPinMode.OUT
        bar._gpio_pins[2].mode = GPIOPinMode.IN

        # Act
        modes = bar.modes[11:14]

        # Assert
        expected = [None, GPIOPinMode.OFF, GPIOPinMode.OUT]
        self.assertListEqual(expected, modes)

    def test_modes_getter__SliceIndexWithOffsetAndGPIOAddressing__ReturnsOnlyCorrectGPIOPinModes(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO
        bar._gpio_pins[0].mode = GPIOPinMode.OFF
        bar._gpio_pins[1].mode = GPIOPinMode.OUT
        bar._gpio_pins[2].mode = GPIOPinMode.IN

        # Act
        modes = bar.modes[5:]

        # Assert
        expected = [GPIOPinMode.OUT, GPIOPinMode.IN]
        self.assertListEqual(expected, modes)

    def test_modes_getter__IntListIndexAddressingNotGPIOPins__ReturnsNoneForNotGPIOPins(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        modes = bar.modes[[5, 3, 0, 2, 1]]

        # Assert
        expected = [None, GPIOPinMode.OFF, None, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, modes)

    def test_modes_getter__IntListIndexWithGPIOAddressing__ReturnsOnlyCorrectGPIOPinModes(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO
        bar._gpio_pins[0].mode = GPIOPinMode.OFF
        bar._gpio_pins[1].mode = GPIOPinMode.OUT
        bar._gpio_pins[2].mode = GPIOPinMode.IN

        # Act
        modes = bar.modes[[2, 0, 1]]

        # Assert
        expected = [GPIOPinMode.IN, GPIOPinMode.OFF, GPIOPinMode.OUT]
        self.assertListEqual(expected, modes)

    def test_modes_getter__IntListIndexWithOffset__ReturnsCorrectGPIOPinModes(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.PinBar)
        bar._gpio_pins[0].mode = GPIOPinMode.OFF
        bar._gpio_pins[1].mode = GPIOPinMode.OUT
        bar._gpio_pins[2].mode = GPIOPinMode.IN

        # Act
        modes = bar.modes[[13, 10, 14]]

        # Assert
        expected = [GPIOPinMode.OUT, None, GPIOPinMode.IN]
        self.assertListEqual(expected, modes)

    def test_modes_getter__IntListIndexWithOffsetAndGPIOAddressing__ReturnsOnlyCorrectGPIOPinModes(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO
        bar._gpio_pins[0].mode = GPIOPinMode.OFF
        bar._gpio_pins[1].mode = GPIOPinMode.OUT
        bar._gpio_pins[2].mode = GPIOPinMode.IN

        # Act
        modes = bar.modes[[6, 4, 5]]

        # Assert
        expected = [GPIOPinMode.IN, GPIOPinMode.OFF, GPIOPinMode.OUT]
        self.assertListEqual(expected, modes)

    @parameterized.expand([
        [2],
        [50],
        [slice(0, 30, 1)],
        [[1, 2]],
        [[2, 4, 30]],
        ['test'],
    ])
    @patch(f'{class_path}.{GPIOPinBar._IndexValidator.__name__}', wraps=GPIOPinBar._IndexValidator)
    def test_modes_setter__Always__CallsValidateIndexItem(self, item, index_validator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        try:
            bar.modes[item] = GPIOPinMode.OFF
        except (IndexError, TypeError, PinBarError):
            pass

        # Assert
        expected_parameters = {
            'item': item,
            'offset': bar._addressing_offset,
            'length': bar._addressing_array_length,
            'addressing': bar.addressing,
        }
        index_validator_mock.validate.assert_called_once_with(**expected_parameters)

    @parameterized.expand([
        [GPIOPinMode.OUT],
        [[GPIOPinMode.OUT]],
        [[GPIOPinMode.OUT, GPIOPinMode.OFF]],
        ['test'],
    ])
    @patch(f'{class_path}.{GPIOPinBar._ModeValueValidator.__name__}',
           wraps=GPIOPinBar._ModeValueValidator)
    def test_modes_setter__Always__CallsValidateValue(self, value, value_validator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)

        # Act
        try:
            bar.modes[0] = value
        except (ValueError, TypeError, PinBarError):
            pass
        try:
            bar.modes[0:2] = value
        except (ValueError, TypeError, PinBarError):
            pass
        try:
            bar.modes[[0]] = value
        except (ValueError, TypeError, PinBarError):
            pass

        # Assert
        expected_calls = [
            call(value=value, index_type=int, considered_pins=bar._gpio_pins[0:1]),
            call(value=value, index_type=slice, considered_pins=bar._gpio_pins[0:2]),
            call(value=value, index_type=list, considered_pins=bar._gpio_pins[0:1]),
        ]
        value_validator_mock.validate.assert_has_calls(expected_calls)

    def test_modes_setter__IntIndexAddressingNotGPIOPin__RaisesPinTypeError(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act & Assert
        expected_regex = rf'pin is not of {PinType.__name__}.{PinType.GPIO} for pin idx \d*'
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            bar.modes[0] = GPIOPinMode.OUT
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            bar.modes[1] = GPIOPinMode.OUT
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            bar.modes[5] = GPIOPinMode.OUT

        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OFF, GPIOPinMode.OFF, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__IntIndexWithGPIOAddressing__ChangesCorrectPin(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO

        # Act
        bar.modes[1] = GPIOPinMode.OUT

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OFF, GPIOPinMode.OUT, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__IntIndexAddressingGPIOPin__ChangesPinMode(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        bar.modes[3] = GPIOPinMode.OUT

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OFF, GPIOPinMode.OUT, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__IntIndexWithOffset__ChangesCorrectPin(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.PinBar)

        # Act
        bar.modes[13] = GPIOPinMode.OUT

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OFF, GPIOPinMode.OUT, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__IntIndexWithOffsetAndGPIOAddressing__ChangesCorrectPin(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO

        # Act
        bar.modes[5] = GPIOPinMode.OUT

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OFF, GPIOPinMode.OUT, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__SliceIndexWithModeValue__ChangesAllAddressedGPIOPinModesToMode(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        bar.modes[:] = GPIOPinMode.OUT

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OUT, GPIOPinMode.OUT, GPIOPinMode.OUT, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__SliceIndexWithModeValueAndGPIOAddressing__ChangesAllAddressedGPIOPinModesToMode(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO

        # Act
        bar.modes[1:3] = GPIOPinMode.OUT

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OFF, GPIOPinMode.OUT, GPIOPinMode.OUT, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__SliceIndexWithListValue__ChangesGPIOPinModesToCorrespondingListEntry(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        bar.modes[1:] = [None, GPIOPinMode.OUT, GPIOPinMode.IN, GPIOPinMode.OFF, None]

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OUT, GPIOPinMode.IN, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__SliceIndexWithListValueAndGPIOAddressing__ChangesGPIOPinModesToCorrespondingListEntry(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO

        # Act
        bar.modes[1:3] = [GPIOPinMode.OUT, GPIOPinMode.IN]

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OFF, GPIOPinMode.OUT, GPIOPinMode.IN, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__SliceIndexWithOffset__ChangesCorrectPins(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.PinBar)

        # Act
        bar.modes[11:14] = GPIOPinMode.OUT

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OUT, GPIOPinMode.OUT, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__SliceIndexWithOffsetAndGPIOAddressing__ChangesCorrectPins(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO

        # Act
        bar.modes[5:6] = GPIOPinMode.OUT

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OFF, GPIOPinMode.OUT, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__IntListIndexAddressingNotGPIOPins__RaisesPinTypeError(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act & Assert
        expected_regex = rf'pin is not of {PinType.__name__}.{PinType.GPIO} for pin idx \d*'
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            bar.modes[[5, 3, 0, 2, 1]] = GPIOPinMode.OUT

        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OFF, GPIOPinMode.OFF, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__IntListIndexAddressingGPIOPins__NoPinTypeError(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act & Assert
        with self.assertNotRaised(PinTypeError):
            bar.modes[[3, 2]] = GPIOPinMode.OUT

    def test_modes_setter__IntListIndexWithModeValue__ChangesAllAddressedGPIOPinModesToMode(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        bar.modes[[3, 2]] = GPIOPinMode.OUT

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OUT, GPIOPinMode.OUT, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__IntListIndexWithModeValueAndGPIOAddressing__ChangesAllAddressedGPIOPinModesToMode(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO

        # Act
        bar.modes[[1, 2]] = GPIOPinMode.OUT

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OFF, GPIOPinMode.OUT, GPIOPinMode.OUT, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__IntListIndexWithListValue__ChangesGPIOPinModesToCorrespondingListEntry(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        bar.modes[[3, 2]] = [GPIOPinMode.OUT, GPIOPinMode.IN]

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.IN, GPIOPinMode.OUT, GPIOPinMode.OFF, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__IntListIndexWithListValueAndGPIOAddressing__ChangesGPIOPinModesToCorrespondingListEntry(
            self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO

        # Act
        bar.modes[[2, 1]] = [GPIOPinMode.OUT, GPIOPinMode.IN]

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OFF, GPIOPinMode.IN, GPIOPinMode.OUT, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__IntListIndexWithOffset__ChangesCorrectPins(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.PinBar)

        # Act
        bar.modes[[12, 14]] = GPIOPinMode.OUT

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OUT, GPIOPinMode.OFF, GPIOPinMode.OUT, None]
        self.assertListEqual(expected, actual)

    def test_modes_setter__IntListIndexWithOffsetAndGPIOAddressing__ChangesCorrectPins(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.GPIO)
        assert bar.addressing == PinAddressing.GPIO

        # Act
        bar.modes[[4, 6]] = GPIOPinMode.OUT

        # Assert
        actual = [pin.mode if isinstance(pin, _GPIOPin) else None for pin in bar._pins]
        expected = [None, None, GPIOPinMode.OUT, GPIOPinMode.OFF, GPIOPinMode.OUT, None]
        self.assertListEqual(expected, actual)


@patch.multiple(GPIOPinBar, __abstractmethods__=set())
class GPIOPinBarStateTests(ExtendedTestCase):
    class_path = f'{GPIOPinBar.__module__}.{GPIOPinBar.__name__}'

    @parameterized.expand([
        [2],
        [50],
        [slice(0, 30, 1)],
        [[1, 2]],
        [[2, 4, 30]],
        ['test'],
    ])
    @patch(f'{class_path}.{GPIOPinBar._IndexValidator.__name__}', wraps=GPIOPinBar._IndexValidator)
    def test_states_getter__Always__CallsValidateIndexItem(self, item, index_validator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        try:
            _ = bar.states[item]
        except (IndexError, TypeError, PinBarError):
            pass

        # Assert
        expected_parameters = {
            'item': item,
            'offset': bar._addressing_offset,
            'length': bar._addressing_array_length,
            'addressing': bar.addressing,
        }
        index_validator_mock.validate.assert_called_once_with(**expected_parameters)

    def test_states_getter__IntIndexAddressingNotGPIOPin__RaisesPinTypeError(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act & Assert
        expected_regex = rf'pin is not of {PinType.__name__}.{PinType.GPIO} for pin idx \d*'
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            _ = bar.states[0]
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            _ = bar.states[1]
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            _ = bar.states[5]

    def test_states_getter__IntIndexModeIsOff__RaisesModeIsOffError(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OFF

        # Act & Assert
        expected_regex = rf'cannot get state of gpio pin in {GPIOPinMode.OFF} for pin idx \d*'
        with self.assertRaisesRegex(ModeIsOffError, expected_regex):
            _ = bar.states[2]

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__IntIndexModeIsNotOff__CallsStateGeneratorAndReturnsMockData(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        state_generator_mock.return_value = iter([GPIOPinState.LOW])

        # Act
        state = bar.states[3]

        # Assert
        self.assertEqual(GPIOPinState.LOW, state)
        state_generator_mock.assert_called_once_with([bar._pins[3]])

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__IntIndexWithGPIOAddressing__CallsStateGeneratorAndReturnsMockData(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        state_generator_mock.return_value = iter([GPIOPinState.LOW])

        # Act
        state = bar.states[2]

        # Assert
        expected = GPIOPinState.LOW
        self.assertEqual(expected, state)
        state_generator_mock.assert_called_once_with([bar._gpio_pins[2]])

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__IntIndexWithOffset__CallsStateGeneratorWithCorrectPins(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        state_generator_mock.return_value = iter([GPIOPinState.LOW])

        # Act
        _ = bar.states[12]

        # Assert
        state_generator_mock.assert_called_once_with([bar._pins[2]])

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__IntIndexWithOffsetAndGPIOAddressing__CallsStateGeneratorWithCorrectPins(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        state_generator_mock.return_value = iter([GPIOPinState.LOW])

        # Act
        _ = bar.states[6]

        # Assert
        state_generator_mock.assert_called_once_with([bar._gpio_pins[2]])

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__SliceIndexAddressingNotGPIOPins__ReturnsNoneForNotGPIOPins(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        states = bar.states[:2]

        # Assert
        expected = [None, None]
        self.assertListEqual(expected, states)
        state_generator_mock.assert_called_once_with([])

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__SliceIndexModeIsOff__ReturnsNoneForModeOff(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        bar._gpio_pins[0].mode = GPIOPinMode.OFF
        bar._gpio_pins[1].mode = GPIOPinMode.OUT
        bar._gpio_pins[2].mode = GPIOPinMode.IN

        # Act
        states = bar.states[2:3]

        # Assert
        expected = [None]
        self.assertListEqual(expected, states)
        state_generator_mock.assert_called_once_with([])

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__SliceIndexModeIsNotOff__ReturnsNoneForNotGPIOPins(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        state_generator_mock.return_value = iter([GPIOPinState.LOW, GPIOPinState.HIGH, GPIOPinState.HIGH])

        # Act
        states = bar.states[2:5]

        # Assert
        expected = [GPIOPinState.LOW, GPIOPinState.HIGH, GPIOPinState.HIGH]
        self.assertListEqual(expected, states)
        state_generator_mock.assert_called_once_with(bar._pins[2:5])

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__SliceIndexWithGPIOAddressing__CallsStateGeneratorAndReturnsMockData(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        state_generator_mock.return_value = iter([GPIOPinState.LOW, GPIOPinState.HIGH])

        # Act
        state = bar.states[1:]

        # Assert
        expected = [GPIOPinState.LOW, GPIOPinState.HIGH]
        self.assertListEqual(expected, state)
        state_generator_mock.assert_called_once_with([bar._gpio_pins[1], bar._gpio_pins[2]])

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__SliceIndexWithOffset__CallsStateGeneratorWithCorrectPins(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        state_generator_mock.return_value = iter([GPIOPinState.LOW, GPIOPinState.HIGH])

        # Act
        _ = bar.states[12:14]

        # Assert
        state_generator_mock.assert_called_once_with([bar._pins[2], bar._pins[3]])

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__SliceIndexWithOffsetAndGPIOAddressing__CallsStateGeneratorWithCorrectPins(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        state_generator_mock.return_value = iter([GPIOPinState.LOW, GPIOPinState.HIGH])

        # Act
        _ = bar.states[5:]

        # Assert
        state_generator_mock.assert_called_once_with([bar._gpio_pins[1], bar._gpio_pins[2]])

    @parameterized.expand([
        [[0]],
        [[1]],
        [[5]],
        [[2, 3, 0, 4]],
    ])
    def test_states_getter__IntListIndexAddressingNotGPIOPins__RaisesPinTypeError(self, item: List[int]):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        assert isinstance(item, list)

        # Act
        expected_regex = rf'pin is not of {PinType.__name__}.{PinType.GPIO} for pin idx \d*'
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            _ = bar.states[[1, 5, 0]]

    def test_states_getter__IntListIndexModeIsOff__RaisesModeIsOffError(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        bar._gpio_pins[0].mode = GPIOPinMode.OFF
        bar._gpio_pins[1].mode = GPIOPinMode.OUT
        bar._gpio_pins[2].mode = GPIOPinMode.IN

        # Act & Assert
        expected_regex = rf'cannot get state of gpio pin in {GPIOPinMode.OFF} for pin idx \d*'
        with self.assertRaisesRegex(ModeIsOffError, expected_regex):
            _ = bar.states[[2]]

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__IntListIndexModeIsNotOff__CallsStateGeneratorAndReturnsMockData(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        state_generator_mock.return_value = iter([GPIOPinState.LOW, GPIOPinState.HIGH, GPIOPinState.HIGH])

        # Act
        states = bar.states[[3, 4, 2]]

        # Assert
        expected = [GPIOPinState.LOW, GPIOPinState.HIGH, GPIOPinState.HIGH]
        self.assertListEqual(expected, states)
        state_generator_mock.assert_called_once_with([bar._pins[3], bar._pins[4], bar._pins[2]])

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__IntListIndexWithGPIOAddressing__CallsStateGeneratorAndReturnsMockData(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        state_generator_mock.return_value = iter([GPIOPinState.LOW, GPIOPinState.HIGH])

        # Act
        state = bar.states[[2, 0]]

        # Assert
        expected = [GPIOPinState.LOW, GPIOPinState.HIGH]
        self.assertListEqual(expected, state)
        state_generator_mock.assert_called_once_with([bar._gpio_pins[2], bar._gpio_pins[0]])

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__IntListIndexWithOffset__CallsStateGeneratorWithCorrectPins(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        state_generator_mock.return_value = iter([GPIOPinState.LOW, GPIOPinState.HIGH])

        # Act
        _ = bar.states[[12, 14]]

        # Assert
        state_generator_mock.assert_called_once_with([bar._pins[2], bar._pins[4]])

    @patch(f'{class_path}.{GPIOPinBar._gpio_pin_states_iterator.__name__}')
    def test_states_getter__IntListIndexWithOffsetAndGPIOAddressing__CallsStateGeneratorWithCorrectPins(
            self, state_generator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        state_generator_mock.return_value = iter([GPIOPinState.LOW, GPIOPinState.HIGH])

        # Act
        _ = bar.states[[6, 4]]

        # Assert
        state_generator_mock.assert_called_once_with([bar._gpio_pins[2], bar._gpio_pins[0]])

    @parameterized.expand([
        [2],
        [50],
        [slice(0, 30, 1)],
        [[1, 2]],
        [[2, 4, 30]],
        ['test'],
    ])
    @patch(f'{class_path}.{GPIOPinBar._IndexValidator.__name__}', wraps=GPIOPinBar._IndexValidator)
    def test_states_setter__Always__CallsValidateIndexItem(self, item, index_validator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)

        # Act
        try:
            bar.states[item] = GPIOPinState.HIGH
        except (IndexError, TypeError, PinBarError):
            pass

        # Assert
        expected_parameters = {
            'item': item,
            'offset': bar._addressing_offset,
            'length': bar._addressing_array_length,
            'addressing': bar.addressing,
        }
        index_validator_mock.validate.assert_called_once_with(**expected_parameters)

    @parameterized.expand([
        [GPIOPinState.LOW],
        [[GPIOPinState.LOW]],
        [[GPIOPinState.LOW, GPIOPinState.HIGH]],
        ['test'],
    ])
    @patch(f'{class_path}.{GPIOPinBar._StateValueValidator.__name__}',
           wraps=GPIOPinBar._StateValueValidator)
    def test_states_setter__GPIOModesAreNotOff__CallsValidateValue(self, value, value_validator_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        try:
            bar.states[0] = value
        except (ValueError, TypeError, PinBarError):
            pass
        try:
            bar.states[0:2] = value
        except (ValueError, TypeError, PinBarError):
            pass
        try:
            bar.states[[0]] = value
        except (ValueError, TypeError, PinBarError):
            pass

        # Assert
        expected_calls = [
            call(value=value, index_type=int, considered_pins=bar._gpio_pins[0:1]),
            call(value=value, index_type=slice, considered_pins=bar._gpio_pins[0:2]),
            call(value=value, index_type=list, considered_pins=bar._gpio_pins[0:1]),
        ]
        self.assertEqual(3, value_validator_mock.validate.call_count)
        value_validator_mock.validate.assert_has_calls(expected_calls)

    def test_states_setter__IntIndexAddressingNotGPIOPin__RaisesPinTypeError(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act & Assert
        expected_regex = rf'pin is not of {PinType.__name__}.{PinType.GPIO} for pin idx \d*'
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            bar.states[0] = GPIOPinState.HIGH
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            bar.states[1] = GPIOPinState.HIGH
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            bar.states[5] = GPIOPinState.HIGH

    def test_states_setter__IntIndexModeIsOff__RaisesModeIsOffError(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OFF

        # Act & Assert
        expected_regex = rf'cannot get state of gpio pin in {GPIOPinMode.OFF} for pin idx \d*'
        with self.assertRaisesRegex(ModeIsOffError, expected_regex):
            bar.states[2] = GPIOPinState.HIGH

    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__IntIndexModeIsNotOff__CallsChangeStatesWithCorrectPin(
            self, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[3] = GPIOPinState.HIGH

        # Assert
        change_state_mock.assert_called_once_with([bar._pins[3]], [GPIOPinState.HIGH])

    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__IntIndexWithGPIOAddressing__CallsChangeStatesWithCorrectPins(
            self, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[2] = GPIOPinState.HIGH

        # Assert
        change_state_mock.assert_called_once_with([bar._gpio_pins[2]], [GPIOPinState.HIGH])

    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__IntIndexWithOffset__CallsChangeStatesWithCorrectPins(
            self, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[12] = GPIOPinState.HIGH

        # Assert
        change_state_mock.assert_called_once_with([bar._pins[2]], [GPIOPinState.HIGH])

    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__IntIndexWithOffsetAndGPIOAddressing__CallsChangeStatesWithCorrectPins(
            self, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[6] = GPIOPinState.HIGH

        # Assert
        change_state_mock.assert_called_once_with([bar._gpio_pins[2]], [GPIOPinState.HIGH])

    @parameterized.expand([
        [GPIOPinState.HIGH],
        [[None, None]],
    ])
    def test_states_setter__SliceIndexValueAddressingNotGPIOPins__AlwaysNoPinTypeError(
            self, value):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act & Assert
        with self.assertNotRaised(PinTypeError):
            bar.states[:2] = value

    @parameterized.expand([
        [GPIOPinState.HIGH],
        [[None, None, None]],
    ])
    def test_states_setter__SliceIndexModesAreOff__NoModeIsOffError(self, value):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OFF

        # Act & Assert
        with self.assertNotRaised(ModeIsOffError):
            bar.states[2:5] = value

    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__SliceIndexWithStateValueAddressingNotGPIOPins__EmptyCall(
            self, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[:2] = GPIOPinState.HIGH

        # Assert
        change_state_mock.assert_called_once_with([], [])

    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__SliceIndexWithStateValueModesAreOff__EmptyPinsCall(
            self, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OFF

        # Act & Assert
        with self.assertNotRaised(ModeIsOffError):
            bar.states[2:5] = GPIOPinState.HIGH

        change_state_mock.assert_called_once_with([], [])

    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__SliceIndexWithListValueAddressingNotGPIOPins__EmptyCall(
            self, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[:2] = [None, None]

        # Assert
        change_state_mock.assert_called_once_with([], [])

    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__SliceIndexWithListValueModesAreOff__EmptyCall(
            self, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OFF

        # Act & Assert
        with self.assertNotRaised(ModeIsOffError):
            bar.states[2:5] = [None, None, None]

        change_state_mock.assert_called_once_with([], [])

    @parameterized.expand([
        [GPIOPinState.HIGH],
        [[GPIOPinState.HIGH, GPIOPinState.LOW, GPIOPinState.HIGH]],
    ])
    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__SliceIndexWithModesAreNotOff__CallsChangeStatesWithCorrectPins(
            self, value, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[2:5] = value

        # Assert
        expected_value = value if isinstance(value, list) else [value, value, value]
        change_state_mock.assert_called_once_with(bar._pins[2:5], expected_value)

    @parameterized.expand([
        [GPIOPinState.HIGH],
        [[GPIOPinState.LOW, GPIOPinState.HIGH]],
    ])
    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__SliceIndexWithGPIOAddressing__CallsChangeStatesWithCorrectPins(
            self, value, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[1:] = value

        # Assert
        expected_value = value if isinstance(value, list) else [value, value]
        change_state_mock.assert_called_once_with(bar._gpio_pins[1:], expected_value)

    @parameterized.expand([
        [GPIOPinState.HIGH],
        [[GPIOPinState.HIGH, GPIOPinState.HIGH]],
    ])
    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__SliceIndexWithOffset__CallsChangeStatesWithCorrectPins(
            self, value, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[12:14] = value

        # Assert
        expected_value = value if isinstance(value, list) else [value, value]
        change_state_mock.assert_called_once_with(bar._pins[2:4], expected_value)

    @parameterized.expand([
        [GPIOPinState.LOW],
        [[GPIOPinState.LOW, GPIOPinState.LOW]],
    ])
    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__SliceIndexWithOffsetAndGPIOAddressing__CallsChangeStatesWithCorrectPins(
            self, value, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[5:] = value

        # Assert
        expected_value = value if isinstance(value, list) else [value, value]
        change_state_mock.assert_called_once_with(bar._gpio_pins[1:], expected_value)

    @parameterized.expand([
        [[0]],
        [[1]],
        [[5]],
        [[2, 3, 0, 4]],
    ])
    def test_states_setter__IntListIndexAddressingNotGPIOPins__RaisesPinTypeError(self, item: List[int]):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT
        assert isinstance(item, list)

        # Act
        expected_regex = rf'pin is not of {PinType.__name__}.{PinType.GPIO} for pin idx \d*'
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            bar.states[[1, 5, 0]] = GPIOPinState.HIGH

    def test_states_setter__IntListIndexAddressingNotGPIOPinWithNoneValue__RaisesPinTypeError(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        expected_regex = rf'pin is not of {PinType.__name__}.{PinType.GPIO} for pin idx \d*'
        with self.assertRaisesRegex(PinTypeError, expected_regex):
            bar.states[[1, 5]] = [None, None]

    def test_states_setter__IntListIndexModeIsOff__RaisesModeIsOffError(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        bar._gpio_pins[0].mode = GPIOPinMode.OFF
        bar._gpio_pins[1].mode = GPIOPinMode.OUT
        bar._gpio_pins[2].mode = GPIOPinMode.IN

        # Act & Assert
        expected_regex = rf'cannot get state of gpio pin in {GPIOPinMode.OFF} for pin idx \d*'
        with self.assertRaisesRegex(ModeIsOffError, expected_regex):
            bar.states[[2]] = GPIOPinState.HIGH

    @parameterized.expand([
        [GPIOPinState.HIGH],
        [[GPIOPinState.HIGH, GPIOPinState.LOW, GPIOPinState.HIGH]],
    ])
    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__IntListIndexModeIsNotOff__CallsChangeStatesWithCorrectPins(
            self, value, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[[3, 4, 2]] = value

        # Assert
        expected_pins = [bar._pins[3], bar._pins[4], bar._pins[2]]
        expected_value = value if isinstance(value, list) else [value, value, value]
        change_state_mock.assert_called_once_with(expected_pins, expected_value)

    @parameterized.expand([
        [GPIOPinState.HIGH],
        [[GPIOPinState.HIGH, GPIOPinState.LOW]],
    ])
    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__IntListIndexWithGPIOAddressing__CallsChangeStatesWithCorrectPins(
            self, value, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[[2, 0]] = value

        # Assert
        expected_pins = [bar._gpio_pins[2], bar._gpio_pins[0]]
        expected_value = value if isinstance(value, list) else [value, value]
        change_state_mock.assert_called_once_with(expected_pins, expected_value)

    @parameterized.expand([
        [GPIOPinState.HIGH],
        [[GPIOPinState.HIGH, GPIOPinState.LOW]],
    ])
    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__IntListIndexWithOffset__CallsChangeStatesWithCorrectPins(
            self, value, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.PinBar)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[[12, 14]] = value

        # Assert
        expected_pins = [bar._pins[2], bar._pins[4]]
        expected_value = value if isinstance(value, list) else [value, value]
        change_state_mock.assert_called_once_with(expected_pins, expected_value)

    @parameterized.expand([
        [GPIOPinState.HIGH],
        [[GPIOPinState.HIGH, GPIOPinState.LOW]],
    ])
    @patch(f'{class_path}.{GPIOPinBar._change_gpio_pin_states.__name__}')
    def test_states_setter__IntListIndexWithOffsetAndGPIOAddressing__CallsChangeStatesWithCorrectPins(
            self, value, change_state_mock: MagicMock):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBar(pin_assignment, idx_offset=10, gpio_idx_offset=4, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.states[[6, 4]] = value

        # Assert
        expected_pins = [bar._gpio_pins[2], bar._gpio_pins[0]]
        expected_value = value if isinstance(value, list) else [value, value]
        change_state_mock.assert_called_once_with(expected_pins, expected_value)


class GPIOPinBarEmulatorTests(unittest.TestCase):
    class_path = f'{GPIOPinBarEmulator.__module__}.GPIOPinBarEmulator'

    def test_init__EmptyPinAssignment__SetEmptyStatesList(self):
        # Arrange & Act
        bar = GPIOPinBarEmulator([], initial_addressing=PinAddressing.GPIO)

        # Assert
        self.assertListEqual(bar.pin_assignment, [])
        self.assertListEqual(bar._gpio_states, [])
        self.assertEqual(len(bar), 0)

    def test_init__NoGPIOPinAssignment__SetEmptyStatesList(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.OTHER,
        ]

        # Act
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)

        # Assert
        self.assertListEqual(bar.pin_assignment, pin_assignment)
        self.assertListEqual(bar._gpio_states, [])
        self.assertEqual(len(bar), 3)

    def test_init__OneGPIOPinAssignment__SetOneSizedStatesList(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.OTHER,
        ]
        expected_gpio_states = [None]

        # Act
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)

        # Assert
        self.assertListEqual(bar.pin_assignment, pin_assignment)
        self.assertListEqual(bar._gpio_states, expected_gpio_states)
        self.assertEqual(len(bar), 4)

    def test_init__MultipleGPIOPinAssignment__SetMultipleSizedStatesList(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        expected_gpio_states = [None, None, None]

        # Act
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)

        # Assert
        self.assertListEqual(bar.pin_assignment, pin_assignment)
        self.assertListEqual(bar._gpio_states, expected_gpio_states)
        self.assertEqual(len(bar), 6)

    def test_change_pin_modes__ChangeToOff__ModesChangedAndSetStatesToNone(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=3, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
            _GPIOPin(idx=4, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.OFF),
        ]
        modes_iter = iter([GPIOPinMode.OFF, GPIOPinMode.OFF, GPIOPinMode.OFF])

        previous_states = [GPIOPinState.HIGH, GPIOPinState.LOW, None]
        bar._gpio_states = previous_states
        assert bar._gpio_states == previous_states

        # Act
        bar._change_pin_modes(pins, modes_iter)

        # Assert
        expected_modes = [GPIOPinMode.OFF, GPIOPinMode.OFF, GPIOPinMode.OFF]
        actual_modes = [pin.mode for pin in pins]
        expected_gpio_states = [None, None, None]

        self.assertListEqual(expected_modes, actual_modes)
        self.assertListEqual(bar._gpio_states, expected_gpio_states)

    def test_change_pin_modes__ChangeToOut__ModesChangedAndSetStatesOfPreviousPinsWithOffModeToLow(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=3, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
            _GPIOPin(idx=4, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.OFF),
        ]
        modes_iter = iter([GPIOPinMode.OUT, GPIOPinMode.OUT, GPIOPinMode.OUT])

        previous_states = [GPIOPinState.HIGH, GPIOPinState.LOW, None]
        bar._gpio_states = previous_states
        assert bar._gpio_states == previous_states

        # Act
        bar._change_pin_modes(pins, modes_iter)

        # Assert
        expected_modes = [GPIOPinMode.OUT, GPIOPinMode.OUT, GPIOPinMode.OUT]
        actual_modes = [pin.mode for pin in pins]
        expected_gpio_states = [GPIOPinState.HIGH, GPIOPinState.LOW, GPIOPinState.LOW]

        self.assertListEqual(expected_modes, actual_modes)
        self.assertListEqual(bar._gpio_states, expected_gpio_states)

    def test_change_pin_modes__ChangeToIn__ModesChangedAndSetStatesOfPreviousPinsWithOffModeToLow(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=3, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
            _GPIOPin(idx=4, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.OFF),
        ]
        modes_iter = iter([GPIOPinMode.IN, GPIOPinMode.IN, GPIOPinMode.IN])

        previous_states = [GPIOPinState.HIGH, GPIOPinState.LOW, None]
        bar._gpio_states = previous_states
        assert bar._gpio_states == previous_states

        # Act
        bar._change_pin_modes(pins, modes_iter)

        # Assert
        expected_modes = [GPIOPinMode.IN, GPIOPinMode.IN, GPIOPinMode.IN]
        actual_modes = [pin.mode for pin in pins]
        expected_gpio_states = [GPIOPinState.HIGH, GPIOPinState.LOW, GPIOPinState.LOW]

        self.assertListEqual(expected_modes, actual_modes)
        self.assertListEqual(bar._gpio_states, expected_gpio_states)

    def test_gpio_pin_states_iterator__Always__ReturnsIteratorIteratingOverCorrectPinStates(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=3, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
            _GPIOPin(idx=4, type=PinType.GPIO, gpio_idx=2, mode=GPIOPinMode.OFF),
        ]

        previous_states = [GPIOPinState.HIGH, GPIOPinState.LOW, None]
        bar._gpio_states = previous_states
        assert bar._gpio_states == previous_states

        # Act
        state_iterator = bar._gpio_pin_states_iterator(pins)

        # Assert
        expected_states = [GPIOPinState.HIGH, GPIOPinState.LOW, None]
        actual_states = [state for state in state_iterator]
        self.assertListEqual(expected_states, actual_states)

    def test_state_getter__IntIndex__ReturnsCorrectState(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        previous_states = [GPIOPinState.HIGH, GPIOPinState.LOW, None]
        bar._gpio_states = previous_states

        # Act
        state = bar.states[1]

        # Assert
        self.assertEqual(GPIOPinState.LOW, state)

    def test_state_getter__SliceIndex__ReturnsCorrectStates(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        previous_states = [GPIOPinState.HIGH, GPIOPinState.LOW, None]
        bar._gpio_states = previous_states

        # Act
        states = bar.states[:]

        # Assert
        expected_states = [GPIOPinState.HIGH, GPIOPinState.LOW, None]
        self.assertListEqual(expected_states, states)

    def test_state_getter__ListIndex__ReturnsCorrectStates(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        previous_states = [GPIOPinState.HIGH, GPIOPinState.LOW, None]
        bar._gpio_states = previous_states

        # Act
        states = bar.states[[1, 2, 0]]

        # Assert
        expected_states = [GPIOPinState.LOW, None, GPIOPinState.HIGH]
        self.assertListEqual(expected_states, states)

    def test_change_gpio_pin_states__Always__SetNewStatesForGivenPins(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        pins = [
            _GPIOPin(idx=2, type=PinType.GPIO, gpio_idx=0, mode=GPIOPinMode.OUT),
            _GPIOPin(idx=3, type=PinType.GPIO, gpio_idx=1, mode=GPIOPinMode.IN),
        ]

        previous_states = [GPIOPinState.HIGH, GPIOPinState.LOW, None]
        bar._gpio_states = previous_states
        assert bar._gpio_states == previous_states

        # Act
        bar._change_gpio_pin_states(pins, [GPIOPinState.LOW, GPIOPinState.HIGH])

        # Assert
        expected_states = [GPIOPinState.LOW, GPIOPinState.HIGH, None]
        self.assertListEqual(expected_states, bar._gpio_states)

    def test_state_setter__IntIndex__SetNewStateForCorrectPin(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        previous_states = [GPIOPinState.LOW, GPIOPinState.LOW, GPIOPinState.LOW]
        bar._gpio_states = previous_states

        # Act
        bar.states[1] = GPIOPinState.HIGH

        # Assert
        expected_states = [GPIOPinState.LOW, GPIOPinState.HIGH, GPIOPinState.LOW]
        self.assertListEqual(expected_states, bar._gpio_states)

    def test_state_setter__SliceIndex__SetNewStatesForCorrectPins(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        previous_states = [GPIOPinState.LOW, GPIOPinState.LOW, GPIOPinState.LOW]
        bar._gpio_states = previous_states

        # Act
        bar.states[1:] = GPIOPinState.HIGH

        # Assert
        expected_states = [GPIOPinState.LOW, GPIOPinState.HIGH, GPIOPinState.HIGH]
        self.assertListEqual(expected_states, bar._gpio_states)

    def test_state_setter__ListIndex__SetNewStatesForCorrectPins(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        previous_states = [GPIOPinState.LOW, GPIOPinState.LOW, GPIOPinState.LOW]
        bar._gpio_states = previous_states

        # Act
        bar.states[[1, 2]] = GPIOPinState.HIGH

        # Assert
        expected_states = [GPIOPinState.LOW, GPIOPinState.HIGH, GPIOPinState.HIGH]
        self.assertListEqual(expected_states, bar._gpio_states)

    def test_emulated_gpio_modes_getter__IntIndex__ReturnsCorrectMode(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        modes = bar.emulated_gpio_modes[1]

        # Assert
        expected_modes = GPIOPinMode.OUT
        self.assertEqual(expected_modes, modes)

    def test_emulated_gpio_modes_getter__SliceIndex__ReturnsCorrectModes(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        modes = bar.emulated_gpio_modes[1:]

        # Assert
        expected_modes = [GPIOPinMode.OUT, GPIOPinMode.OUT]
        self.assertListEqual(expected_modes, modes)

    def test_emulated_gpio_modes_setter__IntIndex__SetModeCorrectly(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.emulated_gpio_modes[1] = GPIOPinMode.IN

        # Assert
        expected_modes = [GPIOPinMode.OUT, GPIOPinMode.IN, GPIOPinMode.OUT]
        actual_modes = [pin.mode for pin in bar._gpio_pins]
        self.assertEqual(expected_modes, actual_modes)

    def test_emulated_gpio_modes_setter__SliceIndex__SetModesCorrectly(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        for pin in bar._gpio_pins:
            pin.mode = GPIOPinMode.OUT

        # Act
        bar.emulated_gpio_modes[1:] = GPIOPinMode.IN

        # Assert
        expected_modes = [GPIOPinMode.OUT, GPIOPinMode.IN, GPIOPinMode.IN]
        actual_modes = [pin.mode for pin in bar._gpio_pins]
        self.assertEqual(expected_modes, actual_modes)

    def test_emulated_gpio_states_getter__IntIndex__ReturnsCorrectState(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        bar._gpio_states = [GPIOPinState.LOW, GPIOPinState.HIGH, None]

        # Act
        state = bar.emulated_gpio_states[1]

        # Assert
        expected_state = GPIOPinState.HIGH
        self.assertEqual(expected_state, state)

    def test_emulated_gpio_states_getter__SliceIndex__ReturnsCorrectStates(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        bar._gpio_states = [GPIOPinState.LOW, GPIOPinState.HIGH, None]

        # Act
        states = bar.emulated_gpio_states[1:]

        # Assert
        expected_states = [GPIOPinState.HIGH, None]
        self.assertListEqual(expected_states, states)

    def test_emulated_gpio_states_setter__IntIndex__SetStateCorrectly(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        bar._gpio_states = [GPIOPinState.LOW, GPIOPinState.HIGH, None]

        # Act
        bar.emulated_gpio_states[1] = GPIOPinState.LOW

        # Assert
        expected_states = [GPIOPinState.LOW, GPIOPinState.LOW, None]
        self.assertEqual(expected_states, bar._gpio_states)

    def test_emulated_gpio_states_setter__SliceIndex__SetStatesCorrectly(self):
        # Arrange
        pin_assignment = [
            PinType.POWER,
            PinType.GROUND,
            PinType.GPIO,
            PinType.GPIO,
            PinType.GPIO,
            PinType.OTHER,
        ]
        bar = GPIOPinBarEmulator(pin_assignment, initial_addressing=PinAddressing.GPIO)
        bar._gpio_states = [GPIOPinState.LOW, GPIOPinState.HIGH, None]

        # Act
        bar.emulated_gpio_states[1:] = [GPIOPinState.LOW, GPIOPinState.LOW]

        # Assert
        expected_states = [GPIOPinState.LOW, GPIOPinState.LOW, GPIOPinState.LOW]
        self.assertEqual(expected_states, bar._gpio_states)

