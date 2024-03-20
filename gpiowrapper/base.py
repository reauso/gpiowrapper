from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, unique
from operator import itemgetter
from types import NoneType
from typing import List, Union, Optional, Any, Iterable, Iterator

from gpiowrapper.errors import PinTypeError, ModeIsOffError
from gpiowrapper.util import IndexableProperty, replace_none_in_slice, subtract_offset_from_slice


@unique
class PinAddressing(Enum):
    """
    The pin addressing determines which pin is addressed for a given index.

    - In PinBar mode, the index matches the pin id on the pin bar assignment.
      E.g. if you want to address the pin in the upper left corner you can use the lowest id as
      index assuming that the assignment of the pin ids starts in that corner.
    - In GPIO mode, the index matches the individual gpio pin id enumeration.
      When using this mode you can only address pins of type GPIO.
      E.g. if the 12th pin of the pin bar is labeled as GPIO_0, then you can use the index zero to
      address that pin.
    """
    PinBar = 'PinBar'
    """
    In PinBar mode, the index matches the pin id on the pin bar assignment. E.g. if you want to address the
    pin in the upper left corner you can use the lowest id as index assuming that the assignment of the pin ids 
    starts in that corner.
    """
    GPIO = 'GPIO'
    """
    In GPIO mode, the index matches the individual gpio pin id enumeration. 
    When using this mode you can only address pins of type GPIO. 
    E.g. if the 12th pin of the pin bar is labeled as GPIO_0, then you can use the index zero to 
    address that pin.   
    """

    def __str__(self):
        return self.value


@unique
class PinType(Enum):
    """
    An enumeration of types for pins of a pin bar.
    Entries are:

    - POWER typed pins are responsible for constant power supply.
    - GROUND typed pins can be used to close electronic circuits.
    - GPIO typed pins are general purpose input output pins which are controllable and can be used
      for several kinds of applications.
    - OTHER typed pins with functionality not listed in this enumeration.
    """

    POWER = 0
    """ POWER typed pins are responsible for constant power supply. """
    GROUND = 1
    """ GROUND typed pins can be used to close electronic circuits. """
    GPIO = 2
    """
    GPIO typed pins are general purpose input output pins which are controllable and can be used
    for several kinds of applications.
    """
    OTHER = 3
    """ OTHER typed pins with functionality not listed in this enumeration. """


@unique
class GPIOPinState(Enum):
    """
    Possible gpio pin states.
    Note that this enumeration can only represent discrete values and therefore is incomplete.
    Values are:

    - LOW state represents a voltage-free pin state.
    - HIGH state represents a voltage-high pin state.
    """
    LOW = 0
    """ LOW state represents a voltage-free pin state. """
    HIGH = 1
    """ HIGH state represents a voltage-high pin state. """


@unique
class GPIOPinMode(Enum):
    """
    The Mode of a gpio pin.
    Note that not an implementation may not support all listed modes for a gpio pin.
    Possible modes are:

    - OFF: represents an unused gpio pin.
    - IN: represents an input gpio pin. Note that there is no inbuilt pull down or pull up resistor interposed.
    - IN_PULL_DOWN: represents an input gpio pin with inbuilt pull down resistor. So the default state of a pin in
      this mode is LOW.
    - IN_PULL_UP: represents an input gpio pin with inbuilt pull up resistor. So the default state of a pin in
      this mode is HIGH.
    - OUT: represents an output gpio pin. Note that there is no inbuilt pull down or pull up resistor interposed.
    """
    OFF = 0
    """ represents an unused gpio pin. """
    IN = 1
    """ represents an input gpio pin. Note that there is no inbuilt pull down or pull up resistor interposed. """
    IN_PULL_DOWN = 2
    """
    represents an input gpio pin with inbuilt pull down resistor. So the default state of a pin in this mode is LOW.
    """
    IN_PULL_UP = 3
    """
    represents an input gpio pin with inbuilt pull up resistor. So the default state of a pin in this mode is HIGH.
    """
    OUT = 4
    """ represents an output gpio pin. Note that there is no inbuilt pull down or pull up resistor interposed. """


