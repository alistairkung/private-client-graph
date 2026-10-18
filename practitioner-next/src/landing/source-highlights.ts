import type { Evidence } from "../shared/contracts";

/** Split at exact quote boundaries without changing any source character. */
export function sourceHighlights(text: string, evidence: Evidence[]) {
  const ranges: { start: number; end: number; ids: string[] }[] = [];
  const quotes = new Map<string, string[]>();
  for (const item of evidence) {
    if (!item.supporting_text) continue;
    quotes.set(item.supporting_text, [
      ...(quotes.get(item.supporting_text) ?? []),
      item.id,
    ]);
  }
  for (const [quote, ids] of quotes) {
    let start = text.indexOf(quote);
    while (start >= 0) {
      ranges.push({ start, end: start + quote.length, ids });
      start = text.indexOf(quote, start + 1);
    }
  }
  const boundaries = [
    ...new Set([
      0,
      text.length,
      ...ranges.flatMap((range) => [range.start, range.end]),
    ]),
  ].sort((a, b) => a - b);
  return boundaries.slice(0, -1).map((start, index) => ({
    text: text.slice(start, boundaries[index + 1]),
    start,
    ids: [
      ...new Set(
        ranges
          .filter((range) => range.start <= start && range.end > start)
          .flatMap((range) => range.ids),
      ),
    ],
  }));
}
