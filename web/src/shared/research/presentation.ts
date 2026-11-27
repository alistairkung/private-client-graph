export type ResearchText = (key: string, values?: Record<string, string | number>) => string;

export const researchText: ResearchText = (key, values = {}) =>
  key.replace(/\{(\w+)\}/g, (token, name: string) => String(values[name] ?? token));

export function percentMetric(value: number | null) {
  return value === null ? "Unavailable" : `${(value * 100).toFixed(2)}%`;
}
