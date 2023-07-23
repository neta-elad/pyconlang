from pyconlang.metadata import Metadata

from . import metadata_as


def test_metadata(metadata: None) -> None:
    with metadata_as(Metadata(scope="fake")):
        assert Metadata.default().scope == "fake"

    assert Metadata.default().scope == "modern"
