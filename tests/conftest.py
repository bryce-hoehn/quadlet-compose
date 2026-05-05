"""Shared test fixtures for podlet-compose."""

from pathlib import Path

import pytest

# Root paths used across test modules
PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = Path(__file__).parent / "fixtures"
TEST_COMPOSE_DIR = PROJECT_ROOT / "test-compose"


@pytest.fixture
def compose_path():
    """Path to the test-compose/compose.yaml fixture."""
    return TEST_COMPOSE_DIR / "compose.yaml"


@pytest.fixture
def fixtures_dir():
    """Path to the tests/fixtures/ directory."""
    return FIXTURES_DIR
