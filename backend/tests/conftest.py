import pytest

from medievaia.srd import parse_srd


@pytest.fixture(scope="session")
def srd_documents():
    return parse_srd()
