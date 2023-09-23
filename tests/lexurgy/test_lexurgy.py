from inspect import cleandoc
from pathlib import Path

from pyconlang.lexurgy import LexurgyClient
from pyconlang.lexurgy.domain import LexurgyRequest, LexurgyResponse


def test_roundtrip(
    modern_changes: str,
    modern_changes_path: Path,
    lexurgy_client: LexurgyClient,
) -> None:
    assert lexurgy_client.roundtrip(LexurgyRequest(["iki"])) == LexurgyResponse(
        ["iʃi"],
        {
            "archaic-phonetic": ["iki"],
            "archaic": ["iki"],
            "modern-phonetic": ["iʃi"],
            "modern": ["ishi"],
        },
    )

    modern_changes_path.write_text(
        modern_changes.replace(
            "era2:",
            cleandoc(
                """
                post-alveolars-front:
                    ʃ => s
                    
                era2:
                """
            ),
        )
    )

    assert lexurgy_client.roundtrip(LexurgyRequest(["iki"])) == LexurgyResponse(
        ["isi"],
        {
            "archaic-phonetic": ["iki"],
            "archaic": ["iki"],
            "modern-phonetic": ["isi"],
            "modern": ["isi"],
        },
    )