@dataclass(slots=True, kw_only=True)
class Pin:
    """
    Dataclass to store pin data.
    """

    idx: int
    """ The id of the pin on the pin bar. """
    type: PinType
    """ The type of the pin. """


@dataclass(slots=True, kw_only=True)
class GPIOPin(Pin):
    """
    Dataclass to additionally store gpio pin data.
    """

    gpio_idx: int
    """ The gpio id of the pin. Depends on the individual gpio pin enumeration. """
    mode: GPIOPinMode = GPIOPinMode.OFF
    """ The current mode of the gpio pin. """


class PinBar(ABC):
    """
    An abstract base class representing an electronic pin bar with zero to several pins.
    """

    def __init__(self, pin_assignment: List[PinType], idx_offset: int = 0):
        """
        Creates a new PinBar object.

        :param pin_assignment: The pin assignment list contains each pin's type.
          The list is ordered by the pin id on the pin bar starting with the lowest id.
        :param idx_offset: The id starting offset on the pin bar. This value matches the lowest existing pin bar id.
          E.g. the first pin has the id 1 on the pin bar, then this parameter needs to be 1 too.
        """
        self._pins: List[Pin] = [Pin(idx=i + idx_offset, type=type) for i, type in enumerate(pin_assignment)]
        self._idx_offset: int = idx_offset

    @property
    def pin_assignment(self) -> List[PinType]:
        """
        Gets the pin assignment of this pin bar object as list.

        Note that a change to this list will NOT change the pin assignment of this object.
        To change the pin assignment you need to create a new pin bar object.
        """
        return [pin.type for pin in self._pins]

    @property
    def idx_offset(self) -> int:
        """ Gets the id starting offset of this pin bar object. This value matches the lowest pin id. """
        return self._idx_offset

    def __len__(self) -> int:
        """ Gets the total number of pins for this pin bar. This includes any pin type. """
        return len(self._pins)


