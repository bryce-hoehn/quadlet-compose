"""Tests for hacks.interpolate — variable substitution."""

import pytest

from hacks.interpolate import _substitute


class TestInterpolate:
    """Test $VAR and ${VAR} substitution patterns."""

    def test_dollar_without_braces(self):
        assert _substitute("Hello $NAME!", {"NAME": "Alice"}) == "Hello Alice!"

    def test_dollar_with_braces(self):
        assert _substitute("Hello ${NAME}", {"NAME": "Alice"}) == "Hello Alice"

    def test_unset_variable_replaced_with_empty(self):
        """Unresolved variables become empty strings (docker-compose behavior)."""
        assert _substitute("Hello ${NAME}", {}) == "Hello "

    def test_unset_variable_no_braces(self):
        assert _substitute("Value: $VAR", {}) == "Value: "

    def test_escaped_dollar(self):
        """$$ is treated as a literal $ escape."""
        assert _substitute("$$literal", {}) == "$literal"

    def test_escaped_dollar_with_var(self):
        assert _substitute("$$${AMOUNT}", {"AMOUNT": "100"}) == "$100"

    def test_empty_variable_value(self):
        assert _substitute("Value: ${VAR}", {"VAR": ""}) == "Value: "

    def test_multiple_variables(self):
        assert _substitute(
            "${GREETING} ${NAME}!", {"GREETING": "Hello", "NAME": "World"}
        ) == "Hello World!"

    def test_variable_in_middle_of_text(self):
        assert _substitute(
            "host=${HOST}:port=${PORT}", {"HOST": "db", "PORT": "5432"}
        ) == "host=db:port=5432"

    def test_same_variable_multiple_times(self):
        assert _substitute(
            "$FOO and $FOO", {"FOO": "bar"}
        ) == "bar and bar"

    def test_no_variables(self):
        assert _substitute("plain text", {}) == "plain text"

    def test_empty_string(self):
        assert _substitute("", {"FOO": "bar"}) == ""

    def test_numeric_value(self):
        assert _substitute("port=${PORT}", {"PORT": "8080"}) == "port=8080"

    def test_variable_with_underscores(self):
        assert _substitute(
            "${MY_VAR}", {"MY_VAR": "works"}
        ) == "works"

    def test_adjacent_variables(self):
        assert _substitute(
            "${A}${B}", {"A": "hello", "B": "world"}
        ) == "helloworld"


class TestDockerDefaultSyntax:
    """Test Docker-style ${VAR:-default}, ${VAR-default}, etc."""

    def test_default_if_unset_or_empty(self):
        """${VAR:-default} uses default when VAR is unset or empty."""
        assert _substitute("${HOST:-localhost}", {}) == "localhost"
        assert _substitute("${HOST:-localhost}", {"HOST": ""}) == "localhost"

    def test_default_if_unset_or_empty_with_value(self):
        """${VAR:-default} uses VAR when set and non-empty."""
        assert _substitute("${HOST:-localhost}", {"HOST": "db"}) == "db"

    def test_default_if_unset_only(self):
        """${VAR-default} uses default only when VAR is unset."""
        assert _substitute("${HOST-localhost}", {}) == "localhost"

    def test_default_if_unset_keeps_empty(self):
        """${VAR-default} keeps empty string when VAR is set to empty."""
        assert _substitute("${HOST-localhost}", {"HOST": ""}) == ""

    def test_default_if_unset_with_value(self):
        """${VAR-default} uses VAR when set."""
        assert _substitute("${HOST-localhost}", {"HOST": "db"}) == "db"

    def test_alt_if_set_and_nonempty(self):
        """${VAR:+alt} uses alt when VAR is set and non-empty."""
        assert _substitute("${DEBUG:+--verbose}", {"DEBUG": "1"}) == "--verbose"

    def test_alt_if_set_and_empty(self):
        """${VAR:+alt} returns empty when VAR is set but empty."""
        assert _substitute("${DEBUG:+--verbose}", {"DEBUG": ""}) == ""

    def test_alt_if_set_and_unset(self):
        """${VAR:+alt} returns empty when VAR is unset."""
        assert _substitute("${DEBUG:+--verbose}", {}) == ""

    def test_alt_if_set_any(self):
        """${VAR+alt} uses alt when VAR is set (even if empty)."""
        assert _substitute("${DEBUG+--verbose}", {"DEBUG": ""}) == "--verbose"

    def test_alt_if_set_unset(self):
        """${VAR+alt} returns empty when VAR is unset."""
        assert _substitute("${DEBUG+--verbose}", {}) == ""

    def test_default_with_colon_priority(self):
        """${VAR:-default} takes priority over ${VAR-default} matching."""
        assert _substitute("${VAR:-fallback}", {"VAR": ""}) == "fallback"

    def test_complex_default_value(self):
        """Default values can contain complex strings."""
        assert _substitute(
            "${DB_URL:-postgres://localhost:5432/mydb}", {}
        ) == "postgres://localhost:5432/mydb"
