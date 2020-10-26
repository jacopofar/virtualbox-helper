import pytest

from virtualbox_helper import detect_fragment, image_diff_score


def test_region_match(tmpdir):
    with open('tests/match_data/debian_grub.png', 'rb') as fp:
        screenshot_data = fp.read()

    detection = detect_fragment(screenshot_data, 'tests/match_data/grub_fragment.png')
    assert detection is not None
    # it's basically an exact match
    assert detection[0] > 0.9
    assert detection[1] == (19, 59)
    assert detection[2] == (172, 114)
    target_file = tmpdir.join('grub_match_test.png')

    # no match at all
    no_match = detect_fragment(screenshot_data, 'tests/match_data/random_image.png')
    assert no_match is None

    # force a match by lowering the threshold
    forced_match = detect_fragment(screenshot_data, 'tests/match_data/random_image.png', threshold=0.001)
    assert forced_match is not None

    with pytest.raises(FileNotFoundError):
        detect_fragment(screenshot_data, 'non_existing_file.png')

    assert detection == detect_fragment(
        screenshot_data,
        'tests/match_data/grub_fragment.png',
        store_match=str(target_file)
        )
    assert target_file.size() > 30_000
    assert image_diff_score(target_file.read_binary(), 'tests/match_data/grub_match.png') < 0.001