class GPIOPinBar(PinBar, ABC):
    """
    An abstract base class representing an electronic pin bar with zero to several pins which provides
    functionality for gpio pins.
    """

    def __init__(
            self,
            pin_assignment: List[PinType],
            initial_addressing: PinAddressing,
            idx_offset: int = 0,
            gpio_order_from_ids: List[int] = None,
            gpio_idx_offset: int = 0
    ):
        """
        Creates a new GPIOPinBar object that provides functionality for gpio pins.

        :param pin_assignment: The pin assignment list contains each pin's type.
          The list is ordered by the pin id on the pin bar starting with the lowest id.
        :param initial_addressing: Determines which pins are addressed for given indices.
        :param idx_offset: The id starting offset on the pin bar. This value matches the lowest existing pin bar id.
          E.g. the first pin has the id 1 on the pin bar, then this parameter needs to be 1 too.
        :param gpio_order_from_ids: A list of integers that determines the gpio id enumeration.
          The list is ordered by the gpio id starting with the lowest gpio id and contains the pin bar ids.
          E.g. Pin 27 on the pin bar is labeled as GPIO_0, then the first entry of this list needs to be 27.
        :param gpio_idx_offset: The gpio id starting offset of the individual gpio enumeration.
          This value matches the lowest existing gpio id.
        """
        super().__init__(pin_assignment=pin_assignment, idx_offset=idx_offset)
        self._gpio_idx_offset: int = gpio_idx_offset

        self._convert_gpio_types_in_pins_list(gpio_order_from_ids)
        self._gpio_pins: List[GPIOPin] = [pin for pin in self._pins if isinstance(pin, GPIOPin)]
        self._gpio_pins.sort(key=lambda x: x.gpio_idx)

        self._index_validator_class: IndexValidator.__class__ = IndexValidator
        self._mode_validator_class: ModeValueValidator.__class__ = ModeValueValidator
        self._state_validator_class: StateValueValidator.__class__ = StateValueValidator

        self.addressing = initial_addressing

    def _convert_gpio_types_in_pins_list(self, gpio_order_from_ids) -> None:
        """
        Converts pins of type gpio into GPIOPin dataclass objects.
        :param gpio_order_from_ids: see __init__ params.
        """
        gpio_pin_indices = [i for i, pin in enumerate(self._pins) if pin.type is PinType.GPIO]
        gpio_order_indices = gpio_pin_indices

        if gpio_order_from_ids is not None:
            gpio_order_indices = [i - self._idx_offset for i in gpio_order_from_ids]

        if not sorted(gpio_order_indices) == gpio_pin_indices:
            raise ValueError(f'gpio_order_from_ids parameter is invalid! '
                             'Check if you are missing a gpio pin or have duplicates.')

        for i, index in enumerate(gpio_order_indices):
            pin = self._pins[index]
            self._pins[index] = GPIOPin(
                idx=pin.idx,
                type=PinType.GPIO,
                gpio_idx=i + self._gpio_idx_offset,
                mode=GPIOPinMode.OFF
            )

    @property
    def gpio_idx_offset(self) -> int:
        """
        Gets the gpio id starting offset of this gpio pin bar object.
        This value matches the lowest gpio pin gpio id.
        See PinAddressing.GPIO for more information of the different pin id spaces.
        """
        return self._gpio_idx_offset

    @property
    def num_gpio_pins(self) -> int:
        """ Gets the total number of GPIO Pins. """
        return len(self._gpio_pins)

    @property
    def addressing(self) -> PinAddressing:
        """
        Gets the current pin addressing mode of this pin bar.
        """
        return self._addressing

    @addressing.setter
    def addressing(self, new_addressing: PinAddressing) -> None:
        """
        Sets the pin addressing mode of this pin bar. Allowed addressing modes are PinBar and GPIO.
        :param new_addressing: The new addressing mode.
        """
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

    @IndexableProperty
    def modes(self, item) -> Union[Optional[GPIOPinMode], List[Optional[GPIOPinMode]]]:
        """
        Get the mode(s) of the pins of this pin bar.
        Considers the currently set pin addressing!

        :param item: The index item. Valid indices are of type int, slice or list.
        :return: A GPIOPinMode for int indices,
          a list of GPIOPinMode and None for slice indices where None represents that the corresponding pin is not
          a gpio pin, a list of GPIOPinMode for list indices.
        """
        self._index_validator_class.validate(item=item, offset=self._addressing_offset,
                                             length=self._addressing_array_length, pin_bar=self)

        item_pins = self._get_pins(item=item)

        if isinstance(item_pins, list):
            return [pin.mode if isinstance(pin, GPIOPin) else None for pin in item_pins]
        else:
            return item_pins.mode if isinstance(item_pins, GPIOPin) else None

    @modes.itemsetter
    def modes(self, key, value: Union[GPIOPinMode, List[Optional[GPIOPinMode]]]) -> None:
        """
        Set new gpio pin mode(s) for the pins of this pin bar.
        Considers the currently set pin addressing!

        :param key: The index item. Valid indices are of type int, slice or list.
        :param value: The new value(s). Note that if you use a slice index and the slice is addressing
          pins that are not of type gpio, you have to pass a None value for these pins.
        """
        self._index_validator_class.validate(item=key, offset=self._addressing_offset,
                                             length=self._addressing_array_length, pin_bar=self)

        item_pins = self._get_pins(item=key)
        item_pins = [item_pins] if not isinstance(item_pins, list) else item_pins

        if not isinstance(key, slice):
            self._validate_pins_are_gpio(item_pins)

        self._mode_validator_class.validate(value=value, index_type=type(key), considered_pins=item_pins)

        if isinstance(value, list):
            value = [v for v in value if v is not None]

        item_pins = [pin for pin in item_pins if isinstance(pin, GPIOPin)]
        new_values = [value for _ in item_pins] if isinstance(value, GPIOPinMode) else list(value)

        self._change_pin_modes(item_pins, new_values)

    def _change_pin_modes(self, pins: List[GPIOPin], new_modes: List[GPIOPinMode]):
        """
        Change the modes of the given list of pins.

        :param pins: The pins of which the mode is to be changed.
        :param new_modes: A list object which provides the new modes.
        """
        for pin, new_mode in zip(pins, new_modes):
            pin.mode = new_mode

    @IndexableProperty
    def states(self, item) -> Union[Optional[GPIOPinState], List[Optional[GPIOPinState]]]:
        """
        Get the state(s) of the pins of this pin bar.
        Considers the currently set pin addressing!

        :param item: The index item. Valid indices are of type int, slice or list.
        :return: A GPIOPinState for int indices,
          a list of GPIOPinState and None for slice indices where None represents that the corresponding pin is not
          a gpio pin or the gpio pin is in OFF mode, a list of GPIOPinState for list indices.
        """
        self._index_validator_class.validate(item=item, offset=self._addressing_offset,
                                             length=self._addressing_array_length, pin_bar=self)

        item_pins = self._get_pins(item=item)
        item_pins = [item_pins] if not isinstance(item_pins, list) else item_pins
        gpio_pins = [pin for pin in item_pins if isinstance(pin, GPIOPin)]

        if not isinstance(item, slice):
            self._validate_pins_are_gpio(item_pins)
            self._validate_gpio_pin_modes_not_off(gpio_pins)
        else:
            gpio_pins = [pin for pin in gpio_pins if pin.mode is not GPIOPinMode.OFF]

        state_iterator = self._gpio_pin_states_iterator(gpio_pins)
        if isinstance(item, int):
            return next(state_iterator)
        else:
            return [next(state_iterator) if isinstance(pin, GPIOPin) and pin.mode is not GPIOPinMode.OFF else None
                    for pin in item_pins]

    @abstractmethod
    def _gpio_pin_states_iterator(self, pins: List[GPIOPin]) -> Iterator[Optional[GPIOPinState]]:
        """
        Gets an iterator which provides the current states of the given pins.
        The state order of the iterator matches the pin order of the given list of pins.

        :param pins: The pins of which the state is to be read.
        :return: An iterator returning the current state values in the correct order.
        """
        pass

    @states.itemsetter
    def states(self, key, value: Union[GPIOPinState, List[Optional[GPIOPinState]]]) -> None:
        """
        Set new gpio pin state(s) for the pins of this pin bar.
        Considers the currently set pin addressing!

        :param key: The index item. Valid indices are of type int, slice or list.
        :param value: The new value(s). Note that if you use a slice index and the slice is addressing
          pins that are either not of type gpio or are in OFF mode, you have to pass a None value for
          these pins.
        """
        self._index_validator_class.validate(item=key, offset=self._addressing_offset,
                                             length=self._addressing_array_length, pin_bar=self)

        item_pins = self._get_pins(item=key)
        item_pins = [item_pins] if not isinstance(item_pins, list) else item_pins
        gpio_pins = [pin for pin in item_pins if isinstance(pin, GPIOPin)]

        if not isinstance(key, slice):
            self._validate_pins_are_gpio(item_pins)
            self._validate_gpio_pin_modes_not_off(gpio_pins)

        self._state_validator_class.validate(value=value, index_type=type(key), considered_pins=item_pins)

        if isinstance(key, slice):
            gpio_pins = [pin for pin in gpio_pins if pin.mode is not GPIOPinMode.OFF]
        if isinstance(value, GPIOPinState):
            value = [value for _ in gpio_pins]
        elif isinstance(value, list):
            value = [v for v in value if v is not None]

        self._change_gpio_pin_states(gpio_pins, value)

    @abstractmethod
    def _change_gpio_pin_states(self, pins: List[GPIOPin], new_states: List[GPIOPinState]) -> None:
        """
        Change the states of the given list of pins.

        :param pins: The pins of which the state is to be changed.
        :param new_states: The list with the new pin states.
        """
        pass

    def _get_pins(self, item: Union[int, slice, list]) -> Union[Pin, List[Pin]]:
        """
        Gets the pins addressed by a given index item.
        Considers the currently set pin addressing!

        :param item: An index item of type int, slice or list.
        :return: A list of pins.
        """
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
    def _validate_pins_are_gpio(item_pins: Iterable[Pin]) -> None:
        """ Validates that a list of pins contains only pins of type GPIOPin. """
        for pin in item_pins:
            if not isinstance(pin, GPIOPin):
                raise PinTypeError(f'pin is not of {PinType.__name__}.{PinType.GPIO} for pin idx {pin.idx}')

    @staticmethod
    def _validate_gpio_pin_modes_not_off(gpio_pins: Iterable[GPIOPin]) -> None:
        """ Validates tha a list of gpio pins contains only pins which are NOT in OFF mode. """
        for pin in gpio_pins:
            if pin.mode is GPIOPinMode.OFF:
                raise ModeIsOffError(f'cannot get state of gpio pin in {GPIOPinMode.OFF} for pin idx {pin.idx}')

    def reset_gpio_pins(self) -> None:
        """ Resets all pin modes of this pin bar. """
        new_values = [GPIOPinMode.OFF for _ in self._gpio_pins]
        self._change_pin_modes(self._gpio_pins, new_values)


