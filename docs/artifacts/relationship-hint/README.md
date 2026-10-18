# Relationship invitation review evidence

Captured from the production build and real local curated Case 01 API using the
existing deterministic test boundaries. All displayed material is synthetic.

- [Desktop: contextual hint beside the unselected settlor button](desktop.png)
- [701px: wrapped hint stays clear of the Evidence pane](intermediate.png)
- [320px Chinese with reduced motion: hint clears Alice’s caption](phone-320-chinese-reduced.png)

The browser matrix checks 320, 390, 700, 701, 900 and 1512px in English and Chinese,
with ordinary and reduced motion. It verifies hint clearance, preserved initial
selection, exact Source text, input pass-through and touch/keyboard dismissal.
Existing tests retain 44px targets, free outer scrolling, exact Evidence selection,
reverse-scroll dismissal and the explicit reduced-motion heading opacity.

Local validation: 739 Python tests and 170 frontend tests passed; TypeScript and
production build passed. All 88 functional browser tests passed across the full
suite and affected-suite reruns; 10 existing optional/viewport skips remain.
The final landing rerun passed all 24 checks with six existing viewport skips.
An isolated runner used port 4175 because 4173 was occupied. Test-only origin
headers were aligned for the affected API tests and restored unchanged afterward.

Final diff review isolated hint geometry assertions in a named browser helper;
no material readability concerns remain. The design detector reported no findings.
Paid provider usage remains **0/5**.

See the [landing design record](../../design/landing-document-story.md).
