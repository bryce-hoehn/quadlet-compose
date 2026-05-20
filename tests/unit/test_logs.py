"""Tests for subcommands/logs.py — compose_logs and journalctl fallback."""

from pathlib import Path
from unittest.mock import MagicMock, call, patch

from utils import ComposeError
from utils.compose import ServiceInfo


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

        # First call (podman logs) fails, second call (journalctl) succeeds.
        mock_run.side_effect = [ComposeError("no container"), None]

        compose_logs()

        assert mock_run.call_count == 2
        # First call: podman logs
        first_args = mock_run.call_args_list[0][0][0]
        assert first_args[0] == "podman"
        # Second call: journalctl
        second_args = mock_run.call_args_list[1][0][0]
        assert second_args[0] == "journalctl"
        assert "--user" in second_args
        assert "-u" in second_args
        assert "myapp-web-1.service" in second_args

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
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )
        mock_run.side_effect = [ComposeError("fail"), None]

        compose_logs(follow=True)

        second_args = mock_run.call_args_list[1][0][0]
        assert "-f" in second_args

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
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )
        mock_run.side_effect = [ComposeError("fail"), None]

        compose_logs(since="1h ago")

        second_args = mock_run.call_args_list[1][0][0]
        assert "--since" in second_args
        assert "1h ago" in second_args

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
    ) -> None:
        """tail=N is translated to --lines=N for journalctl."""
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )
        mock_run.side_effect = [ComposeError("fail"), None]

        compose_logs(tail=50)

        second_args = mock_run.call_args_list[1][0][0]
        assert "--lines" in second_args
        assert "50" in second_args
        # Should NOT contain --tail (that's a podman-logs flag)
        assert "--tail" not in second_args

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
    ) -> None:
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1"},
        )
        mock_run.side_effect = [ComposeError("fail"), None]

        compose_logs(until="2024-06-01")

        second_args = mock_run.call_args_list[1][0][0]
        assert "--until" in second_args
        assert "2024-06-01" in second_args

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
    ) -> None:
        """Each container gets a ``-u <name>.service`` entry."""
        from subcommands.logs import compose_logs

        mock_resolve.return_value = Path("/fake/compose.yml")
        mock_parse.return_value = {}
        mock_info.return_value = ServiceInfo(
            container_names={"web": "myapp-web-1", "db": "myapp-db-1"},
        )
        mock_run.side_effect = [ComposeError("fail"), None]

        compose_logs()

        second_args = mock_run.call_args_list[1][0][0]
        # Both services should be present as -u name.service pairs
        assert "myapp-web-1.service" in second_args
        assert "myapp-db-1.service" in second_args

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
