import pytest
import numpy as np

from virtualbox_runner import image_diff_score


def test_image_diff():
    # an image is identical to itself
    assert image_diff_score(
        'tests/match_data/random_image.png',
        'tests/match_data/random_image.png',
        ) == 0.0
    # around 11% of pixels in these images are different
    assert image_diff_score(
        'tests/match_data/random_image.png',
        'tests/match_data/random_image2.png',
        ) > 0.1
    # considering the colors, the difference is smaller
    assert image_diff_score(
        'tests/match_data/random_image.png',
        'tests/match_data/random_image2.png',
        binary_diff=False,
    ) == pytest.approx(0.058, 0.01)

    totally_black = np.zeros((100, 200, 3), np.uint8)
    totally_white = np.ones((100, 200, 3), np.uint8) * 255
    totally_red = np.dstack(
        (totally_white[:, :, 0], totally_black[:, :, 1:])
        ).astype(np.uint8)
    # they are 100% different with both comparison methods
    assert image_diff_score(totally_black, totally_white) == 1.0
    assert image_diff_score(totally_black, totally_white, binary_diff=False) == 1.0
    # the function is commutative
    assert image_diff_score(totally_white, totally_black) == 1.0
    assert image_diff_score(totally_white, totally_black, binary_diff=False) == 1.0
    # if we consider the color one method is different
    assert image_diff_score(totally_black, totally_red) == 1.0
    assert image_diff_score(
        totally_black,
        totally_red,
        binary_diff=False,
        ) == pytest.approx(1 / 3, 0.001)

    rng = np.random.default_rng(seed=1)
    w = 800
    h = 600
    rand_img = rng.integers(0, 255, size=(w, h, 3), dtype=np.uint8)

    rand_img[12][42] = [0, 255, 0]
    rand_img2 = rand_img.copy()
    rand_img2[12][42] = [128, 128, 128]
    assert image_diff_score(rand_img, rand_img2) == 1 / (h * w)
    assert image_diff_score(
        rand_img,
        rand_img2,
        binary_diff=False,
        ) == pytest.approx((128 * 2 + 127) / (255 * 3) / (h * w), 0.001)
