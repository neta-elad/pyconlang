from inspect import cleandoc
from pathlib import Path

from pyconlang.lexurgy import LexurgyClient
from pyconlang.lexurgy.domain import LexurgyRequest, LexurgyResponse


def test_roundtrip(
    sample_changes: str, simple_changes: Path, lexurgy_client: LexurgyClient
) -> None:
    assert lexurgy_client.roundtrip(LexurgyRequest(["iki"])) == LexurgyResponse(
        ["ishi"], {"phonetic": ["iʃi"]}
    )

    simple_changes.write_text(
        sample_changes.replace(
            "romanizer-phonetic:",
            cleandoc(
                """
        post-alveolars-front:
            ʃ => s
            
        romanizer-phonetic:
    """
            ),
        )
    )

    assert lexurgy_client.roundtrip(LexurgyRequest(["iki"])) == LexurgyResponse(
        ["isi"], {"phonetic": ["isi"]}
    )
