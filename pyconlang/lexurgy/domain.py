from dataclasses import dataclass, field
from typing import cast

from dataclasses_json import DataClassJsonMixin, LetterCase, config


@dataclass(eq=True, frozen=True)
class TraceLine:
    rule: str
    word: str
    before: str
    after: str

    def set_word(self, new_word: str) -> "TraceLine":
        return TraceLine(self.rule, new_word, self.before, self.after)


class CamelCaseJsonMixin(DataClassJsonMixin):
    dataclass_json_config = cast(
        None, config(letter_case=LetterCase.CAMEL)["dataclasses_json"]
    )


# @dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class LexurgyRequest(CamelCaseJsonMixin):
    words: list[str]
    start_at: str | None = field(default=None)
    stop_before: str | None = field(default=None)
    debug_words: list[str] = field(default_factory=list)
    romanize: bool = field(default=True)


@dataclass
class LexurgyResponse(CamelCaseJsonMixin):
    words: list[str]
    intermediates: dict[str, list[str]] = field(default_factory=dict)
    trace_lines: list[str] = field(default_factory=list)


@dataclass
class LexurgyErrorResponse(CamelCaseJsonMixin):
    message: str
    stack_trace: list[str]


AnyLexurgyResponse = LexurgyResponse | LexurgyErrorResponse
