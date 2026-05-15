"""Tests for utils/converters/_duration.py."""

from utils.converters._duration import _parse_duration_seconds


class TestParseDurationSeconds:
    """Tests for _parse_duration_seconds()."""

    # -- Plain integers --

    def test_int_zero(self) -> None:
        assert _parse_duration_seconds(0) == 0

    def test_int_positive(self) -> None:
        assert _parse_duration_seconds(30) == 30

    def test_int_large(self) -> None:
        assert _parse_duration_seconds(3600) == 3600

    # -- Plain floats --

    def test_float(self) -> None:
        assert _parse_duration_seconds(1.5) == 1

    def test_float_zero(self) -> None:
        assert _parse_duration_seconds(0.0) == 0

    # -- String numbers --

    def test_string_int(self) -> None:
        assert _parse_duration_seconds("30") == 30

    def test_string_float(self) -> None:
        assert _parse_duration_seconds("1.5") == 1

    def test_string_zero(self) -> None:
        assert _parse_duration_seconds("0") == 0

    # -- Go-style durations --

    def test_seconds_only(self) -> None:
        assert _parse_duration_seconds("10s") == 10

    def test_minutes_only(self) -> None:
        assert _parse_duration_seconds("5m") == 300

    def test_hours_only(self) -> None:
        assert _parse_duration_seconds("2h") == 7200

    def test_hours_minutes_seconds(self) -> None:
        assert _parse_duration_seconds("1h30m10s") == 5410

    def test_hours_and_minutes(self) -> None:
        assert _parse_duration_seconds("1h30m") == 5400

    def test_minutes_and_seconds(self) -> None:
        assert _parse_duration_seconds("90m30s") == 5430

    # -- Edge cases --

    def test_empty_string(self) -> None:
        assert _parse_duration_seconds("") == 0

    def test_whitespace_string(self) -> None:
        assert _parse_duration_seconds("   ") == 0

    def test_whitespace_around_number(self) -> None:
        assert _parse_duration_seconds("  30  ") == 30
