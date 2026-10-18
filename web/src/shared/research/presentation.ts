export type ResearchText = (key: string, values?: Record<string, string | number>) => string;

export const researchText: ResearchText = (key, values = {}) =>
  key.replace(/\{(\w+)\}/g, (token, name: string) => String(values[name] ?? token));
