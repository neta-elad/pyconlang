import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, TypeVar, cast

from dataclasses_json import DataClassJsonMixin, LetterCase, config

from .errors import LexurgyResponseBadType, LexurgyResponseMissingType


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


@dataclass
class LexurgyRequest(CamelCaseJsonMixin):
    words: list[str]
    start_at: str | None = field(default=None)
    stop_before: str | None = field(default=None)
    trace_words: list[str] = field(default_factory=list)
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

_T = TypeVar("_T", covariant=True)


class DictConstructable(Protocol[_T]):
    @classmethod
    def from_dict(cls, a_dict: dict[Any, Any]) -> _T:
        ...


_LEXURGY_RESPONSE: Mapping[str, DictConstructable[AnyLexurgyResponse]] = {
    "changed": LexurgyResponse,
    "error": LexurgyErrorResponse,
}


def from_json(raw_payload: str, mapping: Mapping[str, DictConstructable[_T]]) -> _T:
    payload = json.loads(raw_payload)

    if "type" not in payload:
        raise LexurgyResponseMissingType()

    payload_type = payload["type"]

    if payload_type not in mapping:
        raise LexurgyResponseBadType()

    target_type = mapping[payload_type]

    return target_type.from_dict(payload)


def parse_response(payload: str) -> AnyLexurgyResponse:
    return from_json(payload, _LEXURGY_RESPONSE)
