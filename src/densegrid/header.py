import zlib

from densegrid.pixel import encode_pixel, decode_pixel

MAGIC = 0xD47
FORMAT_VERSION = 1
HEADER_LENGTH = 12


def pack_header(payload_size: int, version: int, payload: bytes) -> list[tuple[int, int, int]]:
    """Pack metadata into 12 encoded pixel tuples.

    Layout (each value is 6-bit, one pixel):
      0-1:  magic (12 bits)
      2-5:  payload size (24 bits, up to 16MB)
      6-7:  format version (12 bits)
      8-11: CRC32 low 24 bits (4 x 6-bit)
    """
    checksum = zlib.crc32(payload) & 0xFFFFFF

    values = [
        (MAGIC >> 6) & 0x3F,
        MAGIC & 0x3F,
        (payload_size >> 18) & 0x3F,
        (payload_size >> 12) & 0x3F,
        (payload_size >> 6) & 0x3F,
        payload_size & 0x3F,
        (version >> 6) & 0x3F,
        version & 0x3F,
        (checksum >> 18) & 0x3F,
        (checksum >> 12) & 0x3F,
        (checksum >> 6) & 0x3F,
        checksum & 0x3F,
    ]

    return [encode_pixel(v) for v in values]


def unpack_header(pixels: list[tuple[int, int, int]]) -> tuple[int, int, int, int, int]:
    """Unpack 12 pixel tuples into header metadata.

    Returns (payload_size, version, crc32_checksum, grid_width, grid_height).
    grid_width and grid_height are 0 for default (square) grids.
    """
    values = [decode_pixel(p) for p in pixels]

    magic = (values[0] << 6) | values[1]
    if magic != MAGIC:
        raise ValueError(f"Bad magic: expected 0x{MAGIC:X}, got 0x{magic:X}")

    payload_size = (values[2] << 18) | (values[3] << 12) | (values[4] << 6) | values[5]
    version = (values[6] << 6) | values[7]
    checksum = (values[8] << 18) | (values[9] << 12) | (values[10] << 6) | values[11]

    return payload_size, version, checksum, 0, 0
