from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from ..domain import Component, Compound, Joiner, JoinerStress, ResolvedForm
from ..unicode import combine, remove_primary_stress
from .arrange import AffixArranger
from .domain import Evolved
from .errors import BadAffixation


class QueryCache(Protocol):
    def __getitem__(self, query: "Query") -> Evolved:
        ...

    def __contains__(self, item: "Query") -> bool:
        ...


@dataclass(eq=True, frozen=True)
class ComponentQuery:
    query: str
    start: str | None = field(default=None, kw_only=True)
    end: str | None = field(default=None, kw_only=True)

    def get_query(self, cache: QueryCache) -> str:
        return self.query

    def set_end(self, end: str | None) -> "ComponentQuery":
        return ComponentQuery(self.query, start=self.start, end=end)


@dataclass(eq=True, frozen=True)
class CompoundQuery:
    head: "Query"
    joiner: Joiner
    tail: "Query"
    end: str | None = field(default=None, kw_only=True)

    @property
    def start(self) -> str | None:
        return self.joiner.era_name()

    def get_query(self, cache: QueryCache) -> str:
        assert self.head.end == self.start
        assert self.tail.end == self.start

        if self.head.start != self.start:
            assert self.head in cache
            head = cache[self.head].phonetic
        else:
            head = self.head.get_query(cache)

        if self.tail.start != self.start:
            assert self.tail in cache
            tail = cache[self.tail].phonetic
        else:
            tail = self.tail.get_query(cache)

        if self.joiner.stress is JoinerStress.HEAD:
            tail = remove_primary_stress(tail)
        else:
            head = remove_primary_stress(head)

        return combine(head, tail)

    def set_end(self, end: str | None) -> "CompoundQuery":
        return CompoundQuery(
            self.head,
            self.joiner,
            self.tail,
            end=end,
        )

    def is_dependent(self) -> bool:
        """non-immediate query"""
        return self.start != self.head.start or self.start != self.tail.start


Query = ComponentQuery | CompoundQuery
DependableQuery = str | Query


@dataclass
class QueryWalker:
    queries: dict[int, Query] = field(default_factory=dict)
    layers: dict[int, int] = field(default_factory=dict)
    max_layer: int = field(default=0)

    def set_layer(self, query: Query, layer: int = 0) -> None:
        self.layers[id(query)] = layer
        self.queries[id(query)] = query

    def get_layer(self, query: DependableQuery) -> int:
        if isinstance(query, str):
            return 0
        return self.layers[id(query)]

    def get_query(self, query_id: int) -> Query:
        return self.queries[query_id]

    def walk_query(self, query: Query) -> None:
        match query:
            case ComponentQuery():
                self.set_layer(query)
            case CompoundQuery():
                self.walk_query(query.head)
                self.walk_query(query.tail)

                layer = int(query.is_dependent()) + max(
                    self.get_layer(query.head), self.get_layer(query.tail)
                )
                self.set_layer(query, layer)
                self.max_layer = max(self.max_layer, layer)

    def walk_queries(self, queries: list[Query]) -> list[list[Query]]:
        # when do I need a query:
        # when start != end
        # or start == end == None *and* it is in the original list

        ids = {id(query) for query in queries}

        for query in queries:
            self.walk_query(query)

        result: list[list[Query]] = []
        for _i in range(1 + self.max_layer):
            result.append([])

        for query_id, layer in self.layers.items():
            query = self.get_query(query_id)
            if query.start != query.end:
                result[layer].append(query)
            elif query.start is None and id(query) in ids:
                result[layer].append(query)

        return result


BatcherCache = dict[ResolvedForm, Query]


def order_in_layers(queries: list[Query]) -> list[list[Query]]:
    return QueryWalker().walk_queries(queries)


def segment_by_start_end(
    queries: list[Query],
) -> Mapping[tuple[str | None, str | None], list[Query]]:
    segments: dict[tuple[str | None, str | None], list[Query]] = {}

    for query in queries:
        start_end = query.start, query.end
        segments.setdefault(start_end, [])
        segments[start_end].append(query)

    return segments


@dataclass
class Builder:
    cache: BatcherCache
    arranger: AffixArranger

    def build_query_uncached(self, form: ResolvedForm) -> Query:
        match form:
            case Component():
                return ComponentQuery(form.form.form, start=form.form.era_name())
            case Compound():
                joiner = form.joiner
                head = self.build_query(form.head).set_end(joiner.era_name())
                tail = self.build_query(form.tail).set_end(joiner.era_name())

                if self.arranger.is_before(
                    joiner.era_name(), head.start
                ) or self.arranger.is_before(joiner.era_name(), tail.start):
                    raise BadAffixation(
                        "Affix time must always be later than stem's time"
                    )

                return CompoundQuery(head, form.joiner, tail)

    def build_query(self, form: ResolvedForm) -> Query:
        if form in self.cache:
            return self.cache[form]

        query = self.build_query_uncached(form)

        self.cache[form] = query
        return query

    def build_and_order(
        self,
        forms: Sequence[ResolvedForm],
    ) -> tuple[Mapping[ResolvedForm, Query], list[list[Query]]]:
        mapping: dict[ResolvedForm, Query] = {}
        queries: list[Query] = []

        for form in forms:
            query = self.build_query(form)
            mapping[form] = query
            queries.append(query)

        return mapping, order_in_layers(queries)


@dataclass
class Batcher:
    cache: BatcherCache = field(default_factory=dict)

    def builder(self, arranger: AffixArranger) -> Builder:
        return Builder(self.cache, arranger)
