from pathlib import Path

import pytest

from Carapace.main import load_source
from Carapace.src.errors import SourceFileError


# ===========================================================================
# Source file validation
# ===========================================================================


def test_load_source_reads_utf8_cara_file(tmp_path):
    """A readable .cara file is loaded as UTF-8 source text."""
    source = tmp_path / "program.cara"
    source.write_text("FORWARD 10\n", encoding="utf-8")

    assert load_source(source) == "FORWARD 10\n"


def test_load_source_rejects_wrong_extension(tmp_path):
    """Only .cara files are accepted as Carapace source files."""
    source = tmp_path / "program.txt"
    source.write_text("FORWARD 10", encoding="utf-8")

    with pytest.raises(SourceFileError, match="extension"):
        load_source(source)


def test_load_source_rejects_missing_file(tmp_path):
    """A missing source path is reported through SourceFileError."""
    source = tmp_path / "missing.cara"

    with pytest.raises(SourceFileError, match="not found"):
        load_source(source)


def test_load_source_rejects_directory(tmp_path):
    """A directory with a .cara suffix is not a valid source file."""
    source = tmp_path / "folder.cara"
    source.mkdir()

    with pytest.raises(SourceFileError, match="not a file"):
        load_source(source)


def test_load_source_wraps_invalid_utf8(tmp_path):
    """Decoding failures are normalized into the public source-file error type."""
    source = tmp_path / "program.cara"
    source.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(SourceFileError, match="Cannot read source file"):
        load_source(source)
