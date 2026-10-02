from typing import Literal


EntityType = Literal["person", "trust"]

RelationshipType = Literal[
    "parent_of",
    "sibling_of",
    "spouse_of",
    "settlor_of",
    "trustee_of",
    "beneficiary_of",
]
