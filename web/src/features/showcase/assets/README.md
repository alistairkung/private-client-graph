# Evergreen sample capture

`evergreen-sample.png` is a 2× browser capture of the actual shared `GraphView`,
after explicitly loading sample analysis at `/` on base commit `7783e3a`.
The sample request used the backend-owned Case 01 extraction fixture and real
deterministic graph construction. No relationships, labels, or geometry were
drawn separately. Only browser zoom controls and renderer attribution were hidden
for the capture; the graph was unselected.

To refresh: build and run the application, open `/` at a 1600×1100 viewport with
device scale factor 2, explicitly load sample analysis, wait for graph fitting
and fonts, then capture the `Relationship graph` element. Keep the complete
graph and its current connector conventions. This is a static sample image,
never a live result or an interactive control.
