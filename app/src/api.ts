import { API_TOKEN, BASE_URL } from './config';
import { DEMO, DEMO_NOTICE, demoAudioUrl, demoRequest } from './demo';

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
  if (DEMO) return demoRequest<T>(path, (rest.method ?? 'GET').toUpperCase(), json);
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

/** Same as api() but returns the body as text (for downloads such as the Markdown report or CSV). */
export async function apiText(path: string): Promise<string> {
  if (DEMO) throw new ApiError('demo_mode', DEMO_NOTICE);
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, { headers: { 'X-API-Token': API_TOKEN } });
  } catch {
    throw new ApiError('network_error', 'Não consegui falar com o servidor. Ele está rodando e na mesma rede?');
  }
  if (!response.ok) {
    let data: { error?: string; detail?: string } = {};
    try {
      data = await response.json();
    } catch {
      // not json
    }
    throw new ApiError(data.error ?? 'http_error', data.detail ?? response.statusText, response.status);
  }
  return response.text();
}

/** Audio elements and players cannot send headers, so the token travels in the query string. */
export function audioUrl(path: string): string {
  if (DEMO) return demoAudioUrl(path);
  return `${BASE_URL}${path}?token=${encodeURIComponent(API_TOKEN)}`;
}
