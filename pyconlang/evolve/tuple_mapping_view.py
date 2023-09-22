from dataclasses import dataclass
from typing import Generic, Iterator, MutableMapping, TypeVar

_K1 = TypeVar("_K1")
_K2 = TypeVar("_K2")
_V = TypeVar("_V")


@dataclass
class TupleMappingView(Generic[_K1, _K2, _V], MutableMapping[_K2, _V]):
    underlying_mapping: MutableMapping[tuple[_K1, _K2], _V]
    first: _K1

    def __getitem__(self, item: _K2) -> _V:
        return self.underlying_mapping[(self.first, item)]

    def __setitem__(self, key: _K2, value: _V) -> None:
        self.underlying_mapping[(self.first, key)] = value

    def __delitem__(self, key: _K2) -> None:
        del self.underlying_mapping[(self.first, key)]

    def __len__(self) -> int:
        return len({key for key in self.underlying_mapping if key[0] == self.first})

    def __iter__(self) -> Iterator[_K2]:
        return iter(key[1] for key in self.underlying_mapping if key[0] == self.first)

    def __contains__(self, item: object) -> bool:
        return (self.first, item) in self.underlying_mapping
