"""Tests for subcommands/logs.py — compose_logs and journalctl fallback."""

import json
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from rich.console import Console

from utils import ComposeError
from utils.compose import ServiceInfo


class TestFormatJournalLine:
    """``_format_journal_line`` parses JSON and prints formatted output."""

    def _capture(self, line: str, **kwargs: object) -> str:
        """Run ``_format_journal_line`` and return captured output."""
        from subcommands.logs import _format_journal_line

        buf = StringIO()
        console = Console(file=buf, force_terminal=False, no_color=True)
        _format_journal_line(line, console=console, **kwargs)  # type: ignore[arg-type]
        return buf.getvalue()

    def test_basic_message(self) -> None:
        entry = json.dumps(
            {
                "MESSAGE": "hello world",
                "PRIORITY": 6,
                "_SYSTEMD_UNIT": "myapp-web-1.service",
            }
        )
        output = self._capture(entry)
        assert "myapp-web-1 |" in output
        assert "hello world" in output

    def test_no_log_prefix(self) -> None:
        entry = json.dumps(
            {
                "MESSAGE": "hello",
                "PRIORITY": 6,
                "_SYSTEMD_UNIT": "myapp-web-1.service",
            }
        )
        output = self._capture(entry, no_log_prefix=True)
        assert "myapp-web-1 |" not in output
        assert "hello" in output

    def test_timestamps(self) -> None:
        # 2024-01-15T12:30:00.123456Z in microseconds
        ts_us = 1705318200123456
        entry = json.dumps(
            {
                "MESSAGE": "ts test",
                "PRIORITY": 6,
                "__REALTIME_TIMESTAMP": str(ts_us),
                "_SYSTEMD_UNIT": "myapp.service",
            }
        )
        output = self._capture(entry, timestamps=True)
        assert "2024-01-15T" in output
        assert "ts test" in output

    def test_empty_line_skipped(self) -> None:
        output = self._capture("   ")
        assert output == ""

    def test_invalid_json_printed_as_is(self) -> None:
        output = self._capture("not json at all")
        assert "not json at all" in output

    def test_missing_message_skipped(self) -> None:
        entry = json.dumps({"PRIORITY": 6, "_SYSTEMD_UNIT": "x.service"})
        output = self._capture(entry)
        assert output == ""

    def test_byte_array_message(self) -> None:
        entry = json.dumps(
            {
                "MESSAGE": [104, 101, 108, 108, 111],  # "hello"
                "PRIORITY": 6,
            }
        )
        output = self._capture(entry)
        assert "hello" in output

    def test_syslog_identifier_fallback(self) -> None:
        """When ``_SYSTEMD_UNIT`` is absent, use ``SYSLOG_IDENTIFIER``."""
        entry = json.dumps(
            {
                "MESSAGE": "msg",
                "PRIORITY": 6,
                "SYSLOG_IDENTIFIER": "myapp",
            }
        )
        output = self._capture(entry)
        assert "myapp |" in output

    def test_strips_service_suffix(self) -> None:
        """.service suffix is stripped from the unit name."""
        entry = json.dumps(
            {
                "MESSAGE": "msg",
                "PRIORITY": 6,
                "_SYSTEMD_UNIT": "myapp-web-1.service",
            }
        )
        output = self._capture(entry)
        assert "myapp-web-1 |" in output
        assert ".service |" not in output


class TestRunJournalctlJson:
    """``_run_journalctl_json`` invokes journalctl with ``--output=json``."""

    @patch("subcommands.logs.subprocess.run")
    def test_non_follow(self, mock_run: MagicMock) -> None:
        from subcommands.logs import _run_journalctl_json

        entry = json.dumps(
            {
                "MESSAGE": "test line",
                "PRIORITY": 6,
                "_SYSTEMD_UNIT": "myapp.service",
            }
        )
        mock_run.return_value = MagicMock(stdout=entry + "\n")

        buf = StringIO()
        with patch(
            "subcommands.logs.Console",
            return_value=Console(
                file=buf,
                force_terminal=False,
                no_color=True,
            ),
        ):
            _run_journalctl_json(
                ["journalctl", "--user"],
                no_color=True,
            )

        args = mock_run.call_args[0][0]
        assert "--output=json" in args
        assert "test line" in buf.getvalue()

    @patch("subcommands.logs.subprocess.run")
    def test_args_passed_through(self, mock_run: MagicMock) -> None:
        from subcommands.logs import _run_journalctl_json

        mock_run.return_value = MagicMock(stdout="")

        _run_journalctl_json(
            ["journalctl", "--user", "-u", "myapp.service", "--lines", "50"],
            no_color=True,
        )

        args = mock_run.call_args[0][0]
        assert "-u" in args
        assert "myapp.service" in args
        assert "--lines" in args
        assert "50" in args
        assert "--output=json" in args


