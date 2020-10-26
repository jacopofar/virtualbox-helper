# Virtualbox helper

This library helps to automate UI tasks on a Virtualbox machine using OpenCV.

It's based on `remotevbox` to interact with the SOAP service and `OpenCV` to
perform region detection.

__Features__:
* can start the `vboxwebsrv` SOAP server programmatically and shut it down
* match a region of the screen with a given fragment
* wait for a fragment and click on its center
* store if required a representation of the area it matched
* accepts images as NumPy ndarray, raw bytes of filesystem paths

## Installation

    python3 -m pip install virtualbox_helper


## Example usage

```Python 3

from virtualbox_helper import (
    ensure_server_running,
    get_machine,
    wait_for_fragment,
    wait_click_on_fragment,
)

# this starts the server and stops it when the interpreter exits
# or you can use the command vboxwebsrv manually
ensure_server_running()

machine = get_machine('vbox', 'yourpassphrase', 'Debian testing')
machine.launch()

no_match = detect_fragment(screenshot_data, 'some/random_image.png')
assert no_match is None

detection = detect_fragment(screenshot_data, 'valid_element.png')
assert detection is not None
# similarity score
assert detection[0] > 0.9
# coordinates of the bounding box that was detected
assert detection[1] == (19, 59)
assert detection[2] == (172, 114)

# raw bytes or a numpy (X, Y, 3) matrix can be used instead of a file path
button_data = open('button.png', 'rb').read()
target = wait_click_on_fragment(machine, button_data, timeout=60.0)
# target has the same structure of match above

wait_for_fragment(machine, 'some/element/to/wait_for.png')

with open('screenshot.png', 'wb') as f:
    screenshot_data = machine.take_screenshot_to_bytes()
    f.write(screenshot_data)

# this functionality is part of remotevbox
machine.send_character_string('hello world')
machine.send_key_combination(['<enter>'])

machine.poweroff()
```

## When shoulkd I use this?

Hopefully never! If you have a proper API for what you want to automate,
go with that.
To automate UI operations look into `PyAutoGUI`, and `Selenium` or `Puppeteer`
for the web.

However, if you can't do that, for example if you are writing tests for
TempleOS or something weird, then this may be fine.


## Tests

The tests are based on pytest, can be run using `poetry run test`.
They expect a machine called "Debian testing" running Debian 11.
Should be trivial to adapt to some other image.
