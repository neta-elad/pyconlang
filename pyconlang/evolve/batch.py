from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple, Union

from ..types import AffixType, ResolvedForm
from .types import Evolved

Cache = Dict["EvolveQuery", Evolved]


@dataclass(eq=True, frozen=True)
class LeafEvolveQuery:
    query: str
    start: Optional[str] = field(default=None, kw_only=True)
    end: Optional[str] = field(default=None, kw_only=True)

    def get_query(self, cache: Cache) -> str:
        return self.query

    def set_end(self, end: Optional[str]) -> "LeafEvolveQuery":
        return LeafEvolveQuery(self.query, start=self.start, end=end)


@dataclass(eq=True, frozen=True)
class NodeEvolveQuery:
    affix_type: AffixType
    stem: "EvolveQuery"
    affix: "EvolveQuery"
    start: Optional[str] = field(default=None, kw_only=True)
    end: Optional[str] = field(default=None, kw_only=True)

    def get_query(self, cache: Cache) -> str:
        assert self.stem.end == self.start
        assert self.affix.end == self.start

        if self.stem.start != self.start:
            assert self.stem in cache
            stem = cache[self.stem].phonetic
        else:
            stem = self.stem.get_query(cache)

        if self.affix.start != self.start:
            assert self.affix in cache
            affix = cache[self.affix].phonetic
        else:
            affix = self.affix.get_query(cache)

        return self.affix_type.fuse(stem, affix)

    def set_end(self, end: Optional[str]) -> "NodeEvolveQuery":
        return NodeEvolveQuery(
            self.affix_type, self.stem, self.affix, start=self.start, end=end
        )

    def is_dependent(self) -> bool:
        return self.start != self.stem.start or self.start != self.affix.start


EvolveQuery = Union[LeafEvolveQuery, NodeEvolveQuery]
DependableQuery = Union[str, EvolveQuery]


@dataclass
class QueryWalker:
    queries: Dict[int, EvolveQuery] = field(default_factory=dict)
    layers: Dict[int, int] = field(default_factory=dict)
    max_layer: int = field(default=0)

    def set_layer(self, query: EvolveQuery, layer: int = 0) -> None:
        self.layers[id(query)] = layer
        self.queries[id(query)] = query

    def get_layer(self, query: DependableQuery) -> int:
        if isinstance(query, str):
            return 0
        return self.layers[id(query)]

    def get_query(self, query_id: int) -> EvolveQuery:
        return self.queries[query_id]

    def walk_query(self, query: EvolveQuery) -> None:
        match query:
            case LeafEvolveQuery():
                self.set_layer(query)
            case NodeEvolveQuery():
                self.walk_query(query.stem)
                self.walk_query(query.affix)

                layer = int(query.is_dependent()) + max(
                    self.get_layer(query.stem), self.get_layer(query.affix)
                )
                self.set_layer(query, layer)
                self.max_layer = max(self.max_layer, layer)

    def walk_queries(self, queries: List[EvolveQuery]) -> List[List[EvolveQuery]]:
        # when do I need a query:
        # when start != end
        # or start == end == None *and* it is in the original list

        ids = {id(query) for query in queries}

        for query in queries:
            self.walk_query(query)

        result: List[List[EvolveQuery]] = []
        for _i in range(1 + self.max_layer):
            result.append([])

        for query_id, layer in self.layers.items():
            query = self.get_query(query_id)
            if query.start != query.end:
                result[layer].append(query)
            elif query.start is None and id(query) in ids:
                result[layer].append(query)

        return result


def order_in_layers(queries: List[EvolveQuery]) -> List[List[EvolveQuery]]:
    return QueryWalker().walk_queries(queries)


# query with end=None only run when it is a root
# end is never set in init, only after


def build_query(form: ResolvedForm) -> EvolveQuery:
    stem = form.stem
    stem_query: EvolveQuery = LeafEvolveQuery(stem.form, start=stem.era_name())
    for affix in form.affixes:
        affix_query = build_query(affix.form)
        affix_era = affix.era_name()
        # affix_query.start = affix.era_name()

        if affix_era is None and stem_query.start is not None:
            raise RuntimeError("Affix time must always be later than stem's time")

        elif affix_era is None and stem_query.start is None:
            stem_query = NodeEvolveQuery(affix.type, stem_query, affix_query)

        elif affix_era is not None and stem_query.start != affix_era:
            # assume affix.era > stem_query.start
            affix_query = affix_query.set_end(affix_era)
            stem_query = stem_query.set_end(affix_era)

            stem_query = NodeEvolveQuery(
                affix.type, stem_query, affix_query, start=affix_era
            )

        else:  # affix start == query_start != None
            affix_query = affix_query.set_end(affix_era)
            stem_query = stem_query.set_end(affix_era)
            stem_query = NodeEvolveQuery(
                affix.type, stem_query, affix_query, start=stem_query.start
            )

    return stem_query


def build_and_order(
    forms: Sequence[ResolvedForm],
) -> Tuple[Mapping[ResolvedForm, EvolveQuery], List[List[EvolveQuery]]]:
    mapping: Dict[ResolvedForm, EvolveQuery] = {}
    queries: List[EvolveQuery] = []
    # todo cache resolved form to query

    for form in forms:
        query = build_query(form)
        mapping[form] = query
        queries.append(query)

    return mapping, order_in_layers(queries)


def segment_by_start_end(
    queries: List[EvolveQuery],
) -> Mapping[Tuple[Optional[str], Optional[str]], List[EvolveQuery]]:
    segments: Dict[Tuple[Optional[str], Optional[str]], List[EvolveQuery]] = {}

    for query in queries:
        start_end = query.start, query.end
        segments.setdefault(start_end, [])
        segments[start_end].append(query)

    return segments
