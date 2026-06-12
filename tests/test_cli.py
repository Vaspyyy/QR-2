import os
import subprocess
import tempfile


def test_encode_help():
    result = subprocess.run(
        ["python", "-m", "densegrid.cli", "encode", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "input" in result.stdout.lower() or "file" in result.stdout.lower()


def test_decode_help():
    result = subprocess.run(
        ["python", "-m", "densegrid.cli", "decode", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0


def test_encode_decode_roundtrip_cli():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = os.path.join(tmpdir, "input.txt")
        png_file = os.path.join(tmpdir, "output.png")
        output_file = os.path.join(tmpdir, "recovered.txt")

        with open(input_file, "wb") as f:
            f.write(b"Hello from CLI!")

        # Encode
        result = subprocess.run(
            ["python", "-m", "densegrid.cli", "encode", input_file, "-o", png_file],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Encode failed: {result.stderr}"
        assert os.path.exists(png_file)

        # Decode
        result = subprocess.run(
            ["python", "-m", "densegrid.cli", "decode", png_file, "-o", output_file],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Decode failed: {result.stderr}"
        assert os.path.exists(output_file)

        with open(output_file, "rb") as f:
            assert f.read() == b"Hello from CLI!"
