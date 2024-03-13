from abc import ABC, abstractmethod
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, unique
from operator import itemgetter
from types import NoneType
from typing import List, Union, Optional, Any, Iterable, Iterator

from gpiowrapper.util import IndexableProperty, replace_none_in_slice, subtract_offset_from_slice


# TODO doc


@unique
class PinAddressing(Enum):
    PinBar = 'PinBar'
    GPIO = 'GPIO'

    def __str__(self):
        return self.value


@unique
class GPIOLibrary(Enum):
    Emulator = 'Emulator'
    RPi_GPIO = 'RPi_GPIO'

    def __str__(self):
        return self.value


@unique
class GPIOBoardType(Enum):
    RASPI_40_PIN = 'RASPI_40_PIN'

    def __str__(self):
        return self.value


@unique
class PinType(Enum):
    POWER = 0
    GROUND = 1
    GPIO = 2
    OTHER = 3


@unique
class GPIOPinState(Enum):
    LOW = 0
    HIGH = 1


@unique
class GPIOPinMode(Enum):
    OFF = 0
    IN = 1
    IN_PULL_DOWN = 2
    IN_PULL_UP = 3
    OUT = 4


@dataclass(slots=True, kw_only=True)
class _Pin:
    idx: int
    type: PinType


@dataclass(slots=True, kw_only=True)
class _GPIOPin(_Pin):
    gpio_idx: int
    mode: GPIOPinMode = GPIOPinMode.OFF


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


class PinBar(ABC):
    def __init__(self, pin_assignment: List[PinType], idx_offset: int = 0):
        self._pins: List[_Pin] = [_Pin(idx=i + idx_offset, type=type) for i, type in enumerate(pin_assignment)]
        self._idx_offset: int = idx_offset

    @property
    def pin_assignment(self) -> List[PinType]:
        return [pin.type for pin in self._pins]

    @property
    def idx_offset(self) -> int:
        return self._idx_offset

    def __len__(self) -> int:
        return len(self._pins)


