# content of conftest.py
import pytest

from virtualbox_runner import get_machine


@pytest.fixture(scope="module")
def running_machine():
    machine = get_machine('vbox', 'yourpassphrase', 'Debian testing')
    machine.launch()
    yield machine
    machine.poweroff()