class IndexValidator:
    """ Validator for index items that validates valid types and values. """

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
            pin_bar: GPIOPinBar
    ) -> None:
        """
        Validates both type and value of the given item as index.
        :param item: The index item.
        :param offset: The current offset. Depends on the current pin addressing used.
        :param length: The length of the pin array. Depends on the current pin addressing used.
        :param pin_bar: The current pin bar object used.
        """
        cls.validate_index_type(type(item))
        validation_func = cls._validation_mapping()[type(item)]

        if validation_func is not None:
            # noinspection PyArgumentList
            validation_func(item=item, offset=offset, length=length, pin_bar=pin_bar)

    @classmethod
    def validate_index_type(cls, item_type):
        """ Validates the type of the index item. """
        if item_type not in [int, slice, list]:
            raise TypeError(f'index must be integer, slice or list, not {item_type.__name__}')

    @classmethod
    def validate_int_index(cls, item: int, offset: int, length: int, pin_bar: GPIOPinBar, **_):
        if not offset <= item < offset + length:
            raise IndexError(f'index out of range for {PinAddressing.__name__}.{str(pin_bar.addressing)}')

    @classmethod
    def validate_slice_index(cls, item: slice, **_):
        if (
                (item.start is not None and not isinstance(item.start, int)) or
                (item.stop is not None and not isinstance(item.stop, int)) or
                (item.step is not None and not isinstance(item.step, int))
        ):
            raise TypeError(f'slice indices must be integers or None or have an __index__ method')

    @classmethod
    def validate_list_index(cls, item: list, offset: int, length: int, pin_bar: GPIOPinBar, **_):
        for i, index in enumerate(item):
            if isinstance(index, int):
                try:
                    cls.validate_int_index(index, offset, length, pin_bar)
                except IndexError:
                    raise IndexError(
                        f'index out of range for {PinAddressing.__name__}.{str(pin_bar.addressing)} at position {i}'
                    ) from None
            else:
                raise TypeError(f'list indices must be integers or have an __index__ method. '
                                f'Found type {type(index).__name__} at position {i}')


