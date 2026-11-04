import { API_TOKEN, BASE_URL } from './config';

export class ApiError extends Error {
  code: string;
  detail: string;
  status: number;
  provider?: string;

  constructor(code: string, detail: string, status = 0, provider?: string) {
    super(detail || code);
    this.name = 'ApiError';
    this.code = code;
    this.detail = detail;
    this.status = status;
    this.provider = provider;
  }
}

type ApiInit = Omit<RequestInit, 'body'> & { json?: unknown; body?: BodyInit | null };

export async function api<T>(path: string, init: ApiInit = {}): Promise<T> {
  const { json, headers, body, ...rest } = init;
  const finalHeaders: Record<string, string> = { 'X-API-Token': API_TOKEN, ...(headers as Record<string, string>) };
  let finalBody = body;
  if (json !== undefined) {
    finalHeaders['Content-Type'] = 'application/json';
    finalBody = JSON.stringify(json);
  }

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, { ...rest, headers: finalHeaders, body: finalBody });
  } catch {
    throw new ApiError('network_error', 'Não consegui falar com o servidor. Ele está rodando e na mesma rede?');
  }

  if (!response.ok) {
    let data: { error?: string; detail?: string; provider?: string } = {};
    try {
      data = await response.json();
    } catch {
      // the body was not json; fall back to the status text
    }
    throw new ApiError(data.error ?? 'http_error', data.detail ?? response.statusText, response.status, data.provider);
  }
  return (await response.json()) as T;
}

/** Audio elements and players cannot send headers, so the token travels in the query string. */
export function audioUrl(path: string): string {
  return `${BASE_URL}${path}?token=${encodeURIComponent(API_TOKEN)}`;
}
