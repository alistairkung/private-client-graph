"""Deterministic baseline for outstanding-document leads in original correspondence."""
import re
from dataclasses import dataclass

# Require an actor, a forward-looking action, and a document. Merely naming someone scores zero.
_PROMISE = re.compile(
    r"\b(?P<name>[A-Z][a-zA-Z’'-]+(?: [A-Z][a-zA-Z’'-]+){1,2}) "
    r"(?i:will|agreed to) (?i:circulate|send|forward|provide) "
    r"(?i:(?:the |a |an )?(?:executed |signed |outstanding )?"
    r"(?P<document>appointment|notice|deed|instrument|letter|resolution))\b"
)


@dataclass(frozen=True)
class Suggestion:
    query: str
    origin: str
    passage: str
    rationale: str


def ranked_suggestions(original_text: dict[str, str]) -> tuple[Suggestion, ...]:
    ranked: list[tuple[int, Suggestion]] = []
    for origin, text in original_text.items():
        for sentence in re.finditer(r"[^.!?\n]+[.!?]?", text):
            passage = sentence[0].strip()
            for match in _PROMISE.finditer(passage):
                name, document = match["name"], match["document"].lower()
                rank = 0 if document == "appointment" else 1
                reason = f"{name} is expected to supply the {document}. Their name may locate that document."
                ranked.append((rank, Suggestion(name, origin, passage, reason)))
    unique: dict[str, Suggestion] = {}
    for _, lead in sorted(ranked, key=lambda pair: (pair[0], pair[1].query, pair[1].origin)):
        unique.setdefault(lead.query.casefold(), lead)
    return tuple(unique.values())[:3]
