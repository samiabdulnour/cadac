from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def root() -> Path:
    """The repository itself: its own standards and example brief are the
    first things the checks must read."""
    return ROOT
