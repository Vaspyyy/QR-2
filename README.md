# QR² (Dense Grid)

A high-density 2D barcode format. Looks like a QR code, stores 5× more data.

Instead of binary black/white pixels, each pixel encodes **6 bits** using 4 intensity levels per RGB channel. A single 177×177 image holds ~19 KB — compared to ~3 KB for a QR Version 40.

## Install

```bash
pip install -e .
```

Requires Python 3.10+, zero external dependencies.

## Usage

```bash
# Encode a file to QR² PNG
dgencode myfile.txt -o output.png

# Decode it back
dgdecode output.png -o recovered.txt
```

## How it works

Each pixel in the data region carries 2 bits in Red + 2 bits in Green + 2 bits in Blue = 6 bits total.

| Channel | Level 0 | Level 1 | Level 2 | Level 3 |
|---------|---------|---------|---------|---------|
| Value   | 0       | 85      | 170     | 255     |
| Bits    | 00      | 01      | 10      | 11      |

The image retains QR code structure (finder patterns, timing patterns, quiet zone) so it's instantly recognizable. Everything outside structural elements is data.

**Header format** (12 pixels): magic `0xD47`, payload size (24-bit), format version, CRC32 checksum.

## Tests

```bash
source .venv/bin/activate
pytest
```

32 tests covering pixel encoding, grid layout, header pack/unpack, PNG I/O, full roundtrip, and CLI.

## Project structure

```
src/densegrid/
├── pixel.py      — 6-bit RGB encode/decode
├── grid.py       — 177×177 layout (finders, timing, data region)
├── header.py     — magic, size, version, CRC32
├── png.py        — minimal PNG encoder/decoder (stdlib only)
├── encode.py     — file → QR² PNG
├── decode.py     — QR² PNG → file
└── cli.py        — dgencode / dgdecode commands
```

## Limitations

- Single image only (~19 KB max per file)
- Digital-only (no print/camera — exact pixel values required)
- PNG format only (no JPEG — lossy compression destroys data)

## Future

- Multi-image sequences for larger files
- Higher density modes (8/16/256 levels per channel)
- BMP support
