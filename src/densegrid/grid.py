GRID_SIZE = 177
QUIET_ZONE = 4
FINDER_SIZE = 7
HEADER_PIXELS = 12

_BLACK = (0, 0, 0)
_WHITE = (255, 255, 255)

_FINDER_PATTERN = [
    [0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 0],
    [0, 1, 0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0, 1, 0],
    [0, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0],
]

_FINDER_POSITIONS = [
    (QUIET_ZONE, QUIET_ZONE),
    (QUIET_ZONE, GRID_SIZE - QUIET_ZONE - FINDER_SIZE),
    (GRID_SIZE - QUIET_ZONE - FINDER_SIZE, QUIET_ZONE),
]

_TIMING_ROW = FINDER_SIZE - 1
_TIMING_COL = FINDER_SIZE - 1
_FINDER_END = QUIET_ZONE + FINDER_SIZE
_TIMING_END = GRID_SIZE - QUIET_ZONE - FINDER_SIZE
_DATA_START = QUIET_ZONE + FINDER_SIZE + 1


def is_finder_region(r: int, c: int) -> bool:
    for fr, fc in _FINDER_POSITIONS:
        if fr <= r < fr + FINDER_SIZE and fc <= c < fc + FINDER_SIZE:
            return True
    return False


def is_timing_pixel(r: int, c: int) -> bool:
    if r == _TIMING_ROW and _FINDER_END <= c < _TIMING_END:
        return True
    if c == _TIMING_COL and _FINDER_END <= r < _TIMING_END:
        return True
    return False


def make_grid() -> list[list[tuple[int, int, int]]]:
    grid = [[_WHITE] * GRID_SIZE for _ in range(GRID_SIZE)]

    for fr, fc in _FINDER_POSITIONS:
        for dr in range(FINDER_SIZE):
            for dc in range(FINDER_SIZE):
                grid[fr + dr][fc + dc] = (
                    _BLACK if _FINDER_PATTERN[dr][dc] == 0 else _WHITE
                )

    for c in range(_FINDER_END, _TIMING_END):
        grid[_TIMING_ROW][c] = _BLACK if (c - _FINDER_END) % 2 == 0 else _WHITE

    for r in range(_FINDER_END, _TIMING_END):
        grid[r][_TIMING_COL] = _BLACK if (r - _FINDER_END) % 2 == 0 else _WHITE

    return grid


def get_data_pixels() -> list[tuple[int, int]]:
    result = []
    for r in range(_DATA_START, GRID_SIZE - QUIET_ZONE):
        for c in range(_DATA_START, GRID_SIZE - QUIET_ZONE):
            if not is_finder_region(r, c) and not is_timing_pixel(r, c):
                result.append((r, c))
    return result
