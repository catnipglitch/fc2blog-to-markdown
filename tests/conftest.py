from pathlib import Path

import pytest

SAMPLE_PATH = Path(__file__).parent.parent / "sample" / "sample-fc2-export.txt"


@pytest.fixture(scope="session")
def sample_text() -> str:
    return SAMPLE_PATH.read_text(encoding="utf-8")
