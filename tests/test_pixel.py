from densegrid.pixel import encode_pixel, decode_pixel


def test_encode_zero():
    assert encode_pixel(0) == (0, 0, 0)


def test_encode_max():
    assert encode_pixel(63) == (255, 255, 255)


def test_encode_red_only():
    assert encode_pixel(0b010000) == (85, 0, 0)


def test_encode_green_only():
    assert encode_pixel(0b000100) == (0, 85, 0)


def test_encode_blue_only():
    assert encode_pixel(0b000001) == (0, 0, 85)


def test_decode_all_levels():
    for level, value in enumerate([0, 85, 170, 255]):
        n = level << 4
        assert decode_pixel((value, 0, 0)) == n


def test_roundtrip_all_values():
    for n in range(64):
        assert decode_pixel(encode_pixel(n)) == n


def test_decode_tolerance():
    assert decode_pixel((170, 85, 255)) == 0b100111
