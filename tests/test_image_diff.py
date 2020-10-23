from virtualbox_runner import image_diff_score


def test_image_diff():
    with open('tests/match_data/random_image.png', 'rb') as rif:
        data1 = rif.read()
        assert image_diff_score(data1, 'tests/match_data/random_image.png') == 0.0

    with open('tests/match_data/random_image.png', 'rb') as rif:
        data1 = rif.read()
        assert image_diff_score(data1, 'tests/match_data/random_image2.png') > 0.0