class TestComposeLogsPodmanSuccess:
    """When podman logs succeeds, journalctl should NOT be called."""

    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_basic_invocation(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {"services": {"web": {"image": "nginx"}}}
        mock_info.return_value = ServiceInfo(
            project_name="myapp",
            container_names={"web": "myapp-web-1"},
            service_names=["web"],
            images={"web": "nginx"},
        )

        compose_logs()

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "podman"
        assert args[1] == "logs"
        assert "myapp-web-1" in args

    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_follow_flag(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )

        compose_logs(follow=True)

        args = mock_run.call_args[0][0]
        assert "--follow" in args

    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_since_and_until(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )

        compose_logs(since="2024-01-01", until="2024-01-02")

        args = mock_run.call_args[0][0]
        assert "--since" in args
        assert "2024-01-01" in args
        assert "--until" in args
        assert "2024-01-02" in args

    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_tail(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )

        compose_logs(tail=100)

        args = mock_run.call_args[0][0]
        assert "--tail" in args
        assert "100" in args


class TestComposeLogsJournalctlFallback:
    """When podman logs fails (ComposeError), fall back to journalctl."""

    @patch("subcommands.logs._run_journalctl_json")
    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_fallback_to_journalctl(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
        mock_journal: MagicMock,
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {"services": {"web": {"image": "nginx"}}}
        mock_info.return_value = ServiceInfo(
            project_name="myapp",
            container_names={"web": "myapp-web-1"},
            service_names=["web"],
            images={"web": "nginx"},
        )

        # podman logs fails, triggering journalctl fallback.
        mock_run.side_effect = ComposeError("no container")

        compose_logs()

        mock_journal.assert_called_once()
        journal_args = mock_journal.call_args[0][0]
        assert journal_args[0] == "journalctl"
        assert "--user" in journal_args
        assert "-u" in journal_args
        assert "myapp-web-1.service" in journal_args

    @patch("subcommands.logs._run_journalctl_json")
    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_fallback_preserves_follow(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
        mock_journal: MagicMock,
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )
        mock_run.side_effect = ComposeError("fail")

        compose_logs(follow=True)

        journal_args = mock_journal.call_args[0][0]
        assert "-f" in journal_args
        assert mock_journal.call_args[1]["follow"] is True

    @patch("subcommands.logs._run_journalctl_json")
    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_fallback_preserves_since(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
        mock_journal: MagicMock,
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )
        mock_run.side_effect = ComposeError("fail")

        compose_logs(since="1h ago")

        journal_args = mock_journal.call_args[0][0]
        assert "--since" in journal_args
        assert "1h ago" in journal_args

    @patch("subcommands.logs._run_journalctl_json")
    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_fallback_preserves_tail_as_lines(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
        mock_journal: MagicMock,
    ) -> None:
        """tail=N is translated to --lines=N for journalctl."""
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )
        mock_run.side_effect = ComposeError("fail")

        compose_logs(tail=50)

        journal_args = mock_journal.call_args[0][0]
        assert "--lines" in journal_args
        assert "50" in journal_args
        # Should NOT contain --tail (that's a podman-logs flag)
        assert "--tail" not in journal_args

    @patch("subcommands.logs._run_journalctl_json")
    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_fallback_preserves_until(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
        mock_journal: MagicMock,
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )
        mock_run.side_effect = ComposeError("fail")

        compose_logs(until="2024-06-01")

        journal_args = mock_journal.call_args[0][0]
        assert "--until" in journal_args
        assert "2024-06-01" in journal_args

    @patch("subcommands.logs._run_journalctl_json")
    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_fallback_multiple_containers(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
        mock_journal: MagicMock,
    ) -> None:
        """Each container gets a ``-u <name>.service`` entry."""
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1", "db": "myapp-db-1"},
        )
        mock_run.side_effect = ComposeError("fail")

        compose_logs()

        journal_args = mock_journal.call_args[0][0]
        # Both services should be present as -u name.service pairs
        assert "myapp-web-1.service" in journal_args
        assert "myapp-db-1.service" in journal_args

    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_no_fallback_when_podman_succeeds(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        """If podman logs succeeds, journalctl is never called."""
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )

        compose_logs()

        assert mock_run.call_count == 1
        assert mock_run.call_args[0][0][0] == "podman"

    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_podman_logs_called_with_check_true(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        """podman logs must be called with check=True so failures raise."""
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )

        compose_logs()

        first_call = mock_run.call_args_list[0]
        assert first_call[1].get("check") is True

    @patch("subcommands.logs._run_journalctl_json")
    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_fallback_passes_no_color(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
        mock_journal: MagicMock,
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )
        mock_run.side_effect = ComposeError("fail")

        compose_logs(no_color=True)

        assert mock_journal.call_args[1]["no_color"] is True

    @patch("subcommands.logs._run_journalctl_json")
    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_fallback_passes_no_log_prefix(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
        mock_journal: MagicMock,
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )
        mock_run.side_effect = ComposeError("fail")

        compose_logs(no_log_prefix=True)

        assert mock_journal.call_args[1]["no_log_prefix"] is True

    @patch("subcommands.logs._run_journalctl_json")
    @patch("subcommands.logs.run_cmd")
    @patch("subcommands.logs.get_service_info")
    @patch("subcommands.logs.parse_compose")
    @patch("subcommands.logs.resolve_compose_path")
    def test_fallback_passes_timestamps(
        self,
        mock_resolve: MagicMock,
        mock_parse: MagicMock,
        mock_info: MagicMock,
        mock_run: MagicMock,
        mock_journal: MagicMock,
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )
        mock_run.side_effect = ComposeError("fail")

        compose_logs(timestamps=True)

        assert mock_journal.call_args[1]["timestamps"] is True
