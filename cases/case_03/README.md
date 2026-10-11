## Notes on Case 03

Case 03 introduces entity aliases as its single new difficulty: the same
person referred to by more than one surface form. Rebecca Tan appears in
the source as "Rebecca Tan", as "Rebecca", and as "Mrs Tan". Everyone else
in the source appears only by full canonical name.

The committed extraction fixture emits both "Rebecca Tan" and "Rebecca" as
endpoints. The exact-name builder therefore constructs two Rebecca entities,
producing one false-positive and one false-negative spouse edge. "Mrs Tan"
appears only in supporting text, not as an extracted endpoint. This deterministic
fixture failure does not imply that a live extractor must emit unresolved aliases:
one recorded live run resolved Rebecca Tan consistently and scored perfectly.
See the [research design](../../docs/design/entity-resolution-research-experiment.md)
for the observation and its limits.

Surname-only references ("Tan") are deliberately excluded. Three other Tans
appear in the source (Jonathan Tan, Michael Tan, and Sophie Tan), so a bare
surname is genuinely ambiguous and would introduce a second difficulty
alongside aliasing.

Case 03 deliberately does not exercise `sibling_of` or `trustee_of`, which
belong to Case 02, nor multiple trusts, which belongs to a later case. The
three-beneficiary recap sentence in the source is not used as approved
evidence, so that multi-edge provenance behaviour remains isolated to
Case 02.