class ValueValidator(ABC):
    """
    Abstract base class to validate values set for the gpio pin attributes.
    """

    @classmethod
    def _validation_mapping(cls):
        """ Gets the validation method for each index type. """
        return {
            int: cls._validate_for_int_index,
            slice: cls._validate_for_slice_index,
            list: cls._validate_for_list_index,
        }

    @classmethod
    def validate(cls, value, index_type, considered_pins: List[Pin]):
        """
        Validates both type and value of the given value.
        :param value: The value to validate.
        :param index_type: The index type used to address the list.
        :param considered_pins: A list of the considered pins of the current operation.
        """
        cls._validate_type(type(value))

        validation_func = cls._validation_mapping()[index_type]
        if validation_func is not None:
            # noinspection PyArgumentList
            validation_func(value=value, considered_pins=considered_pins)

    @classmethod
    @abstractmethod
    def _validate_type(cls, value_type):
        """ Validates the type of the value. """
        pass

    @classmethod
    def _validate_for_int_index(cls, value, **_):
        """ Validates the value for an int index. """
        if isinstance(value, list):
            raise ValueError('setting an array element with a sequence.')

    @classmethod
    def _validate_for_slice_index(cls, value, considered_pins: List[Pin], **_):
        """ Validates the value for a slice index. """
        if isinstance(value, list):
            cls._validate_list_size(considered_pins, value)
            cls._validate_list_entries(value, considered_pins, none_allowed=True)

    @classmethod
    def _validate_for_list_index(cls, value, considered_pins: List[Pin], **_):
        """ Validates the value for a list index. """
        if isinstance(value, list):
            cls._validate_list_size(considered_pins, value)
            cls._validate_list_entries(value, considered_pins, none_allowed=False)

    @classmethod
    def _validate_list_size(cls, considered_pins, value):
        """ Validates that the number of values and the number of considered pins are the same. """
        if len(value) is not len(considered_pins):
            raise ValueError(
                f'could not broadcast input array from size {len(value)} into size {len(considered_pins)}')

    @classmethod
    def _validate_list_entries(cls, value, considered_pins: List[Pin], none_allowed: bool) -> None:
        """
        Validates that the value list entries are valid for each individual pin type of the
        considered pins.
        :param value: The list of values to validate.
        :param considered_pins: The considered pins by this operation.
        :param none_allowed: If None values are allowed or not.
        """
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

            if (v is None and isinstance(pin, GPIOPin)) or (v is not None and not isinstance(pin, GPIOPin)):
                msg = f'unable to assign {v} at position {i} to pin of type {pin.type}'
                raise PinTypeError(msg)

    @classmethod
    @abstractmethod
    def _allowed_list_entry_types(cls) -> List:
        """ Gets a list of the allowed data types when the value to validate is a list. """
        pass


