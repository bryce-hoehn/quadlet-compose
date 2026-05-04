"""Tests for utils.compose._interpolate — variable substitution."""

import pytest

from utils.compose import _interpolate


class TestInterpolate:
    """Test $VAR and ${VAR} substitution patterns."""

    def test_dollar_without_braces(self):
        assert _interpolate("Hello $NAME!", {"NAME": "Alice"}) == "Hello Alice!"

    def test_dollar_with_braces(self):
        assert _interpolate("Hello ${NAME}", {"NAME": "Alice"}) == "Hello Alice"

    def test_unset_variable_replaced_with_empty(self):
        """Unresolved variables become empty strings (docker-compose behavior)."""
        assert _interpolate("Hello ${NAME}", {}) == "Hello "

    def test_unset_variable_no_braces(self):
        assert _interpolate("Value: $VAR", {}) == "Value: "

    def test_escaped_dollar(self):
        """$$ is treated as a literal $ escape."""
        assert _interpolate("$$literal", {}) == "$literal"

    def test_escaped_dollar_with_var(self):
        assert _interpolate("$$${AMOUNT}", {"AMOUNT": "100"}) == "$100"

    def test_empty_variable_value(self):
        assert _interpolate("Value: ${VAR}", {"VAR": ""}) == "Value: "

    def test_multiple_variables(self):
        assert _interpolate(
            "${GREETING} ${NAME}!", {"GREETING": "Hello", "NAME": "World"}
        ) == "Hello World!"

    def test_variable_in_middle_of_text(self):
        assert _interpolate(
            "host=${HOST}:port=${PORT}", {"HOST": "db", "PORT": "5432"}
        ) == "host=db:port=5432"

    def test_same_variable_multiple_times(self):
        assert _interpolate(
            "$FOO and $FOO", {"FOO": "bar"}
        ) == "bar and bar"

    def test_no_variables(self):
        assert _interpolate("plain text", {}) == "plain text"

    def test_empty_string(self):
        assert _interpolate("", {"FOO": "bar"}) == ""

    def test_numeric_value(self):
        """Template.substitute requires string values."""
        assert _interpolate("port=${PORT}", {"PORT": "8080"}) == "port=8080"

    def test_variable_with_underscores(self):
        assert _interpolate(
            "${MY_VAR}", {"MY_VAR": "works"}
        ) == "works"

    def test_adjacent_variables(self):
        assert _interpolate(
            "${A}${B}", {"A": "hello", "B": "world"}
        ) == "helloworld"
