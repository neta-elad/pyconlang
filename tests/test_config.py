from pyconlang.config import Config, config

from . import config_as


def test_config(modern_config: Config) -> None:
    with config_as(Config(scope="fake")):
        assert config().scope == "fake"

    assert config().scope == "modern"
