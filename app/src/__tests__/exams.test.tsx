import { render, screen, userEvent, within } from '@testing-library/react-native';

import { api } from '../api';
import TracksScreen from '../app/(tabs)/tracks';
import ExamScreen from '../app/exam/[level]';

jest.mock('../api', () => ({ api: jest.fn(), audioUrl: (p: string) => p, ApiError: class extends Error {} }));
jest.mock('../audio', () => ({ playUrl: jest.fn(), appendAudio: jest.fn(), useVoiceRecorder: jest.fn() }));
jest.mock('expo-router', () => {
  const React = require('react');
  return {
    router: { push: jest.fn(), replace: jest.fn(), back: jest.fn(), canGoBack: () => false },
    useLocalSearchParams: () => ({ level: 'B1' }),
    useFocusEffect: (cb: () => void) => React.useEffect(cb, []),
  };
});

const apiMock = api as jest.Mock;
const { router } = jest.requireMock('expo-router');

const EXAM = (over = {}) => ({ available: false, missing_modules: 1, passed: false, best_score: null, open_run_id: null, ...over });
const MODULES = {
  levels: [
    { level: 'B1', total: 2, completed: 2, unlocked: true, exam: EXAM({ available: true, missing_modules: 0 }),
      modules: [{ id: 'b1_a', title: 'Past simple', order: 1, completed: true }, { id: 'b1_b', title: 'Futuros', order: 2, completed: true }] },
    { level: 'B2', total: 1, completed: 0, unlocked: false, exam: EXAM(),
      modules: [{ id: 'b2_a', title: 'Voz passiva', order: 1, completed: false }] },
  ],
};

function q(id: string) {
  return { id, type: 'gap', prompt: `Q ${id}`, prompt_pt: null, glossary: {}, options: null, words: null, answered: false };
}

beforeEach(() => {
  apiMock.mockReset();
  router.push.mockClear();
});

test('locked level shows the lock and its modules do not open', async () => {
  apiMock.mockResolvedValue(MODULES);
  await render(<TracksScreen />);
  expect(await screen.findByText('🔒 Passe na prova de B1')).toBeTruthy();
  await userEvent.press(screen.getByTestId('module-b2_a'));
  expect(router.push).not.toHaveBeenCalled();
});

test('an available exam can be started from the trail', async () => {
  apiMock.mockResolvedValue(MODULES);
  await render(<TracksScreen />);
  await userEvent.press(await screen.findByText('Fazer prova'));
  expect(router.push).toHaveBeenCalledWith('/exam/B1');
  expect(screen.queryByTestId('exam-B2')).toBeNull(); // a locked level shows only its lock
});

test('an unlocked level with modules left shows how many are missing', async () => {
  const levels = [{ ...MODULES.levels[0], completed: 1, exam: EXAM({ missing_modules: 1 }) }];
  apiMock.mockResolvedValue({ levels });
  await render(<TracksScreen />);
  expect(within(await screen.findByTestId('exam-B1')).getByText('Faltam 1 módulos')).toBeTruthy();
});

test('exam gives no feedback between questions and a failed result lists the wrong ones', async () => {
  apiMock.mockImplementation(async (path: string) => {
    if (path === '/exams/B1/start') return { run_id: 3, level: 'B1', questions: [q('q01'), q('q02')] };
    if (path === '/exams/runs/3/q01/answer') return { saved: true, finished: false, score: null, passed: null };
    if (path === '/exams/runs/3/q02/answer') return { saved: true, finished: true, score: 50, passed: false };
    if (path === '/exams/runs/3')
      return { run_id: 3, level: 'B1', finished: true, score: 50, passed: false, pass_percent: 75, results: [
        { id: 'q01', prompt: 'Q q01', module_id: 'b1_a', module_title: 'Past simple', user_answer: 'goed', correct: false, correct_answer: 'went', explanation: 'Irregular.' },
        { id: 'q02', prompt: 'Q q02', module_id: 'b1_b', module_title: 'Futuros', user_answer: 'will', correct: true, correct_answer: 'will', explanation: 'ok' },
      ] };
    throw new Error(path);
  });
  await render(<ExamScreen />);
  expect(await screen.findByText('Prova B1 · 1 de 2')).toBeTruthy();
  await userEvent.type(screen.getByPlaceholderText('Sua resposta'), 'goed');
  await userEvent.press(screen.getByText('Responder'));
  expect(await screen.findByText('Q q02')).toBeTruthy();
  expect(screen.queryByText('Correto!')).toBeNull();
  await userEvent.type(screen.getByPlaceholderText('Sua resposta'), 'will');
  await userEvent.press(screen.getByText('Responder'));
  expect(await screen.findByText('Faltou pouco: precisa de 75%')).toBeTruthy();
  expect(screen.getByText('50%')).toBeTruthy();
  expect(screen.getByText('Past simple')).toBeTruthy();
  expect(screen.getByText('Certa: went')).toBeTruthy();
  expect(screen.queryByText('Futuros')).toBeNull();
  apiMock.mockClear();
  await userEvent.press(screen.getByText('Refazer prova'));
  expect(apiMock).toHaveBeenCalledWith('/exams/B1/start', expect.objectContaining({ method: 'POST' }));
});
