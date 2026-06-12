from densegrid.grid import (
    GRID_SIZE,
    QUIET_ZONE,
    FINDER_SIZE,
    make_grid,
    get_data_pixels,
    is_finder_region,
    is_timing_pixel,
)


def test_grid_constants():
    assert GRID_SIZE == 177
    assert QUIET_ZONE == 4
    assert FINDER_SIZE == 7


def test_make_grid_dimensions():
    grid = make_grid()
    assert len(grid) == GRID_SIZE
    assert all(len(row) == GRID_SIZE for row in grid)


def test_finder_top_left():
    grid = make_grid()
    # Top-left finder: 7x7 nested squares
    # Outer border should be black (0,0,0)
    assert grid[4][4] == (0, 0, 0)  # top-left corner of finder
    # Inner 3x3 should be black (center)
    assert grid[7][7] == (0, 0, 0)


def test_quiet_zone_is_white():
    grid = make_grid()
    # Top-left quiet zone
    assert grid[0][0] == (255, 255, 255)
    assert grid[3][3] == (255, 255, 255)


def test_timing_pattern():
    grid = make_grid()
    # Row 6 (index): alternating black/white starting after finder
    # Column 6 (index): alternating black/white starting after finder
    # At position (6, 11) should be black (even offset from finder edge)
    assert grid[6][11] == (0, 0, 0)
    # At position (6, 12) should be white
    assert grid[6][12] == (255, 255, 255)


def test_data_pixel_count():
    data_pixels = get_data_pixels()
    # Data region: rows 8–176, cols 8–176 = 169×169 = 28561
    # Minus the header row (12 pixels) and structural overlaps
    assert len(data_pixels) > 20000
    assert len(data_pixels) < 30000


def test_data_pixels_not_in_structural_regions():
    data_pixels = get_data_pixels()
    for (r, c) in data_pixels:
        assert not is_finder_region(r, c)
        assert r >= QUIET_ZONE + FINDER_SIZE + 1  # below timing row
        assert c >= QUIET_ZONE + FINDER_SIZE + 1  # right of timing col
