"""Aggregate a ten-reader exploratory panel without invoking Benchmark v3 scoring."""

from collections import Counter
from collections.abc import Mapping
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from private_client_graph.evaluation import _edge
from private_client_graph.graph import ENDPOINT_TYPES
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.models.source import Source
from private_client_graph.models.types import RelationshipType
from private_client_graph.research.retained_inputs import value_digest


Position = Literal['support', 'reject', 'uncertain']
Text = Annotated[str, Field(min_length=1)]
PANEL = tuple(f'r{index:02}' for index in range(1, 11))
MAJORITY = 6


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Citation(Contract):
    source_id: Text
    quote: Text


class Route(Contract):
    complete: bool
    members: list[Citation] = Field(min_length=1)


class Opinion(Contract):
    source: Text
    predicate: RelationshipType
    target: Text
    position: Position
    confidence: Literal['high', 'medium', 'low']
    timing: Text
    reason: Text
    routes: list[Route]

    @property
    def edge(self) -> SemanticEdge:
        return _edge(self.source, self.predicate, self.target)

    @model_validator(mode='after')
    def verify_names(self) -> 'Opinion':
        if (self.source != self.source.strip() or self.target != self.target.strip()
                or self.source == self.target):
            raise ValueError('Use distinct nonempty exact endpoint names.')
        return self


class Review(Contract):
    relationships: list[Opinion]
    unresolved: list[Text]
    contradictions: list[Text]

    @model_validator(mode='after')
    def verify_one_position(self) -> 'Review':
        edges = [item.edge for item in self.relationships]
        if len(edges) != len(set(edges)):
            raise ValueError('A reviewer may give only one position on each canonical proposition.')
        return self


class SubmittedRoute(Contract):
    route_id: str
    members: list[Citation]
    reviewers: list[str]
    claimed_complete_by: list[str]


class Agreement(Contract):
    source: str
    predicate: RelationshipType
    target: str
    endpoint_types: tuple[Literal['person', 'trust'], Literal['person', 'trust']]
    counts: dict[str, int]
    votes: dict[str, Opinion | None]
    eligible_routes: list[SubmittedRoute]
    citation_issues: list[str]
    entity_type_conflicts: list[str]

    @property
    def edge(self) -> SemanticEdge:
        return self.source, self.predicate, self.target


class Ruling(Contract):
    source: Text
    predicate: RelationshipType
    target: Text
    decision: Literal['supported', 'unresolved']
    accepted_route_ids: list[Text]
    reason: Text

    @property
    def edge(self) -> SemanticEdge:
        return _edge(self.source, self.predicate, self.target)


class EvidenceReview(Contract):
    rulings: list[Ruling]
    limitations: list[Text]


def aggregate(reviews: Mapping[str, Review], sources: list[Source]) -> list[Agreement]:
    if set(reviews) != set(PANEL):
        raise ValueError('Exactly ten identified reviewers are required.')
    texts = {source.id: source.text for source in sources}
    if len(sources) != 65 or len(texts) != 65:
        raise ValueError('Exactly 65 unique Sources are required.')
    by_edge: dict[SemanticEdge, dict[str, Opinion]] = {}
    for reviewer in PANEL:
        for opinion in reviews[reviewer].relationships:
            by_edge.setdefault(opinion.edge, {})[reviewer] = opinion
    majority_types: dict[str, set[str]] = {}
    for edge, opinions in by_edge.items():
        if sum(opinion.position == 'support' for opinion in opinions.values()) >= MAJORITY:
            for name, entity_type in zip((edge[0], edge[2]), ENDPOINT_TYPES[edge[1]], strict=True):
                majority_types.setdefault(name, set()).add(entity_type)

    matrix = []
    for edge, opinions in sorted(by_edge.items()):
        counts: Counter[str] = Counter(opinion.position for opinion in opinions.values())
        routes, issues = _check_routes(opinions, texts)
        matrix.append(Agreement(
            source=edge[0], predicate=edge[1], target=edge[2], endpoint_types=ENDPOINT_TYPES[edge[1]],
            counts={**{key: counts[key] for key in ('support', 'reject', 'uncertain')},
                    'omitted': len(PANEL) - len(opinions)},
            votes={reviewer: opinions.get(reviewer) for reviewer in PANEL},
            eligible_routes=routes, citation_issues=issues,
            entity_type_conflicts=[name for name in (edge[0], edge[2])
                                   if len(majority_types.get(name, set())) > 1],
        ))
    return matrix


def _check_routes(
    opinions: Mapping[str, Opinion], texts: Mapping[str, str],
) -> tuple[list[SubmittedRoute], list[str]]:
    eligible: dict[str, SubmittedRoute] = {}
    issues = []
    for reviewer, opinion in opinions.items():
        for index, route in enumerate(opinion.routes, 1):
            invalid = [
                member.source_id for member in route.members
                if not member.quote.strip() or member.quote not in texts.get(member.source_id, '')
            ]
            if invalid:
                issues.append(f'{reviewer} route {index}: missing exact body quotation in {", ".join(invalid)}')
            if invalid or opinion.position != 'support':
                continue
            # Preserve whole alternatives. Never union incomplete routes across readers.
            key = sorted({(member.source_id, member.quote) for member in route.members})
            identity = value_digest(key)
            if identity not in eligible:
                eligible[identity] = SubmittedRoute(
                    route_id=identity, members=[Citation(source_id=src, quote=quote) for src, quote in key],
                    reviewers=[], claimed_complete_by=[],
                )
            entry = eligible[identity]
            if reviewer not in entry.reviewers:
                entry.reviewers.append(reviewer)
            if route.complete and reviewer not in entry.claimed_complete_by:
                entry.claimed_complete_by.append(reviewer)
    return list(eligible.values()), issues


def verify_evidence_rulings(matrix: list[Agreement], review: EvidenceReview) -> list[SemanticEdge]:
    majority = {item.edge: item for item in matrix if item.counts['support'] >= MAJORITY}
    rulings = {row.edge: row for row in review.rulings}
    if rulings.keys() != majority.keys() or len(rulings) != len(review.rulings):
        raise ValueError('The evidence review must rule exactly once on every majority proposition.')
    adjudicated = []
    for edge, ruling in rulings.items():
        agreement = majority[edge]
        permitted = {route.route_id for route in agreement.eligible_routes if route.claimed_complete_by}
        selected = set(ruling.accepted_route_ids)
        if len(selected) != len(ruling.accepted_route_ids) or not selected <= permitted:
            raise ValueError('A ruling may only accept an intact verified route submitted as complete.')
        if ruling.decision == 'supported':
            if not selected or agreement.entity_type_conflicts:
                raise ValueError('A supported ruling requires an intact route and consistent entity types.')
            adjudicated.append(edge)
        elif selected:
            raise ValueError('An unresolved ruling cannot approve supporting routes.')
    return sorted(adjudicated)
