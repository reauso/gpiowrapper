# gpiowrapper

A gpio wrapper library that provides an interface layer for libraries that control 
electronic pin bars. 
So that you can simply switch between different electronic pin bar layouts, boards and chips.

## Installation

The simplest way to install the gpiowrapper library is to install from pypi via
```bash
pip install gpiowrapper
```
But you can also install from the gitHub repo instead.
```bash
pip install git+https://github.com/reauso/gpiowrapper.git@latest
```

There are some optional extra dependency packages which enable the usage of existing implementations for
libraries and boards. A full list of current implementations is available in section 
**_Setting up custom pin bar wrappers_**.

This is the list of current extra dependencies:

| Name      | Description                                                            |
|-----------|------------------------------------------------------------------------|
| `raspi`   | Adds dependencies that enable the usage of the raspberry pi gpio pins. |
| `all`     | Installs all dependencies from all extras.                             |

To install gpiowrapper with extra dependencies use this command with pip:
```pip install gpiowrapper[<extra_name>]```
where you replace `<extra_name>` with the extra dependency package name you want to install.
You can also install multiple extras by appending more extra names separated by `,`. 

## Usage

The gpiowrapper library api is structured very simple.

First you create an object of the desired pin bar.
When creating a pin bar object you need to define your initial addressing mode.
Boards usually have several systems for identifying a pin like counting the pins from top to
bottom on the pin bar or use the pin names which mostly come from the electronic chip.
If you look at the [pin bar diagram](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html) 
of the raspberry pi 4 you see that these two systems are not
even close to being the same. To clarify how to interpret a given index you need to specify which
addressing to use. The `PinAddressing.GPIO` in the example code below identifies a pin by using the 
gpio id of the pin names. E.g. using index 0 equals pin 27 on the raspberry 4 pin bar.
It is also important to know that it is possible for each type of addressing to have a starting 
index offset. In case of the raspberry 4 pin bar, the first pin has the idx 1 and the last pin 
the idx 40. So the index to use when addressing the first pin is also 1. 

Each gpio pin has a current mode and state which can be accessed and modified by indexable 
properties called `modes` and `states` as shown in the example code below.

```python
from gpiowrapper import PinAddressing, GPIOPinMode, GPIOPinState
from gpiowrapper.raspi import Raspi40PinBarEmulator

if __name__ == "__main__":
    bar = Raspi40PinBarEmulator(initial_addressing=PinAddressing.GPIO)

    # get pin mode
    gpio_0_mode = bar.modes[0]

    # set pin mode(s)
    bar.modes[0] = GPIOPinMode.OUT
    bar.modes[1:5] = GPIOPinMode.OUT
    bar.modes[[6, 7]] = [GPIOPinMode.IN_PULL_DOWN, GPIOPinMode.IN_PULL_UP]

    # get pin states
    pin_states = bar.states[:]

    # set pin states
    bar.states[0:5] = GPIOPinState.HIGH
    bar.states[[0, 4, 2]] = GPIOPinState.LOW
```

## Currently pre supported libraries and boards

| Library  | Board / Pin Bar            | Wrapper Class Name | Extra Dependencies | 
|----------|----------------------------|--------------------|--------------------|
| RPi.GPIO | _custom pin bar layout_    | RPiGPIOPinBar      | raspi              |
| RPi.GPIO | Raspberry Pi 40 Pin Header | Raspi40PinBarRPi   | raspi              |

You can use the `GPIOPinBarFactory` class to simply create an instance of the GPIOPinBar you need.
Each library and board supported has a corresponding `LibraryType` and `BoardType`.
To create a pin bar instance with _custom pin bar layout_ you can set `None` as `BoardType` parameter.

```python
from gpiowrapper import GPIOPinBarFactory, LibraryType, BoardType, PinAddressing

if __name__ == "__main__":
    bar = GPIOPinBarFactory.new_pin_bar_instance(
        library=LibraryType.RPi_GPIO,
        board=BoardType.Raspi_40_pin_header,
        initial_addressing=PinAddressing.PinBar
    )
```

## Setting up custom pin bar wrappers

This section describes how you create a custom pin bar class to wrap a custom library.

The abstract base class for all pin bars with gpio functionality is called GPIOPinBar which
can simply be imported by `from gpiowrapper.base import GPIOPinBar`.
Each subclass has to implement the `_gpio_pin_states_iterator` and `_change_gpio_pin_states`
methods to get and set the states of the gpio pins. Additionally, if the gpio pins need some kind
of setup to be used or cleanup after usage in your custom library, you can simply overwrite the 
`_change_pin_modes` method.

An example implementation is given by `GPIOPinBarEmulator` class at location `gpiowrapper/base.py`

## Planned Improvements

- event listeners if pin state changes
- support of PWM gpio pins 
- implement other electric components which can be nested so that if you do: `led.on()` the corresponding pin 
  state is changed to the voltage level required for this led to be on. Other electronic components like a
  relay can be interposed.
