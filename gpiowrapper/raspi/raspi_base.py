import copy
from dataclasses import dataclass

from gpiowrapper.base import PinType, GPIOPinBarEmulator, PinAddressing


@dataclass(frozen=True)
class Raspi40PinBarData:
    # from https://www.raspberrypi.com/documentation/computers/raspberry-pi.html
    # and https://www.raspberrypi.com/documentation/computers/images/GPIO-Pinout-Diagram-2.png
    # (Last revisited 05.03.2024)

    @staticmethod
    def pin_assignment():
        value = [
            PinType.POWER, PinType.POWER, PinType.GPIO, PinType.POWER,  # 1  - 4
            PinType.GPIO, PinType.GROUND, PinType.GPIO, PinType.GPIO,  # 5  - 8
            PinType.GROUND, PinType.GPIO, PinType.GPIO, PinType.GPIO,  # 9  - 12
            PinType.GPIO, PinType.GROUND, PinType.GPIO, PinType.GPIO,  # 13 - 16
            PinType.POWER, PinType.GPIO, PinType.GPIO, PinType.GROUND,  # 17 - 20
            PinType.GPIO, PinType.GPIO, PinType.GPIO, PinType.GPIO,  # 21 - 24
            PinType.GROUND, PinType.GPIO, PinType.GPIO, PinType.GPIO,  # 25 - 28
            PinType.GPIO, PinType.GROUND, PinType.GPIO, PinType.GPIO,  # 29 - 32
            PinType.GPIO, PinType.GROUND, PinType.GPIO, PinType.GPIO,  # 33 - 36
            PinType.GPIO, PinType.GPIO, PinType.GROUND, PinType.GPIO,  # 37 - 40
        ]
        return copy.deepcopy(value)

    @staticmethod
    def idx_offset():
        return 1

    @staticmethod
    def gpio_orders_from_ids():
        value = [27, 28, 3, 5, 7, 29, 31, 26, 24, 21, 19, 23, 32,
                 33, 8, 10, 36, 11, 12, 35, 38, 40, 15, 16, 18, 22, 37, 13]
        return copy.deepcopy(value)

    @staticmethod
    def gpio_idx_offset():
        return 0


class Raspi40PinBarEmulator(GPIOPinBarEmulator):
    def __init__(self, initial_addressing: PinAddressing):
        super().__init__(
            pin_assignment=Raspi40PinBarData.pin_assignment(),
            initial_addressing=initial_addressing,
            idx_offset=Raspi40PinBarData.idx_offset(),
            gpio_order_from_ids=Raspi40PinBarData.gpio_orders_from_ids(),
            gpio_idx_offset=Raspi40PinBarData.gpio_idx_offset(),
        )
