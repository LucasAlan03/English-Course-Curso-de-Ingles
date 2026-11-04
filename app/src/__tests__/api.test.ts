import { api, ApiError, audioUrl } from '../api';
import { API_TOKEN, BASE_URL } from '../config';

function mockFetch(status: number, body: unknown) {
  const fn = jest.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    statusText: 'status text',
    json: async () => body,
  });
  (global as any).fetch = fn;
  return fn;
}

afterEach(() => {
  jest.restoreAllMocks();
});

test('sends the token header and returns parsed json', async () => {
  const fetchMock = mockFetch(200, { status: 'ok' });
  const result = await api<{ status: string }>('/health');
  expect(result).toEqual({ status: 'ok' });
  const [url, init] = fetchMock.mock.calls[0];
  expect(url).toBe(`${BASE_URL}/health`);
  expect(init.headers['X-API-Token']).toBe(API_TOKEN);
});

test('json option sets content type and stringifies the body', async () => {
  const fetchMock = mockFetch(200, { id: 1 });
  await api('/sessions', { method: 'POST', json: { kind: 'free' } });
  const init = fetchMock.mock.calls[0][1];
  expect(init.method).toBe('POST');
  expect(init.headers['Content-Type']).toBe('application/json');
  expect(init.body).toBe(JSON.stringify({ kind: 'free' }));
});

test('FormData bodies are sent without a content type', async () => {
  const fetchMock = mockFetch(200, { text: 'hi' });
  const form = new FormData();
  form.append('text', 'hello');
  await api('/sessions/1/turn', { method: 'POST', body: form });
  const init = fetchMock.mock.calls[0][1];
  expect(init.headers['Content-Type']).toBeUndefined();
  expect(init.body).toBe(form);
});

test('throws ApiError with code, detail, status and provider', async () => {
  mockFetch(402, { error: 'provider_out_of_credit', detail: 'Os créditos acabaram.', provider: 'openai' });
  await expect(api('/x')).rejects.toMatchObject({
    name: 'ApiError',
    code: 'provider_out_of_credit',
    detail: 'Os créditos acabaram.',
    status: 402,
    provider: 'openai',
  });
});

test('a failure without a json body still becomes an ApiError', async () => {
  (global as any).fetch = jest.fn().mockResolvedValue({
    ok: false,
    status: 500,
    statusText: 'Internal Server Error',
    json: async () => {
      throw new Error('not json');
    },
  });
  await expect(api('/x')).rejects.toMatchObject({ code: 'http_error', status: 500 });
});

test('network failure becomes network_error', async () => {
  (global as any).fetch = jest.fn().mockRejectedValue(new TypeError('Network request failed'));
  const error = (await api('/x').catch((e: unknown) => e)) as ApiError;
  expect(error).toBeInstanceOf(ApiError);
  expect(error.code).toBe('network_error');
});

test('audioUrl carries the token in the query string', () => {
  expect(audioUrl('/audio/a.wav')).toBe(`${BASE_URL}/audio/a.wav?token=${encodeURIComponent(API_TOKEN)}`);
});