class GPIOPinBar(PinBar, ABC):

    def __init__(
            self,
            pin_assignment: List[PinType],
            initial_addressing: PinAddressing,
            idx_offset: int = 0,
            gpio_order_from_ids: List[int] = None,
            gpio_idx_offset: int = 0
    ):
        super().__init__(pin_assignment=pin_assignment, idx_offset=idx_offset)
        self._gpio_idx_offset: int = gpio_idx_offset

        self._convert_gpio_types_in_pins_list(gpio_order_from_ids)
        self._gpio_pins: List[_GPIOPin] = [pin for pin in self._pins if isinstance(pin, _GPIOPin)]
        self._gpio_pins.sort(key=lambda x: x.gpio_idx)

        self.addressing = initial_addressing

    def _convert_gpio_types_in_pins_list(self, gpio_order_from_ids):
        gpio_pin_indices = [i for i, pin in enumerate(self._pins) if pin.type is PinType.GPIO]
        gpio_order_indices = [i - self._idx_offset for i in
                              gpio_order_from_ids] if gpio_order_from_ids is not None else None

        if gpio_order_indices is not None and not sorted(gpio_order_indices) == gpio_pin_indices:
            raise ValueError(f'gpio_order_from_ids parameter is invalid! '
                             'Check if you are missing a gpio pin or have duplicates.')

        order = gpio_pin_indices if gpio_order_indices is None else gpio_order_indices
        for i, index in enumerate(order):
            pin = self._pins[index]
            self._pins[index] = _GPIOPin(idx=pin.idx, type=PinType.GPIO,
                                         gpio_idx=i + self._gpio_idx_offset, mode=GPIOPinMode.OFF)

    @property
    def gpio_idx_offset(self) -> int:
        return self._gpio_idx_offset

    @property
    def num_gpio_pins(self) -> int:
        """
        :return: The number of GPIO Pins
        """
        return len(self._gpio_pins)

    @property
    def addressing(self) -> PinAddressing:
        return self._addressing

    @addressing.setter
    def addressing(self, new_addressing: PinAddressing):
        if new_addressing not in [PinAddressing.PinBar, PinAddressing.GPIO]:
            raise ValueError(f'{new_addressing} is not supported!')

        self._addressing = new_addressing
        self._addressing_array = self._pins if self.addressing is PinAddressing.PinBar else self._gpio_pins
        self._addressing_offset = self.idx_offset if self.addressing is PinAddressing.PinBar else self.gpio_idx_offset
        self._addressing_array_length = len(self) if self.addressing is PinAddressing.PinBar else self.num_gpio_pins

    @property
    def current_idx_offset(self):
        """
        Returns the idx starting offset for the current PinAddressing.
        :return: The idx_offset for PinAddressing.PinBar or the gpio_idx_offset for PinAddressing.GPIO .
        """
        return self._addressing_offset

    @property
    def current_num_addressable_pins(self):
        """
        Returns the number of pins which are addressable for the current PinAddressing.
        :return: The __len__(self) for PinAddressing.PinBar or the num_gpio_pins for PinAddressing.GPIO .
        """
        return self._addressing_array_length

    class _IndexValidator:
        @classmethod
        def _validation_mapping(cls) -> dict:
            return {
                int: cls.validate_int_index,
                slice: cls.validate_slice_index,
                list: cls.validate_list_index,
            }

        @classmethod
        def validate(
                cls,
                item: Any,
                offset: int,
                length: int,
                addressing: PinAddressing
        ):
            cls.validate_index_type(type(item))
            validation_func = cls._validation_mapping()[type(item)]

            if validation_func is not None:
                # noinspection PyArgumentList
                validation_func(item=item, offset=offset, length=length, addressing=addressing)

        @classmethod
        def validate_index_type(cls, item_type):
            if item_type not in [int, slice, list]:
                raise TypeError(f'index must be integer, slice or list, not {item_type.__name__}')

        @classmethod
        def validate_int_index(cls, item: int, offset: int, length: int, addressing: PinAddressing, **_):
            if not offset <= item < offset + length:
                raise IndexError(f'index out of range for {PinAddressing.__name__}.{str(addressing)}')

        @classmethod
        def validate_slice_index(cls, item: slice, **_):
            if (
                    (item.start is not None and not isinstance(item.start, int)) or
                    (item.stop is not None and not isinstance(item.stop, int)) or
                    (item.step is not None and not isinstance(item.step, int))
            ):
                raise TypeError(f'slice indices must be integers or None or have an __index__ method')

        @classmethod
        def validate_list_index(cls, item: list, offset: int, length: int, addressing: PinAddressing, **_):
            for i, index in enumerate(item):
                if isinstance(index, int):
                    try:
                        cls.validate_int_index(index, offset, length, addressing)
                    except IndexError:
                        raise IndexError(
                            f'index out of range for {PinAddressing.__name__}.{str(addressing)} at position {i}'
                        ) from None
                else:
                    raise TypeError(f'list indices must be integers or have an __index__ method. '
                                    f'Found type {type(index).__name__} at position {i}')

    class _ValueValidator(ABC):
        @classmethod
        def _validation_mapping(cls):
            return {
                int: cls._validate_for_int_index,
                slice: cls._validate_for_slice_index,
                list: cls._validate_for_list_index,
            }

        @classmethod
        def validate(cls, value, index_type, considered_pins: List[_Pin]):
            cls._validate_type(type(value))

            validation_func = cls._validation_mapping()[index_type]
            if validation_func is not None:
                # noinspection PyArgumentList
                validation_func(value=value, considered_pins=considered_pins)

        @classmethod
        @abstractmethod
        def _validate_type(cls, value_type):
            pass

        @classmethod
        def _validate_for_int_index(cls, value, **_):
            if isinstance(value, list):
                raise ValueError('setting an array element with a sequence.')

        @classmethod
        def _validate_for_slice_index(cls, value, considered_pins: List[_Pin], **_):
            if isinstance(value, list):
                cls._validate_list_size(considered_pins, value)
                cls._validate_list_entries(value, considered_pins, none_allowed=True)

        @classmethod
        def _validate_for_list_index(cls, value, considered_pins: List[_Pin], **_):
            if isinstance(value, list):
                cls._validate_list_size(considered_pins, value)
                cls._validate_list_entries(value, considered_pins, none_allowed=False)

        @classmethod
        def _validate_list_size(cls, considered_pins, value):
            if len(value) is not len(considered_pins):
                raise ValueError(
                    f'could not broadcast input array from size {len(value)} into size {len(considered_pins)}')

        @classmethod
        def _validate_list_entries(cls, value, considered_pins: List[_Pin], none_allowed: bool):
            value_pin_zip = zip(value, considered_pins)
            allowed_entry_types = cls._allowed_list_entry_types()
            if none_allowed:
                allowed_entry_types.append(NoneType)

            for i, (v, pin) in enumerate(value_pin_zip):
                if type(v) not in allowed_entry_types:
                    allowed_entry_type_names = [i.__name__ for i in allowed_entry_types]
                    msg = (f'list value must be of type {", ".join(allowed_entry_type_names)}. '
                           f'Found type {type(v).__name__} at position {i}')
                    raise ValueError(msg)

                if (v is None and isinstance(pin, _GPIOPin)) or (v is not None and not isinstance(pin, _GPIOPin)):
                    msg = f'unable to assign {v} at position {i} to pin of type {pin.type}'
                    raise PinTypeError(msg)

        @classmethod
        @abstractmethod
        def _allowed_list_entry_types(cls) -> List:
            pass

    class _ModeValueValidator(_ValueValidator):
        @classmethod
        def _validation_mapping(cls):
            return {
                int: cls._validate_for_int_index,
                slice: cls._validate_for_slice_index,
                list: cls._validate_for_list_index,
            }

        @classmethod
        def _validate_type(cls, value_type):
            if value_type not in [GPIOPinMode, list]:
                raise TypeError(f'value must be {GPIOPinMode.__name__} or list, not {value_type.__name__}')

        @classmethod
        def _allowed_list_entry_types(cls) -> List:
            return [GPIOPinMode]

    class _StateValueValidator(_ValueValidator):
        @classmethod
        def _validate_type(cls, value_type):
            if value_type not in [GPIOPinState, list]:
                raise TypeError(f'value must be {GPIOPinState.__name__} or list, not {value_type.__name__}')

        @classmethod
        def _validate_list_entries(cls, value, considered_pins: List[_Pin], none_allowed: bool):
            value_pin_zip = zip(value, considered_pins)
            allowed_entry_types = cls._allowed_list_entry_types()
            if none_allowed:
                allowed_entry_types.append(NoneType)

            for i, (v, pin) in enumerate(value_pin_zip):
                if type(v) not in allowed_entry_types:
                    allowed_entry_type_names = [i.__name__ for i in allowed_entry_types]
                    msg = (f'list value must be of type {", ".join(allowed_entry_type_names)}. '
                           f'Found type {type(v).__name__} at position {i}')
                    raise ValueError(msg)

                '''
                v: GPIOPinState, pin: NoGPIO => PinTypeError
                v: GPIOPinState, pin: GPIO, mode: off => ModeIsOffError
                v: GPIOPinState, pin: GPIO, mode: on => NoError
                v: None, pin: NoGPIO => NoError
                v: None, pin: GPIO, mode: off => NoError
                v: None, pin: GPIO, mode: on => ValueError
                '''

                msg = f'unable to assign {v} at position {i} to pin of type {pin.type}'
                msg = f'{msg} with {pin.mode}' if isinstance(pin, _GPIOPin) else msg

                if v is not None and not isinstance(pin, _GPIOPin):
                    raise PinTypeError(msg)
                elif v is not None and isinstance(pin, _GPIOPin) and pin.mode is GPIOPinMode.OFF:
                    raise ModeIsOffError(msg)
                elif v is None and isinstance(pin, _GPIOPin) and pin.mode is not GPIOPinMode.OFF:
                    raise ValueError(msg)

        @classmethod
        def _allowed_list_entry_types(cls) -> List:
            return [GPIOPinState]

    @IndexableProperty
    def modes(self, item) -> Union[Optional[GPIOPinMode], List[Optional[GPIOPinMode]]]:
        self._IndexValidator.validate(item=item, offset=self._addressing_offset,
                                      length=self._addressing_array_length, addressing=self.addressing)

        item_pins = self._get_pins(item=item)

        if isinstance(item_pins, list):
            return [pin.mode if isinstance(pin, _GPIOPin) else None for pin in item_pins]
        else:
            return item_pins.mode if isinstance(item_pins, _GPIOPin) else None

    @modes.itemsetter
    def modes(self, key, value: Union[GPIOPinMode, List[Optional[GPIOPinMode]]]) -> None:
        self._IndexValidator.validate(item=key, offset=self._addressing_offset,
                                      length=self._addressing_array_length, addressing=self.addressing)

        item_pins = self._get_pins(item=key)
        item_pins = [item_pins] if not isinstance(item_pins, list) else item_pins

        if not isinstance(key, slice):
            self._validate_pins_are_gpio(item_pins)

        self._ModeValueValidator.validate(value=value, index_type=type(key), considered_pins=item_pins)

        if isinstance(value, list):
            value = [v for v in value if v is not None]

        item_pins = [pin for pin in item_pins if isinstance(pin, _GPIOPin)]
        value_it = iter(lambda: value, -1) if isinstance(value, GPIOPinMode) else iter(value)

        self._change_pin_modes(item_pins, value_it)

    def _change_pin_modes(self, pins: List[_GPIOPin], new_modes_iterator: Iterator[GPIOPinMode]):
        for pin in pins:
            pin.mode = next(new_modes_iterator)

    @IndexableProperty
    def states(self, item) -> Union[Optional[GPIOPinState], List[Optional[GPIOPinState]]]:
        self._IndexValidator.validate(item=item, offset=self._addressing_offset,
                                      length=self._addressing_array_length, addressing=self.addressing)

        item_pins = self._get_pins(item=item)
        item_pins = [item_pins] if not isinstance(item_pins, list) else item_pins
        gpio_pins = [pin for pin in item_pins if isinstance(pin, _GPIOPin)]

        if not isinstance(item, slice):
            self._validate_pins_are_gpio(item_pins)
            self._validate_gpio_pin_modes_not_off(gpio_pins)
        else:
            gpio_pins = [pin for pin in gpio_pins if pin.mode is not GPIOPinMode.OFF]

        state_iterator = self._gpio_pin_states_iterator(gpio_pins)
        if isinstance(item, int):
            return next(state_iterator)
        else:
            return [next(state_iterator) if isinstance(pin, _GPIOPin) and pin.mode is not GPIOPinMode.OFF else None
                    for pin in item_pins]

    @abstractmethod
    def _gpio_pin_states_iterator(self, pins: List[_GPIOPin]) -> Iterator[Optional[GPIOPinState]]:
        pass

    @states.itemsetter
    def states(self, key, value: Union[GPIOPinState, List[Optional[GPIOPinState]]]) -> None:
        self._IndexValidator.validate(item=key, offset=self._addressing_offset,
                                      length=self._addressing_array_length, addressing=self.addressing)

        item_pins = self._get_pins(item=key)
        item_pins = [item_pins] if not isinstance(item_pins, list) else item_pins
        gpio_pins = [pin for pin in item_pins if isinstance(pin, _GPIOPin)]

        if not isinstance(key, slice):
            self._validate_pins_are_gpio(item_pins)
            self._validate_gpio_pin_modes_not_off(gpio_pins)

        self._StateValueValidator.validate(value=value, index_type=type(key), considered_pins=item_pins)

        if isinstance(key, slice):
            gpio_pins = [pin for pin in gpio_pins if pin.mode is not GPIOPinMode.OFF]
        if isinstance(value, GPIOPinState):
            value = [value for _ in gpio_pins]
        elif isinstance(value, list):
            value = [v for v in value if v is not None]

        self._change_gpio_pin_states(gpio_pins, value)

    @abstractmethod
    def _change_gpio_pin_states(self, pins: List[_GPIOPin], new_states: List[GPIOPinState]) -> None:
        pass

    def _get_pins(self, item: Union[int, slice, list]) -> Union[_Pin, List[_Pin]]:
        if isinstance(item, int):
            return self._addressing_array[item - self._addressing_offset]

        elif isinstance(item, slice):
            item = replace_none_in_slice(item=item)
            item = subtract_offset_from_slice(item=item, offset=self._addressing_offset)
            return self._addressing_array[item]

        elif isinstance(item, list):
            item = [i - self._addressing_offset for i in item]
            pins = itemgetter(*item)(self._addressing_array)
            return list(pins) if isinstance(pins, Iterable) else [pins]

    @staticmethod
    def _validate_pins_are_gpio(item_pins: Iterable[_Pin]):
        for pin in item_pins:
            if not isinstance(pin, _GPIOPin):
                raise PinTypeError(f'pin is not of {PinType.__name__}.{PinType.GPIO} for pin idx {pin.idx}')

    @staticmethod
    def _validate_gpio_pin_modes_not_off(gpio_pins: Iterable[_GPIOPin]):
        for pin in gpio_pins:
            if pin.mode is GPIOPinMode.OFF:
                raise ModeIsOffError(f'cannot get state of gpio pin in {GPIOPinMode.OFF} for pin idx {pin.idx}')

    def reset_gpio_pins(self):
        self.modes[:] = GPIOPinMode.OFF


