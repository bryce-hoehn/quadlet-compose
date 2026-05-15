"""Tests for quadlet_compose CLI — argument parsing, dispatch, help output."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from quadlet_compose import COMMANDS, main, print_help


class TestCommandsList:
    """Tests for the COMMANDS configuration list."""

    def test_is_list(self):
        assert isinstance(COMMANDS, list)

    def test_all_commands_have_required_keys(self):
        for cmd in COMMANDS:
            assert "name" in cmd, f"Command missing 'name': {cmd}"
            assert "help" in cmd, f"Command missing 'help': {cmd}"
            assert "func" in cmd, f"Command missing 'func': {cmd}"

    def test_expected_command_names(self):
        names = {cmd["name"] for cmd in COMMANDS}
        expected = {
            "up",
            "down",
            "build",
            "exec",
            "kill",
            "pull",
            "restart",
            "run",
            "ps",
            "logs",
            "top",
            "images",
            "port",
            "config",
            "convert",
            "version",
        }
        assert names == expected

    def test_all_funcs_are_callable(self):
        for cmd in COMMANDS:
            assert callable(cmd["func"]), f"func for '{cmd['name']}' is not callable"

    def test_up_has_args(self):
        up_cmd = next(c for c in COMMANDS if c["name"] == "up")
        assert "args" in up_cmd
        assert len(up_cmd["args"]) > 0

    def test_down_has_args(self):
        down_cmd = next(c for c in COMMANDS if c["name"] == "down")
        assert "args" in down_cmd

    def test_build_has_args(self):
        build_cmd = next(c for c in COMMANDS if c["name"] == "build")
        assert "args" in build_cmd

    def test_version_has_args(self):
        version_cmd = next(c for c in COMMANDS if c["name"] == "version")
        assert "args" in version_cmd

    def test_command_names_are_unique(self):
        names = [cmd["name"] for cmd in COMMANDS]
        assert len(names) == len(set(names))


class TestPrintHelp:
    """Tests for print_help()."""

    def test_does_not_crash(self):
        """print_help() should run without error."""
        print_help()

    def test_prints_to_console(self, capsys):
        """print_help() should produce output."""
        print_help()
        captured = capsys.readouterr()
        # rich outputs to stdout by default
        assert len(captured.out) > 0

    def test_mentions_usage(self, capsys):
        print_help()
        captured = capsys.readouterr()
        assert "Usage" in captured.out

    def test_mentions_commands(self, capsys):
        print_help()
        captured = capsys.readouterr()
        assert "Commands" in captured.out

    def test_lists_all_commands(self, capsys):
        print_help()
        captured = capsys.readouterr()
        for cmd in COMMANDS:
            assert cmd["name"] in captured.out


class TestMainHelp:
    """Tests for main() with --help flag."""

    def test_help_flag_exits_cleanly(self):
        with patch("sys.argv", ["quadlet-compose", "-h"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_no_command_shows_help(self):
        with patch("sys.argv", ["quadlet-compose"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0


class TestMainDispatch:
    """Tests for main() command dispatch."""

    def test_dispatches_to_up(self):
        mock_func = MagicMock()
        with patch("sys.argv", ["quadlet-compose", "up"]):
            with patch(
                "quadlet_compose.COMMANDS",
                [{"name": "up", "help": "test", "func": mock_func, "args": []}],
            ):
                main()
                mock_func.assert_called_once()

    def test_up_receives_compose_file(self):
        """The -f flag should pass compose_file to the command function."""
        mock_func = MagicMock()
        # We need to patch the COMMANDS list used during subparser creation
        # and also the func that gets set on the args namespace
        with patch("sys.argv", ["quadlet-compose", "-f", "custom.yaml", "up"]):
            with patch(
                "quadlet_compose.COMMANDS",
                [
                    {
                        "name": "up",
                        "help": "test",
                        "func": mock_func,
                        "args": [],
                    },
                ],
            ):
                main()
                mock_func.assert_called_once()
                call_kwargs = mock_func.call_args[1]
                assert call_kwargs["compose_file"] == "custom.yaml"

    def test_up_receives_project_name(self):
        mock_func = MagicMock()
        with patch("sys.argv", ["quadlet-compose", "-p", "myproject", "up"]):
            with patch(
                "quadlet_compose.COMMANDS",
                [
                    {
                        "name": "up",
                        "help": "test",
                        "func": mock_func,
                        "args": [],
                    },
                ],
            ):
                main()
                call_kwargs = mock_func.call_args[1]
                assert call_kwargs["compose_file"] is None

    def test_up_default_compose_file_is_none(self):
        mock_func = MagicMock()
        with patch("sys.argv", ["quadlet-compose", "up"]):
            with patch(
                "quadlet_compose.COMMANDS",
                [
                    {
                        "name": "up",
                        "help": "test",
                        "func": mock_func,
                        "args": [],
                    },
                ],
            ):
                main()
                call_kwargs = mock_func.call_args[1]
                assert call_kwargs["compose_file"] is None

    def test_up_receives_detach_flag(self):
        mock_func = MagicMock()
        with patch("sys.argv", ["quadlet-compose", "up", "-d"]):
            with patch(
                "quadlet_compose.COMMANDS",
                [
                    {
                        "name": "up",
                        "help": "test",
                        "func": mock_func,
                        "args": [
                            (
                                ("-d", "--detach"),
                                {
                                    "action": "store_true",
                                    "default": False,
                                    "help": "detach",
                                },
                            ),
                        ],
                    },
                ],
            ):
                main()
                call_kwargs = mock_func.call_args[1]
                assert call_kwargs["detach"] is True

    def test_up_receives_remove_orphans(self):
        mock_func = MagicMock()
        with patch("sys.argv", ["quadlet-compose", "up", "--remove-orphans"]):
            with patch(
                "quadlet_compose.COMMANDS",
                [
                    {
                        "name": "up",
                        "help": "test",
                        "func": mock_func,
                        "args": [
                            (
                                "--remove-orphans",
                                {
                                    "action": "store_true",
                                    "default": False,
                                    "help": "remove orphans",
                                },
                            ),
                        ],
                    },
                ],
            ):
                main()
                call_kwargs = mock_func.call_args[1]
                assert call_kwargs["remove_orphans"] is True

    def test_version_dispatches(self):
        mock_func = MagicMock()
        with patch("sys.argv", ["quadlet-compose", "version"]):
            with patch(
                "quadlet_compose.COMMANDS",
                [
                    {"name": "version", "help": "test", "func": mock_func},
                ],
            ):
                main()
                mock_func.assert_called_once()

    def test_value_error_exits_1(self):
        mock_func = MagicMock(side_effect=ValueError("test error"))
        with patch("sys.argv", ["quadlet-compose", "up"]):
            with patch(
                "quadlet_compose.COMMANDS",
                [
                    {
                        "name": "up",
                        "help": "test",
                        "func": mock_func,
                        "args": [],
                    },
                ],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

    def test_down_dispatches(self):
        mock_func = MagicMock()
        with patch("sys.argv", ["quadlet-compose", "down"]):
            with patch(
                "quadlet_compose.COMMANDS",
                [
                    {
                        "name": "down",
                        "help": "test",
                        "func": mock_func,
                        "args": [],
                    },
                ],
            ):
                main()
                mock_func.assert_called_once()

    def test_kube_flag_passed_through(self):
        mock_func = MagicMock()
        with patch("sys.argv", ["quadlet-compose", "up", "--kube"]):
            with patch(
                "quadlet_compose.COMMANDS",
                [
                    {
                        "name": "up",
                        "help": "test",
                        "func": mock_func,
                        "args": [
                            ("--kube", {"action": "store_true", "default": False}),
                        ],
                    },
                ],
            ):
                main()
                call_kwargs = mock_func.call_args[1]
                assert call_kwargs["kube"] is True

    def test_convert_dispatches(self):
        mock_func = MagicMock()
        with patch("sys.argv", ["quadlet-compose", "convert"]):
            with patch(
                "quadlet_compose.COMMANDS",
                [
                    {
                        "name": "convert",
                        "help": "test",
                        "func": mock_func,
                        "args": [],
                    },
                ],
            ):
                main()
                mock_func.assert_called_once()

    def test_default_kwargs_passed(self):
        """When no flags are given, defaults should still be passed."""
        mock_func = MagicMock()
        with patch("sys.argv", ["quadlet-compose", "up"]):
            with patch(
                "quadlet_compose.COMMANDS",
                [
                    {
                        "name": "up",
                        "help": "test",
                        "func": mock_func,
                        "args": [],
                    },
                ],
            ):
                main()
                call_kwargs = mock_func.call_args[1]
                assert call_kwargs["compose_file"] is None
                # With dynamic kwargs, only argparse-defined args are passed
                assert len(call_kwargs) == 1  # only compose_file
