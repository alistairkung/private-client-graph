export type JsonRequestErrorKind = "http" | "network" | "invalid-json";

export class JsonRequestError extends Error {
  constructor(
    public readonly kind: JsonRequestErrorKind,
    public readonly status?: number,
    public readonly body?: unknown,
  ) {
    super(`JSON request failed: ${kind}`);
  }
}

export async function requestJson<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, options);
  } catch {
    throw new JsonRequestError("network");
  }
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw new JsonRequestError("invalid-json", response.status);
  }
  if (!response.ok) {
    throw new JsonRequestError("http", response.status, body);
  }
  return body as T;
}
