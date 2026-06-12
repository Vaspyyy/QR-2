import argparse
import sys
from densegrid.encode import encode_file
from densegrid.decode import decode_file


def encode_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="dgencode",
        description="Encode a file into a QR² dense-grid PNG image.",
    )
    parser.add_argument("input", help="Input file to encode")
    parser.add_argument("-o", "--output", required=True, help="Output PNG path")
    args = parser.parse_args(argv)

    with open(args.input, "rb") as f:
        payload = f.read()

    encode_file(payload, args.output)
    print(f"Encoded {len(payload)} bytes → {args.output}")


def decode_main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="dgdecode",
        description="Decode a QR² dense-grid PNG image back to the original file.",
    )
    parser.add_argument("input", help="Input PNG file to decode")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    args = parser.parse_args(argv)

    payload = decode_file(args.input)

    with open(args.output, "wb") as f:
        f.write(payload)

    print(f"Decoded {args.input} → {len(payload)} bytes")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "decode":
        decode_main(sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == "encode":
        encode_main(sys.argv[2:])
    else:
        encode_main(sys.argv[1:] if len(sys.argv) > 1 else None)
