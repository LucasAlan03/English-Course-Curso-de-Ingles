import { render, screen, userEvent } from '@testing-library/react-native';

import { api } from '../api';
import ReviewScreen from '../app/review/[id]';

jest.mock('../api', () => ({ api: jest.fn(), audioUrl: (p: string) => p, ApiError: class extends Error {} }));
jest.mock('../audio', () => ({ playUrl: jest.fn(), appendAudio: jest.fn(), useVoiceRecorder: jest.fn() }));
jest.mock('expo-router', () => ({
  router: { push: jest.fn(), replace: jest.fn(), back: jest.fn(), canGoBack: () => false },
  useLocalSearchParams: () => ({ id: 'b1_a' }),
}));

const apiMock = api as jest.Mock;

const ITEM = {
  id: 'e05', block: 1, type: 'gap', prompt: 'She ___ out.', prompt_pt: 'Ela saiu.', glossary: {}, options: null,
  words: null, audio_url: null, answered: false, result: null,
};

test('review plays the bank items with the run id and ends on the score', async () => {
  apiMock.mockImplementation(async (path: string) => {
    if (path === '/reviews/b1_a/start') return { run_id: 12, exercises: [ITEM] };
    if (path === '/exercises/b1_a/e05/answer')
      return { correct: true, correct_answer: 'went', explanation: 'ok', module_completed: true, score: 100, next_due: '2026-11-06' };
    throw new Error(path);
  });
  await render(<ReviewScreen />);
  expect(await screen.findByText('Revisão · 1 de 1')).toBeTruthy();
  await userEvent.type(screen.getByPlaceholderText('Sua resposta'), 'went');
  await userEvent.press(screen.getByText('Verificar'));
  expect(apiMock).toHaveBeenCalledWith('/exercises/b1_a/e05/answer',
    expect.objectContaining({ json: expect.objectContaining({ answer: 'went', run_id: 12 }) }));
  await userEvent.press(await screen.findByText('Ver resultado'));
  expect(await screen.findByText('100%')).toBeTruthy();
  expect(screen.getByText('Próxima revisão: 06/11')).toBeTruthy();
});
