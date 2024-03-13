from typing import List, Optional, Iterator

from .raspi_base import Raspi40PinBarData
from ..base import GPIOPinBar, _GPIOPin, GPIOPinState, GPIOPinMode, PinAddressing
from ..util import RequiresOptionalImport

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BOARD)
    # GPIO.setwarnings(False)
except RuntimeError as e:
    print("Error importing RPi.GPIO! This is probably because you need superuser privileges.  "
          "You can achieve this by using 'sudo' to run your script")
    raise
except ModuleNotFoundError as e:
    pass


@RequiresOptionalImport(import_='RPi.GPIO', as_='GPIO')
class Raspi40PinBarRPi(GPIOPinBar):
    def __init__(self, initial_addressing: PinAddressing):
        super().__init__(
            pin_assignment=Raspi40PinBarData.pin_assignment(),
            initial_addressing=initial_addressing,
            idx_offset=Raspi40PinBarData.idx_offset(),
            gpio_order_from_ids=Raspi40PinBarData.gpio_orders_from_ids(),
            gpio_idx_offset=Raspi40PinBarData.gpio_idx_offset(),
        )
        self._mode_to_rpi_mode_mapping: dict[GPIOPinMode, int] = {
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
        self._rpi_state_to_state_mapping: dict[int, GPIOPinState] = {
            GPIO.HIGH: GPIOPinState.HIGH,
            GPIO.LOW: GPIOPinState.LOW,
        }
        self._state_to_rpi_state_mapping: dict[GPIOPinState, int] = {
            GPIOPinState.HIGH: GPIO.HIGH,
            GPIOPinState.LOW: GPIO.LOW,
        }

    def _change_pin_modes(self, pins: List[_GPIOPin], new_modes_iterator: Iterator[GPIOPinMode]):
        new_modes = [mode for mode in new_modes_iterator]

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
            rpi_mode = self._mode_to_rpi_mode_mapping[new_mode]
            rpi_pull_up_down = self._mode_to_rpi_pull_up_down[new_mode]

            GPIO.setup(pin_id, rpi_mode, pull_up_down=rpi_pull_up_down)
            pin.mode = new_mode

    def _gpio_pin_states_iterator(self, pins: List[_GPIOPin]) -> Iterator[Optional[GPIOPinState]]:
        channel_ids = [pin.idx for pin in pins]
        states: List[int] = [GPIO.input(idx) for idx in channel_ids]
        states: List[GPIOPinState] = [self._rpi_state_to_state_mapping[state] for state in states]

        return iter(states)

    def _change_gpio_pin_states(self, pins: List[_GPIOPin], new_states: List[GPIOPinState]) -> None:
        channel_ids = [pin.idx for pin in pins]
        states: List[int] = [self._state_to_rpi_state_mapping[state] for state in new_states]
        GPIO.output(channel_ids, states)

    def __del__(self):
        GPIO.cleanup()
