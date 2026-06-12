
def encode_pixel(n: int) -> tuple[int, int, int]:
    """Encode a 0–63 value into an (R, G, B) pixel using 4-level intensity."""
    r = ((n >> 4) & 0b11) * 85
    g = ((n >> 2) & 0b11) * 85
    b = (n & 0b11) * 85
    return (r, g, b)


def decode_pixel(pixel: tuple[int, int, int]) -> int:
    """Decode an (R, G, B) pixel back to a 0–63 value."""
    r, g, b = pixel
    ri = round(r / 85)
    gi = round(g / 85)
    bi = round(b / 85)
    return (ri << 4) | (gi << 2) | bi
