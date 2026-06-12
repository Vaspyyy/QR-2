import zlib
from densegrid.header import (
    MAGIC,
    FORMAT_VERSION,
    pack_header,
    unpack_header,
)


def test_magic_value():
    assert MAGIC == 0xD47


def test_pack_unpack_roundtrip():
    payload = b"Hello, QR2!"
    header = pack_header(len(payload), FORMAT_VERSION, payload)
    size, version, checksum = unpack_header(header)
    assert size == len(payload)
    assert version == FORMAT_VERSION
    assert checksum == zlib.crc32(payload) & 0xFFFFFF


def test_pack_header_length():
    header = pack_header(100, 1, b"x" * 100)
    assert len(header) == 12  # 12 pixels


def test_unpack_magic():
    header = pack_header(10, 1, b"test")
    from densegrid.pixel import decode_pixel
    p0 = decode_pixel(header[0])
    p1 = decode_pixel(header[1])
    magic = (p0 << 6) | p1
    assert magic == MAGIC


def test_large_payload_size():
    payload = b"\x00" * 100000
    header = pack_header(len(payload), 1, payload)
    size, version, checksum = unpack_header(header)
    assert size == 100000
    assert checksum == zlib.crc32(payload) & 0xFFFFFF
