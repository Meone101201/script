"""
Pytest configuration and shared fixtures for RBXLX Extractor tests.
"""

import os
import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def get_fixture_path():
    def _path(filename: str) -> str:
        p = os.path.join(FIXTURES_DIR, filename)
        if not os.path.isfile(p):
            raise FileNotFoundError(f"Fixture not found: {p}")
        return p
    return _path
