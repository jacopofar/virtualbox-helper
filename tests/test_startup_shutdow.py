import time

from virtualbox_helper import ensure_server_running, get_machine

# yep, it's ugly


def test_start_server_and_get_machine():
    ensure_server_running()
    assert get_machine('vbox', 'yourpassphrase', 'Debian testing') is not None


def test_start_machine_and_shutdown():
    ensure_server_running()
    machine = get_machine('vbox', 'yourpassphrase', 'Debian testing')
    machine.launch()
    time.sleep(5)
    machine.poweroff()
