## Notes on Case 03

Case 03 introduces entity aliases as its single new difficulty: the same
person referred to by more than one surface form. Rebecca Tan appears in
the source as "Rebecca Tan", as "Rebecca", and as "Mrs Tan". Everyone else
in the source appears only by full canonical name.

The case is designed to expose the absence of alias resolution in the
current deterministic builder, which groups mentions only when the emitted
string is identical. A correct extraction will therefore contain multiple
distinct name strings for one person, and the builder is expected to split
Rebecca into three separate entities — "Rebecca Tan", "Rebecca", and
"Mrs Tan" — with edges touching her appearing as both false positives and
false negatives. That failure is the point of the case.

Surname-only references ("Tan") are deliberately excluded. Two other Tans
appear in the source (Jonathan Tan, Michael Tan, and Sophie Tan), so a bare
surname is genuinely ambiguous and would introduce a second difficulty
alongside aliasing.

Case 03 deliberately does not exercise `sibling_of` or `trustee_of`, which
belong to Case 02, nor multiple trusts, which belongs to a later case. The
three-beneficiary recap sentence in the source is not used as approved
evidence, so that multi-edge provenance behaviour remains isolated to
Case 02.