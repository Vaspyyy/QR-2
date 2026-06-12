def encode_pixel(n: int) -> tuple[int, int, int]:
    """Encode a 0-63 number into an (R, G, B) pixel.

    The 6-bit number is split into three 2-bit pairs:
    - bits 5-4: red
    - bits 3-2: green
    - bits 1-0: blue

    Each pair maps to: 0 -> 0, 1 -> 85, 2 -> 170, 3 -> 255.
    """

    def pair_to_color(pair: int) -> int:
        return pair * 85

    blue = pair_to_color(n & 0b11)  # bits 1-0
    green = pair_to_color((n >> 2) & 0b11)  # bits 3-2
    red = pair_to_color((n >> 4) & 0b11)  # bits 5-4

    return (red, green, blue)
