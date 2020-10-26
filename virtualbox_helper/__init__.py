import atexit
from subprocess import (
    Popen,
    TimeoutExpired,
    )
from time import sleep, time
from typing import Optional, Tuple, Union

import remotevbox
from remotevbox.machine import IMachine
import cv2 as cv
import numpy as np

_server_proc: Optional[Popen] = None

Image = Union[str, bytes, np.ndarray]


def _read_cv_image(image: Image) -> np.ndarray:
    """Convert a file path, bytes or ndarray to ndarray.

    This helper method allows the library user to send an image in different
    ways without continuously convert.
    """
    if type(image) == np.ndarray:
        return image
    if type(image) == str:
        ret = cv.imread(image, cv.IMREAD_COLOR)
        if ret is None:
            raise FileNotFoundError(f'Cannot find {image}')
        return ret
    if type(image) == bytes:
        return cv.imdecode(np.frombuffer(image, np.uint8), cv.IMREAD_COLOR)


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
    screenshot: Image,
    fragment: Image,
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
    img_rgb = _read_cv_image(screenshot)
    template = _read_cv_image(fragment)
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


def image_diff_score(screenshot: Image, reference: Image, binary_diff=True) -> float:
    """Calculate a difference score between 0 and 1.

    Images are expected to be of the same size, or an error will be raised.
    a score of 0 means they are identical, 1 that the difference is maximum.

    If binary_diff is True (the default), the value represent the ratio of
    pixels in the images with a color that is not exactly the same.

    Otherwise, the value represents the sum of the color d
    ifference in the
    RGB channels divided by the maximum possible value. It is 1.0 when an
    image is completely black and the other completely white.
    """
    img_rgb = _read_cv_image(screenshot)
    ref_rgb = _read_cv_image(reference)
    if img_rgb.shape != ref_rgb.shape:
        raise ValueError(
            f'Images have different shapes: {img_rgb.shape}, {ref_rgb.shape}'
            )
    if binary_diff:
        diff = img_rgb != ref_rgb
        pixel_diff = np.max(diff, -1)
        return np.sum(pixel_diff) / np.prod(pixel_diff.shape)
    else:
        # note: numpy difference won't work because they are uint8
        diff = cv.absdiff(img_rgb, ref_rgb)
        return np.sum(diff) / np.prod(diff.shape) / 255


def wait_for_fragment(
    machine: IMachine,
    fragment: Image,
    threshold: float = 0.8,
    timeout: float = 10.0,
    check_interval: float = 1.0
        ) -> Tuple[float, Tuple[int, int], Tuple[int, int]]:
    """Wait for a fragment to appear and return it, or raise TimeoutError.

    This helper function periodically invokes detect_fragment waiting for a
    fragment to appear. If it doesn't with the given threshold in the given
    time, raises TimeoutError.
    """
    expiration = time() + timeout
    while time() < expiration:
        found = detect_fragment(
            machine.take_screenshot_to_bytes(),
            fragment,
            threshold=threshold
            )
        if found is not None:
            return found
        sleep(check_interval)
    raise TimeoutError()


def wait_click_on_fragment(
    machine: IMachine,
    fragment: Image,
    threshold: float = 0.8,
    timeout: float = 10.0,
    check_interval: float = 1.0,
    left_click: bool = True,
    right_click: bool = False,
    force_absolute_pointer: bool = False,
        ) -> Tuple[float, Tuple[int, int]]:
    """Wait for a fragment, and click on the center of it.

    By default it clicks with the left button, can do the right or both by
    changing the flags.

    It tries to use absolute mouse pointer if possible, or if the flag to
    force it is provided, otherwise falls back to a trick to reset the mouse
    pointer coordinate by moving the mouse to the screen limits in the
    two axes one by one (it avoids moving both axis together to not trigger
    "hot corner" actions in the guest UI).

    If the fragment is not found within the timeout, TimeoutError is raised

    Returns
    -------
    The match accuracy, and X, Y coordinates of the target point
    """
    region_match = wait_for_fragment(
        machine,
        fragment,
        threshold=threshold,
        timeout=timeout,
        check_interval=check_interval,
        )
    center = (
        int((region_match[1][0] + region_match[2][0]) / 2),
        int((region_match[1][1] + region_match[2][1]) / 2),
        )
    if force_absolute_pointer or machine.absolute_mouse_pointer_supported():
        machine.put_mouse_event_absolute(
            center[0],
            center[1],
            left_pressed=left_click,
            right_pressed=right_click,
        )
        sleep(0.3)
        machine.put_mouse_event_absolute(
            center[0],
            center[1],
            left_pressed=not left_click,
            right_pressed=not right_click,
        )
    else:
        machine.put_mouse_event(-5000, 0)
        sleep(0.2)
        machine.put_mouse_event(center[0], 0)
        sleep(0.2)
        machine.put_mouse_event(0, -5000)
        sleep(0.2)
        machine.put_mouse_event(0, center[1])
        sleep(0.2)
        machine.put_mouse_event(
            0,
            0,
            left_pressed=left_click,
            right_pressed=right_click,
        )
        sleep(0.3)
        machine.put_mouse_event(
            0,
            0,
            left_pressed=not left_click,
            right_pressed=not right_click,
        )
    return (region_match[0], center)
