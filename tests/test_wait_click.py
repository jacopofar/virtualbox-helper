import pytest

from virtualbox_helper import wait_click_on_fragment, wait_for_fragment


def test_wait_click(running_machine):
    with pytest.raises(TimeoutError):
        wait_click_on_fragment(running_machine, 'tests/match_data/random_image.png', timeout=5.0)
    target = wait_click_on_fragment(running_machine, 'tests/match_data/debian_login_fragment.png', timeout=60.0)
    assert target[0] > 0.99
    assert target[1][0] == pytest.approx(291, 3)
    assert target[1][1] == pytest.approx(280, 3)
    # now that the mouse clicked, the guest OS will react
    match = wait_for_fragment(running_machine, 'tests/match_data/debian_login_selected.png')
    assert match is not None
