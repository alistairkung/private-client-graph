import type { CanonicalState } from "../shared/contracts";
export type LandingPoint = readonly [number, number];

/** Presentation coordinates keyed by the returned IDs, never fixture ID spellings. */
export function landingPositions(
  state: CanonicalState,
): Map<string, LandingPoint> {
  const positions = new Map<string, LandingPoint>(
    state.entities.map((entity, index) => [
      entity.id,
      [110 + (index % 3) * 210, 65 + Math.floor(index / 3) * 145],
    ]),
  );
  const trusts = state.entities.filter((entity) => entity.type === "trust");
  if (trusts.length !== 1 || state.entities.length > 5) return positions;
  const trust = trusts[0];
  const settlor = state.relationships.find(
    (edge) => edge.type === "settlor_of" && edge.target === trust.id,
  )?.source;
  if (!settlor) return positions;
  const spouseEdge = state.relationships.find(
    (edge) =>
      edge.type === "spouse_of" && [edge.source, edge.target].includes(settlor),
  );
  const spouse =
    spouseEdge &&
    (spouseEdge.source === settlor ? spouseEdge.target : spouseEdge.source);
  const beneficiaries = state.relationships
    .filter(
      (edge) => edge.type === "beneficiary_of" && edge.target === trust.id,
    )
    .map((edge) => edge.source);
  const placed = new Set<string>();
  const place = (id: string | undefined, point: LandingPoint) => {
    if (id && positions.has(id) && !placed.has(id)) {
      positions.set(id, point);
      placed.add(id);
    }
  };
  place(trust.id, [370, 210]);
  place(settlor, [370, 58]);
  place(spouse, [130, 58]);
  const remaining = [
    ...new Set([
      ...beneficiaries,
      ...state.entities.map((entity) => entity.id),
    ]),
  ].filter((id) => !placed.has(id));
  const slots: LandingPoint[] = [
    [155, 350],
    [545, 350],
    [95, 210],
  ];
  remaining.forEach((id, index) =>
    place(id, slots[index] ?? [95 + index * 150, 350]),
  );
  return positions;
}

export function sourceContext(text: string, start: number, length: number) {
  let before = Math.max(0, start - 105);
  let after = Math.min(text.length, start + length + 105);
  if (before > 0) {
    const boundary = text.indexOf(" ", before);
    if (boundary >= 0 && boundary < start) before = boundary + 1;
  }
  if (after < text.length) {
    const boundary = text.lastIndexOf(" ", after);
    if (boundary > start + length) after = boundary;
  }
  return {
    before: (before > 0 ? "… " : "") + text.slice(before, start),
    after:
      text.slice(start + length, after) + (after < text.length ? " …" : ""),
  };
}

/** Match backend entity names verbatim without interpreting the source. */
export function sourceEntitySpans(text: string, names: string[]) {
  const exactNames = [...new Set(names.filter(Boolean))].sort(
    (a, b) => b.length - a.length,
  );
  if (!exactNames.length) return [{ text, entity: false }];
  const pattern = new RegExp(
    `(${exactNames.map((name) => name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`,
    "g",
  );
  return text
    .split(pattern)
    .filter(Boolean)
    .map((part) => ({ text: part, entity: exactNames.includes(part) }));
}

/** Curated source excerpts are verbatim canonical Evidence, in source order. */
export function canonicalSourceExcerpts(
  state: CanonicalState,
  sourceId: string,
) {
  const source = state.sources.find((item) => item.id === sourceId);
  if (!source) return [];
  return [
    ...new Set(
      state.evidence
        .filter((item) => item.source_id === sourceId)
        .map((item) => item.supporting_text),
    ),
  ]
    .filter((text) => text.length > 0 && source.text.includes(text))
    .sort(
      (left, right) => source.text.indexOf(left) - source.text.indexOf(right),
    );
}
