"""Tests for utils.progress — ProgressWriter and track_operation."""

import io
from unittest.mock import patch

import pytest

from utils.progress import (
    ProgressWriter,
    _colorize,
    _green,
    _red,
    _yellow,
    track_operation,
)


class TestAnsiHelpers:
    """Tests for ANSI escape-code helpers."""

    def test_green(self):
        result = _green("ok")
        assert result == "\033[32mok\033[0m"

    def test_red(self):
        result = _red("fail")
        assert result == "\033[31mfail\033[0m"

    def test_yellow(self):
        result = _yellow("warn")
        assert result == "\033[33mwarn\033[0m"


class TestColorize:
    """Tests for _colorize dispatch helper."""

    def test_green(self):
        assert _colorize("done", "green") == _green("done")

    def test_red(self):
        assert _colorize("err", "red") == _red("err")

    def test_yellow(self):
        assert _colorize("warn", "yellow") == _yellow("warn")

    def test_none_returns_plain(self):
        assert _colorize("plain", None) == "plain"

    def test_unknown_color_returns_plain(self):
        assert _colorize("plain", "blue") == "plain"


class TestProgressWriterNonTty:
    """Tests for ProgressWriter with a non-TTY stream (StringIO)."""

    def _writer(self) -> tuple[ProgressWriter, io.StringIO]:
        buf = io.StringIO()
        writer = ProgressWriter(stream=buf)
        assert not writer._is_tty
        return writer, buf

    def test_add_tracks_lines(self):
        writer, _ = self._writer()
        writer.add("Creating", "web")
        writer.add("Creating", "db")
        assert writer._lines == ["Creating web", "Creating db"]

    def test_add_updates_width(self):
        writer, _ = self._writer()
        writer.add("Creating", "web")
        assert writer._width == len("Creating web")
        writer.add("Starting", "really-long-service")
        assert writer._width == len("Starting really-long-service")

    def test_write_initial(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.add("Creating", "db")
        writer.write_initial()
        output = buf.getvalue()
        assert "Creating web" in output
        assert "Creating db" in output

    def test_write_initial_lines_end_with_newline(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.write_initial()
        assert buf.getvalue().endswith("\n")

    def test_update_non_tty_prints_new_line(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.write_initial()
        buf.truncate(0)
        buf.seek(0)

        writer.update("Creating", "web", "done", color="green")
        output = buf.getvalue()
        assert "Creating web" in output
        assert "done" in output
        assert output.endswith("\n")

    def test_update_non_tty_with_color(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.write_initial()
        buf.truncate(0)
        buf.seek(0)

        writer.update("Creating", "web", "done", color="green")
        output = buf.getvalue()
        assert _green("done") in output

    def test_update_non_tty_unknown_label_prints_anyway(self):
        """Updating a label that wasn't registered still prints (non-TTY)."""
        writer, buf = self._writer()
        writer.update("Creating", "unknown", "done")
        output = buf.getvalue()
        assert "Creating unknown" in output
        assert "done" in output


class TestProgressWriterTty:
    """Tests for ProgressWriter with a mock TTY stream."""

    def _writer(self) -> tuple[ProgressWriter, io.StringIO]:
        buf = _TtyStringIO()
        writer = ProgressWriter(stream=buf)
        assert writer._is_tty
        return writer, buf

    def test_write_initial(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.write_initial()
        output = buf.getvalue()
        assert "Creating web" in output

    def test_update_moves_cursor(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.add("Creating", "db")
        writer.write_initial()
        buf.truncate(0)
        buf.seek(0)

        writer.update("Creating", "web", "done", color="green")
        output = buf.getvalue()
        # Should contain ANSI cursor movement codes
        assert "\033[" in output
        assert "done" in output

    def test_update_unknown_label_prints_new_line(self):
        """Updating a label not in _lines falls back to non-ANSI path."""
        writer, buf = self._writer()
        writer.update("Creating", "unknown", "done")
        output = buf.getvalue()
        # Falls back to _write_noansi since label not in _lines
        assert "Creating unknown" in output
        assert "done" in output


class _TtyStringIO(io.StringIO):
    """StringIO that pretends to be a TTY."""

    def isatty(self) -> bool:
        return True


class TestTrackOperation:
    """Tests for the track_operation convenience function."""

    def test_successful_operations(self):
        buf = io.StringIO()
        results: list[str] = []

        track_operation(
            "Starting",
            ["web", "db"],
            results.append,
            stream=buf,
        )

        output = buf.getvalue()
        # Initial lines + update lines
        assert "Starting web" in output
        assert "Starting db" in output
        assert "done" in output
        assert results == ["web", "db"]

    def test_failed_operation_shows_error(self):
        buf = io.StringIO()

        def _fail(item: str) -> None:
            if item == "bad":
                raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            track_operation(
                "Starting",
                ["good", "bad"],
                _fail,
                stream=buf,
            )

        output = buf.getvalue()
        assert "error" in output

    def test_empty_items(self):
        buf = io.StringIO()
        track_operation("Starting", [], lambda x: None, stream=buf)
        assert buf.getvalue() == ""

    def test_single_item(self):
        buf = io.StringIO()
        results: list[str] = []

        track_operation(
            "Creating",
            ["web"],
            results.append,
            stream=buf,
        )

        output = buf.getvalue()
        assert "Creating web" in output
        assert "done" in output
        assert results == ["web"]
