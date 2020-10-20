import logging


from virtualbox_runner import get_machine, ensure_server_running, detect_fragment

logger = logging.getLogger(__name__)


def main():
    ensure_server_running()
    logger.info('Hello world')
    machine = get_machine('vbox', 'yourpassphrase', 'Debian testing', start=True)
    import time
    time.sleep(5)
    screenshot_data = machine.take_screenshot_to_bytes()
    machine.poweroff()

    print('detection:', detect_fragment(screenshot_data, 'fragment.png'))


if __name__ == '__main__':
    main()
