import atexit
from subprocess import (
    Popen,
    TimeoutExpired,
    )
from time import sleep
from typing import Optional, Tuple

import remotevbox
from remotevbox.machine import IMachine
import cv2 as cv
import numpy as np

_server_proc: Optional[Popen] = None


def ensure_server_running():
    """Start a VirtualBox SOAP server.

    This is mega ugly. This server by default logs but doesn't exit
    in case the port is already in use, and this error is ent to stdout.

    So, this only starts it and doesn't care.

    Then, the process is terminated (SIGTERM, and after 3 seconds SIGKILL)
    using the atexit hook.

    Calling the function multiple times and/or when the server is already
    running will start extra servers doing nothing, they are however quite
    light and should be all terminated at exit.
    """
    _server_proc = Popen("vboxwebsrv", shell=True)
    try:
        _server_proc.wait(2)
        raise ValueError('Cannot start the server!')
    except TimeoutExpired:
        # this is the normal case, it should just remain running
        def terminate_vboxserver(proc: Popen = _server_proc):
            proc.terminate()
            sleep(3)
            if proc.poll() is not None:
                print('Process survived the SIGTERM, killing it!')
                proc.kill()
        atexit.register(terminate_vboxserver)


def get_machine(
    user: str,
    password: str,
    machine_name: str,
    server_addr="http://127.0.0.1:18083",
    start=False
        ) -> IMachine:
    """Return the IMachine instance from a server with a given name.

    If start is true, the machine is started as well.
    """

    vbox = remotevbox.connect(server_addr, user, password)
    machine = vbox.get_machine(machine_name)
    if start:
        machine.launch()
    return machine


def detect_fragment(
    screenshot_data: bytes,
    fragment: str,
    threshold: float = 0.8,
    store_match: Optional[str] = None
        ) -> Optional[Tuple[float, Tuple[int, int], Tuple[int, int]]]:
    """Detect the presence and position of a given fragment in the sceenshot.

    If the fragment is not found, None is returned.
    If it's found, a tuple is returned containing the match probability
    and the coordinates of the top left and bottom right corners.

    If store_match is given, a file with that name will be created showing
    the matched region as a red rectangle.
    """
    img_rgb = cv.imdecode(np.frombuffer(screenshot_data, np.uint8), cv.IMREAD_COLOR)
    template = cv.imread(fragment, cv.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f'Cannot find {fragment}')
    w, h, _ = template.shape
    res = cv.matchTemplate(img_rgb, template, cv.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

    if max_val < threshold:
        return None

    top_left = max_loc
    bottom_right = (top_left[0] + h, top_left[1] + w)
    if store_match is not None:
        cv.rectangle(img_rgb, top_left, bottom_right, (0, 0, 255), 2)
        cv.imwrite(store_match, img_rgb)
    return (max_val, top_left, bottom_right)
    # cv.imshow('image', img_rgb)
    # cv.waitKey(0)
    # cv.destroyAllWindows()
