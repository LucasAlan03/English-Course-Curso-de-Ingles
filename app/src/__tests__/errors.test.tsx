import { render, screen } from '@testing-library/react-native';

import ErrorNotice from '../components/ErrorNotice';
import UsageBanner from '../components/UsageBanner';
import { describeError } from '../errors';

jest.mock('expo-router', () => ({ router: { push: jest.fn() } }));

const err = (code: string, detail = '', provider?: string) => ({ code, detail, provider });

test.each([
  ['provider_out_of_credit', 'openai', 'Os créditos de openai acabaram'],
  ['provider_rate_limited', 'gemini', 'gemini atingiu o limite de requisições'],
  ['monthly_cap_reached', undefined, 'teto mensal de gastos'],
  ['invalid_ai_output', undefined, 'A IA devolveu uma resposta inválida'],
  ['empty_transcript', undefined, 'Não consegui ouvir nada'],
  ['provider_unavailable', 'gemini', 'gemini está fora do ar'],
  ['provider_auth_failed', 'anthropic', 'chave de API de anthropic'],
  ['internal_error', undefined, 'Erro inesperado'],
  ['finish_in_progress', undefined, 'já está sendo gerado'],
])('describeError explains %s', (code, provider, expected) => {
  expect(describeError(err(code, 'server text', provider as string | undefined))).toContain(expected);
});

test('describeError falls back to the server detail, then to the raw error', () => {
  expect(describeError(err('some_other_code', 'Detalhe do servidor.'))).toBe('Detalhe do servidor.');
  expect(describeError(new Error('boom'))).toBe('Error: boom');
  expect(describeError(err('network_error', 'Não consegui falar com o servidor.'))).toBe('Não consegui falar com o servidor.');
});

test('ErrorNotice shows the friendly message', async () => {
  await render(<ErrorNotice error={err('provider_out_of_credit', '', 'openai')} />);
  expect(screen.getByText(/Os créditos de openai acabaram/)).toBeTruthy();
});

test('ErrorNotice renders nothing without an error', async () => {
  await render(<ErrorNotice error={null} />);
  expect(screen.queryByTestId('error-notice')).toBeNull();
});

test('UsageBanner is hidden when spending is fine', async () => {
  await render(<UsageBanner usage={{ total: 10, warn: 45, cap: 50, level: 'ok' }} />);
  expect(screen.queryByTestId('usage-banner')).toBeNull();
});

test('UsageBanner warns near the cap and blocks at the cap', async () => {
  await render(<UsageBanner usage={{ total: 46.2, warn: 45, cap: 50, level: 'warn' }} />);
  expect(screen.getByText('Gasto no mês: R$ 46,20 de R$ 50,00')).toBeTruthy();
});

test('UsageBanner says when the cap was reached', async () => {
  await render(<UsageBanner usage={{ total: 50, warn: 45, cap: 50, level: 'blocked' }} />);
  expect(screen.getByText(/Teto mensal atingido/)).toBeTruthy();
});