class ModeValueValidator(ValueValidator):
    """ The value validator when setting new gpio pin mode(s). """

    @classmethod
    def _validate_type(cls, value_type):
        if value_type not in [GPIOPinMode, list]:
            raise TypeError(f'value must be {GPIOPinMode.__name__} or list, not {value_type.__name__}')

    @classmethod
    def _allowed_list_entry_types(cls) -> List:
        return [GPIOPinMode]


class StateValueValidator(ValueValidator):
    """ The value validator when setting new gpio pin state(s). """

    @classmethod
    def _validate_type(cls, value_type):
        if value_type not in [GPIOPinState, list]:
            raise TypeError(f'value must be {GPIOPinState.__name__} or list, not {value_type.__name__}')

    @classmethod
    def _validate_list_entries(cls, value, considered_pins: List[Pin], none_allowed: bool):
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
            msg = f'{msg} with {pin.mode}' if isinstance(pin, GPIOPin) else msg

            if v is not None and not isinstance(pin, GPIOPin):
                raise PinTypeError(msg)
            elif v is not None and isinstance(pin, GPIOPin) and pin.mode is GPIOPinMode.OFF:
                raise ModeIsOffError(msg)
            elif v is None and isinstance(pin, GPIOPin) and pin.mode is not GPIOPinMode.OFF:
                raise ValueError(msg)

    @classmethod
    def _allowed_list_entry_types(cls) -> List:
        return [GPIOPinState]


