import atexit
from subprocess import (
    Popen,
    PIPE,
    STDOUT,
    TimeoutExpired,
    )
from typing import Optional

import remotevbox
from remotevbox.machine import IMachine

_server_proc: Optional[Popen] = None


def ensure_server_running():
    _server_proc = Popen("vboxwebsrv", shell=True)
    try:
        _server_proc.wait(2)
        raise ValueError('Cannot start the server!')
    except TimeoutExpired:
        # this is the normal case, it should just remain running
        def terminate_vboxserver(proc=_server_proc):
            proc.terminate()
        atexit.register(terminate_vboxserver)


def get_machine(
    user: str,
    password: str,
    machine_name: str,
    server_addr="http://127.0.0.1:18083",
    start=True
        ) -> IMachine:

    vbox = remotevbox.connect(server_addr, user, password)
    machine = vbox.get_machine(machine_name)
    if start:
        machine.launch()
    return machine
