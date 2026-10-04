# Treat extracted PDF text as the Authoritative Source

Matter Intake accepts a text-layer PDF as an acquisition format, deterministically extracts and minimally normalizes its text, and treats the resulting finalized text value as the Matter's Authoritative Source. The uploaded PDF is not part of Matter state and is discarded after the intake request whether processing succeeds or fails; the finalized text is sent unchanged to semantic extraction, persisted after successful analysis, displayed for professional review, and used for exact Evidence matching.

## Consequences

The review workspace proves Evidence against the persisted extracted text rather than visual coordinates in the original PDF and does not claim to reproduce the PDF. Private Client Graph does not retain a second source representation or become a document store. Future retrieval chunks, embeddings, or vector indexes, if earned, are rebuildable derived state created from persisted Authoritative Source text and never replace exact Evidence provenance.