class GPIOPinBarEmulator(GPIOPinBar):
    def __init__(
            self,
            pin_assignment: List[PinType],
            initial_addressing: PinAddressing,
            idx_offset: int = 0,
            gpio_order_from_ids: List[int] = None,
            gpio_idx_offset: int = 0
    ):
        super().__init__(
            pin_assignment=pin_assignment,
            initial_addressing=initial_addressing,
            idx_offset=idx_offset,
            gpio_order_from_ids=gpio_order_from_ids,
            gpio_idx_offset=gpio_idx_offset,
        )
        self._gpio_states: List[Optional[GPIOPinState]] = [None for _ in self._gpio_pins]

    def _change_pin_modes(self, pins: List[_GPIOPin], new_modes_iterator: Iterator[GPIOPinMode]):
        offset = self.gpio_idx_offset
        for pin in pins:
            pin.mode = next(new_modes_iterator)
            current_state = self._gpio_states[pin.gpio_idx - offset]

            if pin.mode is GPIOPinMode.OFF:
                self._gpio_states[pin.gpio_idx - offset] = None
            elif current_state is None:
                self._gpio_states[pin.gpio_idx - offset] = GPIOPinState.LOW

    def _gpio_pin_states_iterator(self, pins: List[_GPIOPin]) -> Iterator[Optional[GPIOPinState]]:
        offset = self.gpio_idx_offset
        return iter([self._gpio_states[pin.gpio_idx - offset] for pin in pins])

    def _change_gpio_pin_states(self, pins: List[_GPIOPin], new_states: List[GPIOPinState]) -> None:
        offset = self.gpio_idx_offset

        for pin, state in zip(pins, new_states):
            self._gpio_states[pin.gpio_idx - offset] = state

    @IndexableProperty
    def emulated_gpio_modes(self, item) -> Union[None, GPIOPinMode, List[Optional[GPIOPinMode]]]:
        return [pin.mode for pin in self._gpio_pins][item]

    @emulated_gpio_modes.itemsetter
    def emulated_gpio_modes(self, key, value):
        relevant_pins = self._gpio_pins[key]
        relevant_pins = relevant_pins if isinstance(relevant_pins, list) else [relevant_pins]
        value_it = iter([value for _ in relevant_pins]) if isinstance(value, GPIOPinMode) else iter(value)

        for pin in relevant_pins:
            pin.mode = next(value_it)

    @IndexableProperty
    def emulated_gpio_states(self, item) -> Union[None, GPIOPinMode, List[Optional[GPIOPinMode]]]:
        return self._gpio_states[item]

    @emulated_gpio_states.itemsetter
    def emulated_gpio_states(self, key, value):
        self._gpio_states[key] = value
