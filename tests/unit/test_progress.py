"""Tests for utils.progress — ProgressWriter and track_operation."""

import io
import re
import time
from unittest.mock import patch

import pytest

from utils.progress import (
    ProgressWriter,
    _colorize,
    _format_elapsed,
    _green,
    _red,
    _status_icon,
    _visible_len,
    _yellow,
    track_operation,
)


# ── Colour helpers ─────────────────────────────────────────────────────


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


# ── Formatting helpers ─────────────────────────────────────────────────


class TestVisibleLen:
    """Tests for _visible_len."""

    def test_plain_string(self):
        assert _visible_len("hello") == 5

    def test_string_with_ansi(self):
        colored = _green("ok")
        assert _visible_len(colored) == 2

    def test_empty_string(self):
        assert _visible_len("") == 0

    def test_multiple_ansi_codes(self):
        s = f"{_green('a')}{_red('b')}"
        assert _visible_len(s) == 2


class TestFormatElapsed:
    """Tests for _format_elapsed."""

    def test_sub_second(self):
        assert _format_elapsed(0.5) == "0.5s"

    def test_zero(self):
        assert _format_elapsed(0.0) == "0.0s"

    def test_negative_clamps_to_zero(self):
        assert _format_elapsed(-1.0) == "0.0s"

    def test_seconds(self):
        assert _format_elapsed(5.3) == "5.3s"

    def test_minutes_and_seconds(self):
        assert _format_elapsed(65.0) == "1m 5s"

    def test_exact_minute(self):
        assert _format_elapsed(60.0) == "1m 0s"

    def test_large_minutes(self):
        assert _format_elapsed(185.0) == "3m 5s"


class TestStatusIcon:
    """Tests for _status_icon."""

    def test_done_no_color(self):
        assert _status_icon("done", None) == "✔"

    def test_error_no_color(self):
        assert _status_icon("error", None) == "✗"

    def test_error_capitalized(self):
        assert _status_icon("Error", None) == "✗"

    def test_failed_no_color(self):
        assert _status_icon("failed", None) == "⚠"

    def test_unknown_status(self):
        assert _status_icon("unknown", None) == "•"

    def test_done_with_color(self):
        icon = _status_icon("done", "green")
        assert "✔" in icon
        assert "\033[" in icon

    def test_error_with_color(self):
        icon = _status_icon("error", "red")
        assert "✗" in icon
        assert "\033[" in icon


# ── ProgressWriter (non-TTY) ───────────────────────────────────────────


