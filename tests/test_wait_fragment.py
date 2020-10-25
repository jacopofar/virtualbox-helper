from time import time

import pytest

from virtualbox_runner import wait_for_fragment


def test_wait_fragment(running_machine):
    before = time()
    match = wait_for_fragment(running_machine, 'tests/match_data/grub_fragment.png')
    assert match[0] > 0.99

    with pytest.raises(TimeoutError):
        before = time()
        wait_for_fragment(running_machine, 'tests/match_data/random_image.png', timeout=2.0)
        assert time() + 2.0 > before

    before = time()
    match = wait_for_fragment(running_machine, 'tests/match_data/debian_login.png', timeout=20.0)
    assert match == (1.0, (0, 0), (800, 600))
    # at least 5 seconds to boot and show the debian login ?
    # meh, every test is uglier than the previous one, but what can we do?
    assert time() + 5.0 > before