class GPIOPinBarEmulator(GPIOPinBar):
    """ An emulator class for a gpio pin bar that provides full control of the pin modes and states. """

    def __init__(
            self,
            pin_assignment: List[PinType],
            initial_addressing: PinAddressing,
            idx_offset: int = 0,
            gpio_order_from_ids: List[int] = None,
            gpio_idx_offset: int = 0
    ):
        """
        Creates a new GPIOPinBarEmulator object that provides functionality for gpio pins and full control
        of pin modes and states.

        :param pin_assignment: The pin assignment list contains each pin's type.
          The list is ordered by the pin id on the pin bar starting with the lowest id.
        :param initial_addressing: Determines which pins are addressed for given indices.
        :param idx_offset: The id starting offset on the pin bar. This value matches the lowest existing pin bar id.
          E.g. the first pin has the id 1 on the pin bar, then this parameter needs to be 1 too.
        :param gpio_order_from_ids: A list of integers that determines the gpio id enumeration.
          The list is ordered by the gpio id starting with the lowest gpio id and contains the pin bar ids.
          E.g. Pin 27 on the pin bar is labeled as GPIO_0, then the first entry of this list needs to be 27.
        :param gpio_idx_offset: The gpio id starting offset of the individual gpio enumeration.
          This value matches the lowest existing gpio id.
        """
        super().__init__(
            pin_assignment=pin_assignment,
            initial_addressing=initial_addressing,
            idx_offset=idx_offset,
            gpio_order_from_ids=gpio_order_from_ids,
            gpio_idx_offset=gpio_idx_offset,
        )
        self._gpio_states: List[Optional[GPIOPinState]] = [None for _ in self._gpio_pins]

    def _change_pin_modes(self, pins: List[GPIOPin], new_modes: List[GPIOPinMode]):
        offset = self.gpio_idx_offset
        for pin, new_mode in zip(pins, new_modes):
            pin.mode = new_mode
            current_state = self._gpio_states[pin.gpio_idx - offset]

            if pin.mode is GPIOPinMode.OFF:
                self._gpio_states[pin.gpio_idx - offset] = None
            elif current_state is None:
                self._gpio_states[pin.gpio_idx - offset] = GPIOPinState.LOW

    def _gpio_pin_states_iterator(self, pins: List[GPIOPin]) -> Iterator[Optional[GPIOPinState]]:
        offset = self.gpio_idx_offset
        return iter([self._gpio_states[pin.gpio_idx - offset] for pin in pins])

    def _change_gpio_pin_states(self, pins: List[GPIOPin], new_states: List[GPIOPinState]) -> None:
        offset = self.gpio_idx_offset

        for pin, state in zip(pins, new_states):
            self._gpio_states[pin.gpio_idx - offset] = state

    @IndexableProperty
    def emulated_gpio_modes(self, item) -> Union[GPIOPinMode, List[GPIOPinMode]]:
        """
        Get the gpio pin modes of this pin bar in GPIO pin addressing style.
        :param item: The index item. This is no gpio id! Has to match standard list index types.
        :return: A list of gpio pin modes for the addressed gpio pins or a single GPIOPinMode
          value when item is of type int.
        """
        return [pin.mode for pin in self._gpio_pins][item]

    @emulated_gpio_modes.itemsetter
    def emulated_gpio_modes(self, key, value) -> None:
        """
        Set new gpio pin modes without validation. It is your responsibility that this object is in a valid
        state.
        :param key: The index item. This is no gpio id! Has to match standard list index types.
        :param value: The new value(s) to set. Must follow standard list __setitem__ rules.
        """
        relevant_pins = self._gpio_pins[key]
        relevant_pins = relevant_pins if isinstance(relevant_pins, list) else [relevant_pins]
        value_it = iter([value for _ in relevant_pins]) if isinstance(value, GPIOPinMode) else iter(value)

        for pin in relevant_pins:
            pin.mode = next(value_it)

    @IndexableProperty
    def emulated_gpio_states(self, item) -> Union[None, GPIOPinState, List[Optional[GPIOPinState]]]:
        """
        Get the gpio pin states of this pin bar in GPIO pin addressing style.
        :param item: The index item. This is no gpio id! Has to match standard list index types.
        :return: A list of gpio pin states for the addressed gpio pins or a single None or GPIOPinState
          value when item is of type int.
        """
        return self._gpio_states[item]

    @emulated_gpio_states.itemsetter
    def emulated_gpio_states(self, key, value) -> None:
        """
        Set new gpio pin states without validation. It is your responsibility that this object is in a valid
        state.
        :param key: The index item. This is no gpio id! Has to match standard list index types.
        :param value: The new value(s) to set. Must follow standard list __setitem__ rules.
        """
        self._gpio_states[key] = value
