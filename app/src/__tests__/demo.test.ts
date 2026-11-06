import { demoRequest, normalize } from '@/demo';

const demoData = {
  date: '2026-11-06',
  responses: {
    '/home': { status: 200, body: { hello: 'world' } },
    '/media': { status: 200, body: [{ id: 1 }] },
    '/modules/b2_x/exercises': { status: 403, body: { error: 'module_locked', detail: 'Bloqueado.' } },
  },
  answers: { 'b1_a/e01': { answers: ["I won't go"], explanation: 'Porque sim.' } },
};

beforeEach(() => {
  global.fetch = jest.fn(async () => ({ json: async () => demoData })) as unknown as typeof fetch;
});

test('normalize follows the backend rules', () => {
  expect(normalize('  I WON’T go! ')).toBe('i will not go');
  expect(normalize('She doesn\'t, "really".')).toBe('she does not really');
  expect(normalize("They're here")).toBe('they are here');
});

test('GET returns the recorded body, falling back to the path without query', async () => {
  await expect(demoRequest('/home', 'GET', undefined)).resolves.toEqual({ hello: 'world' });
  await expect(demoRequest('/media?date=2026-01-01', 'GET', undefined)).resolves.toEqual([{ id: 1 }]);
});

test('recorded errors become ApiError', async () => {
  await expect(demoRequest('/modules/b2_x/exercises', 'GET', undefined)).rejects.toMatchObject({
    code: 'module_locked', status: 403,
  });
});

test('lesson answers are graded in the browser', async () => {
  const right = await demoRequest<{ correct: boolean }>('/exercises/b1_a/e01/answer', 'POST', { answer: 'i will not go.' });
  expect(right.correct).toBe(true);
  const wrong = await demoRequest<{ correct: boolean; correct_answer: string }>(
    '/exercises/b1_a/e01/answer', 'POST', { answer: 'I go' });
  expect(wrong).toMatchObject({ correct: false, correct_answer: "I won't go" });
});

test('other writes are refused with the demo notice', async () => {
  await expect(demoRequest('/media', 'POST', {})).rejects.toMatchObject({ code: 'demo_mode' });
});
