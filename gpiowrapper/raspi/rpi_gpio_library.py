from typing import List, Optional, Iterator

from .raspi_base import Raspi40PinBarData
from ..base import GPIOPinBar, _GPIOPin, GPIOPinState, GPIOPinMode, PinAddressing, PinType
from ..util import RequiresOptionalImport

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
except RuntimeError as e:
    print("Error importing RPi.GPIO! This is probably because you need superuser privileges.  "
          "You can achieve this by using 'sudo' to run your script")
    raise
except ModuleNotFoundError as e:
    pass


@RequiresOptionalImport(import_='RPi.GPIO', as_='GPIO')
class RPiGPIOPinBar(GPIOPinBar):
    """
    Pin Bar Wrapper Class for the RPi.GPIO library.
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
        Creates a new RPiGPIOPinBar object which wraps the RPi.GPIO library.
        The object provides functionality for the gpio pins and wraps them to the RPi.GPIO library interface.
        This class supports custom kinds of pin bar layouts but needs the corresponding setup information.
        If you just need a RPi.GPIO pin bar for the 40 pin header of the raspberry simply instantiate an
        Raspi40PinBarRPi object.

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

        # mappings between rpi library and wrapper library
        self._mode_to_rpi_mapping: dict[GPIOPinMode, int] = {
            GPIOPinMode.IN: GPIO.IN,
            GPIOPinMode.IN_PULL_DOWN: GPIO.IN,
            GPIOPinMode.IN_PULL_UP: GPIO.IN,
            GPIOPinMode.OUT: GPIO.OUT,
        }
        self._mode_to_rpi_pull_up_down: dict[GPIOPinMode, Optional[bool]] = {
            GPIOPinMode.IN: GPIO.PUD_OFF,
            GPIOPinMode.IN_PULL_DOWN: GPIO.PUD_DOWN,
            GPIOPinMode.IN_PULL_UP: GPIO.PUD_UP,
            GPIOPinMode.OUT: GPIO.PUD_OFF,
        }
        self._rpi_to_state_mapping: dict[int, GPIOPinState] = {
            GPIO.HIGH: GPIOPinState.HIGH,
            GPIO.LOW: GPIOPinState.LOW,
        }
        self._state_to_rpi_mapping: dict[GPIOPinState, int] = {
            GPIOPinState.HIGH: GPIO.HIGH,
            GPIOPinState.LOW: GPIO.LOW,
        }

    def _change_pin_modes(self, pins: List[_GPIOPin], new_modes: List[GPIOPinMode]):
        pins_and_new_modes = zip(pins, new_modes)
        pins_and_new_modes = [(pin, new_mode) for pin, new_mode in pins_and_new_modes
                              if pin.mode is not new_mode]

        cleanup_pins = [pin for pin, new_mode in pins_and_new_modes if pin.mode is not GPIOPinMode.OFF]
        for pin in cleanup_pins:
            GPIO.cleanup(pin.idx)
            pin.mode = GPIOPinMode.OFF

        setup_pins_and_modes = [(pin, mode) for pin, mode in pins_and_new_modes if mode is not GPIOPinMode.OFF]
        for pin, new_mode in setup_pins_and_modes:
            pin_id = pin.idx
            rpi_mode = self._mode_to_rpi_mapping[new_mode]
            rpi_pull_up_down = self._mode_to_rpi_pull_up_down[new_mode]

            GPIO.setup(pin_id, rpi_mode, pull_up_down=rpi_pull_up_down)
            pin.mode = new_mode

    def _gpio_pin_states_iterator(self, pins: List[_GPIOPin]) -> Iterator[Optional[GPIOPinState]]:
        channel_ids = [pin.idx for pin in pins]
        states: List[int] = [GPIO.input(idx) for idx in channel_ids]
        states: List[GPIOPinState] = [self._rpi_to_state_mapping[state] for state in states]

        return iter(states)

    def _change_gpio_pin_states(self, pins: List[_GPIOPin], new_states: List[GPIOPinState]) -> None:
        channel_ids = [pin.idx for pin in pins]
        states: List[int] = [self._state_to_rpi_mapping[state] for state in new_states]
        GPIO.output(channel_ids, states)

    def __del__(self) -> None:
        self.reset_gpio_pins()


@RequiresOptionalImport(import_='RPi.GPIO', as_='GPIO')
class Raspi40PinBarRPi(RPiGPIOPinBar):
    """
    Implementation of a 40 pin Raspberry pin bar based on the RPi.GPIO library.
    Note that this class needs the RPi.GPIO library to be imported during runtime.
    """

    def __init__(self, initial_addressing: PinAddressing):
        """
        Creates a new instance of a 40 pin Raspberry pin bar using the RPi.GPIO library to communicate with the pi.
        :param initial_addressing: Determines which pins are addressed for given indices.
        """
        super().__init__(
            pin_assignment=Raspi40PinBarData.pin_assignment(),
            initial_addressing=initial_addressing,
            idx_offset=Raspi40PinBarData.idx_offset(),
            gpio_order_from_ids=Raspi40PinBarData.gpio_orders_from_ids(),
            gpio_idx_offset=Raspi40PinBarData.gpio_idx_offset(),
        )
