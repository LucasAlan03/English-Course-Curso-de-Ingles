import { render, screen, userEvent } from '@testing-library/react-native';

import { api, apiText } from '../api';
import { saveText } from '../download';
import CallTimer from '../components/CallTimer';
import ReportScreen from '../app/report/[sessionId]';
import TeachScreen from '../app/teach';

jest.mock('../api', () => ({
  api: jest.fn(), apiText: jest.fn(), audioUrl: (p: string) => p, ApiError: class extends Error {},
}));
jest.mock('../download', () => ({ saveText: jest.fn().mockResolvedValue(undefined) }));
let mockParams: Record<string, string> = {};
jest.mock('expo-router', () => {
  const React = require('react');
  return {
    router: { push: jest.fn(), replace: jest.fn() },
    useLocalSearchParams: () => mockParams,
    useFocusEffect: (cb: () => void) => React.useEffect(cb, []),
  };
});

const apiMock = api as jest.Mock;
const { router } = jest.requireMock('expo-router');

beforeEach(() => {
  apiMock.mockReset();
  (apiText as jest.Mock).mockReset();
  router.replace.mockClear();
});

test('call timer shows elapsed and target minutes', async () => {
  apiMock.mockResolvedValue({ seconds: 400 });
  await render(<CallTimer sessionId="7" />);
  expect(await screen.findByText('6:40 / 10:00')).toBeTruthy();
  expect(apiMock).toHaveBeenCalledWith('/sessions/7/elapsed');
});

const REPORT = {
  report: { mistakes: [], natural_expressions: [], strengths: ['Clear'], score: 80 },
  conversation_score: 80, final_score: 80, next_due: null,
};

test('report download saves the markdown file', async () => {
  mockParams = { sessionId: '9' };
  apiMock.mockResolvedValue(REPORT);
  (apiText as jest.Mock).mockResolvedValue('# Relatório');
  await render(<ReportScreen />);
  await userEvent.press(await screen.findByText('Baixar relatório'));
  expect(apiText).toHaveBeenCalledWith('/sessions/9/report.md');
  expect(saveText).toHaveBeenCalledWith('relatorio-9.md', '# Relatório', 'text/markdown');
});

test('teach screen starts a teach session for the current module', async () => {
  mockParams = {};
  apiMock.mockImplementation(async (path: string) => {
    if (path === '/home') return { next_module: { id: 'b1_past_simple', title: 'Past simple', level: 'B1' } };
    if (path === '/sessions') return { id: 21 };
    throw new Error(path);
  });
  await render(<TeachScreen />);
  await userEvent.press(await screen.findByText('Começar a aula'));
  expect(apiMock).toHaveBeenCalledWith('/sessions', expect.objectContaining({
    method: 'POST', json: { kind: 'teach', module_id: 'b1_past_simple' },
  }));
  expect(router.replace).toHaveBeenCalledWith('/chat/21');
});

test('call 1 starts the module scenario conversation', async () => {
  mockParams = { kind: 'lesson', module: 'b1_verb_to' };
  apiMock.mockImplementation(async (path: string) => {
    if (path === '/modules/b1_verb_to') return { id: 'b1_verb_to', title: 'Verbo + to', scenario: { title: 'Planning', character: 'A friend', goal: 'g' } };
    if (path === '/sessions') return { id: 30 };
    throw new Error(path);
  });
  await render(<TeachScreen />);
  await userEvent.press(await screen.findByText('Começar a ligação'));
  expect(apiMock).toHaveBeenCalledWith('/sessions', expect.objectContaining({
    json: { kind: 'lesson', module_id: 'b1_verb_to' },
  }));
});