class TestProgressWriterNonTty:
    """Tests for ProgressWriter with a non-TTY stream (StringIO)."""

    def _writer(self) -> tuple[ProgressWriter, io.StringIO]:
        buf = io.StringIO()
        writer = ProgressWriter(stream=buf)
        assert not writer._is_tty
        return writer, buf

    def test_add_tracks_labels(self):
        writer, _ = self._writer()
        writer.add("Creating", "web")
        writer.add("Creating", "db")
        assert writer._labels == ["Creating web", "Creating db"]

    def test_write_initial_is_noop(self):
        """On non-TTY, write_initial() produces no output."""
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.write_initial()
        assert buf.getvalue() == ""

    def test_update_prints_plain_line(self):
        writer, buf = self._writer()
        writer.add("Pulling", "nginx")
        writer.write_initial()

        writer.update("Pulling", "nginx", "done", color="green")
        output = buf.getvalue()
        assert "Pulling nginx" in output
        assert "done" in output
        assert output.endswith("\n")

    def test_update_includes_elapsed(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.write_initial()

        writer.update("Creating", "web", "done", color="green")
        output = buf.getvalue()
        # Strip ANSI codes to check elapsed pattern
        plain = re.sub(r"\033\[[0-9;]*m", "", output)
        assert re.search(r"done\s+\d+\.\d+s", plain)

    def test_update_with_color(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.write_initial()

        writer.update("Creating", "web", "done", color="green")
        output = buf.getvalue()
        assert _green("done") in output

    def test_update_unknown_label_prints_anyway(self):
        """Updating a label that wasn't registered still prints (non-TTY)."""
        writer, buf = self._writer()
        writer.update("Creating", "unknown", "done")
        output = buf.getvalue()
        assert "Creating unknown" in output
        assert "done" in output

    def test_finish_is_noop_without_spinner(self):
        """finish() on non-TTY should not error."""
        writer, _ = self._writer()
        writer.finish()  # should not raise


# ── ProgressWriter (TTY) ───────────────────────────────────────────────


class _TtyStringIO(io.StringIO):
    """StringIO that pretends to be a TTY."""

    def isatty(self) -> bool:
        return True


class TestProgressWriterTty:
    """Tests for ProgressWriter with a mock TTY stream."""

    def _writer(self) -> tuple[ProgressWriter, _TtyStringIO]:
        buf = _TtyStringIO()
        writer = ProgressWriter(stream=buf)
        assert writer._is_tty
        return writer, buf

    def test_write_initial_starts_spinner(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.write_initial()

        # Spinner thread should have been created
        assert writer._spinner_thread is not None
        writer.finish()  # clean up

    def test_write_initial_records_start_time(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.write_initial()

        assert "Creating web" in writer._start_times
        writer.finish()

    def test_update_stops_spinner_and_writes_line(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.write_initial()
        buf.truncate(0)
        buf.seek(0)

        writer.update("Creating", "web", "done", color="green")
        # Spinner should be stopped now
        assert writer._spinner_thread is None

        output = buf.getvalue()
        assert "Creating web" in output
        assert "done" in output

    def test_update_right_aligns_status(self):
        writer, buf = self._writer()
        writer._term_width = 60
        writer.add("Creating", "web")
        writer.write_initial()
        buf.truncate(0)
        buf.seek(0)

        writer.update("Creating", "web", "done", color="green")
        output = buf.getvalue()
        # Strip ANSI codes for length check
        plain = re.sub(r"\033\[[0-9;]*m", "", output).strip()
        # The visible line should be approximately term_width
        assert len(plain) >= len("Creating web") + len("✔ done 0.0s")

    def test_update_advances_to_next_item(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.add("Creating", "db")
        writer.write_initial()

        writer.update("Creating", "web", "done", color="green")
        # Should have started spinner on next item
        assert writer._spinner_thread is not None
        assert "Creating db" in writer._start_times
        writer.finish()

    def test_update_unknown_label_falls_back_to_plain(self):
        """Updating a label not in _labels falls back to _write_plain."""
        writer, buf = self._writer()
        writer.update("Creating", "unknown", "done")
        output = buf.getvalue()
        assert "Creating unknown" in output
        assert "done" in output

    def test_finish_stops_spinner(self):
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.write_initial()
        assert writer._spinner_thread is not None

        writer.finish()
        assert writer._spinner_thread is None

    def test_finish_idempotent(self):
        writer, buf = self._writer()
        writer.finish()  # no spinner — should not raise
        writer.finish()  # double finish — should not raise

    def test_spinner_writes_frames(self):
        """Spinner thread should write Braille frames to the stream."""
        writer, buf = self._writer()
        writer.add("Creating", "web")
        writer.write_initial()

        # Let spinner run for a few frames
        time.sleep(0.15)
        writer.finish()

        output = buf.getvalue()
        # Should contain at least one Braille frame character
        braille_chars = set("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
        assert any(c in output for c in braille_chars)

    def test_empty_labels_write_initial_is_noop(self):
        writer, buf = self._writer()
        writer.write_initial()
        assert writer._spinner_thread is None


# ── track_operation ────────────────────────────────────────────────────


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

    def test_finish_called_on_success(self):
        """track_operation should call finish() after success."""
        buf = io.StringIO()
        writer = None

        original_init = ProgressWriter.__init__

        def capture_init(self, stream=None):
            original_init(self, stream)
            nonlocal writer
            writer = self

        with patch.object(ProgressWriter, "__init__", capture_init):
            track_operation("Starting", ["web"], lambda x: None, stream=buf)

        assert writer is not None
        assert writer._spinner_thread is None

    def test_finish_called_on_error(self):
        """track_operation should call finish() even when func raises."""
        buf = io.StringIO()
        writer = None

        original_init = ProgressWriter.__init__

        def capture_init(self, stream=None):
            original_init(self, stream)
            nonlocal writer
            writer = self

        def _fail(item: str) -> None:
            raise RuntimeError("boom")

        with (
            patch.object(ProgressWriter, "__init__", capture_init),
            pytest.raises(RuntimeError, match="boom"),
        ):
            track_operation("Starting", ["bad"], _fail, stream=buf)

        assert writer is not None
        assert writer._spinner_thread is None
