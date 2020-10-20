
def test_take_screenshot(running_machine, tmpdir):
    screenshot_data = running_machine.take_screenshot_to_bytes()
    target_file = tmpdir.join('screenshot.png')
    fp = open(str(target_file), 'wb')
    fp.write(screenshot_data)
    fp.close()
    assert target_file.size() > 30_000
