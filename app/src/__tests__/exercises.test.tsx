import { render, screen, userEvent, waitFor } from '@testing-library/react-native';

import { api } from '../api';
import ExercisePlayer from '../components/exercises/ExercisePlayer';
import TappableText from '../components/TappableText';
import LessonScreen from '../app/lesson/[id]';
import { Exercise } from '../types';

jest.mock('../api', () => ({ api: jest.fn(), audioUrl: (p: string) => `http://x${p}`, ApiError: class extends Error {} }));
jest.mock('../audio', () => ({ playUrl: jest.fn().mockResolvedValue(undefined), appendAudio: jest.fn(), useVoiceRecorder: jest.fn() }));
jest.mock('expo-router', () => {
  const React = require('react');
  return {
    router: { push: jest.fn(), replace: jest.fn(), back: jest.fn(), canGoBack: () => false },
    useLocalSearchParams: () => ({ id: 'b1_a' }),
    useFocusEffect: (cb: () => void) => React.useEffect(cb, []),
  };
});

const apiMock = api as jest.Mock;

function item(id: string, block: 1 | 2 | 3, type: Exercise['type'], extra: Partial<Exercise> = {}): Exercise {
  return {
    id, block, type, prompt: `Prompt ${id}`, prompt_pt: `Tradução ${id}`, glossary: {}, options: null, words: null,
    audio_url: null, answered: false, result: null, ...extra,
  };
}

const FEEDBACK = { correct: true, correct_answer: 'went', explanation: 'Past simple.' };

beforeEach(() => apiMock.mockReset());

test('resumes at the first unanswered item', async () => {
  const items = [
    item('e01', 1, 'choice', { options: ['went', 'go'], answered: true, result: { ...FEEDBACK, user_answer: 'went' } }),
    item('e02', 1, 'choice', { options: ['was', 'were'] }),
  ];
  await render(<ExercisePlayer items={items} submit={jest.fn()} play={jest.fn()} onDone={jest.fn()} />);
  expect(screen.getByText('Prompt e02')).toBeTruthy();
  expect(screen.getByText('Bloco 1 de 3 · Exercício 2 de 9')).toBeTruthy();
});

test('choosing an option submits the option text and shows the feedback', async () => {
  const submit = jest.fn().mockResolvedValue(FEEDBACK);
  const items = [item('e01', 1, 'choice', { options: ['went', 'go'] }), item('e02', 1, 'gap')];
  await render(<ExercisePlayer items={items} submit={submit} play={jest.fn()} onDone={jest.fn()} />);
  await userEvent.press(screen.getByText('went'));
  expect(submit).toHaveBeenCalledWith(items[0], 'went', expect.any(Number));
  expect(await screen.findByText('Correto!')).toBeTruthy();
  expect(screen.getByText('Past simple.')).toBeTruthy();
  await userEvent.press(screen.getByText('Próximo'));
  expect(screen.getByText('Prompt e02')).toBeTruthy();
});

test('order builds the sentence from taps and a tap removes a word', async () => {
  const submit = jest.fn().mockResolvedValue(FEEDBACK);
  const items = [item('e10', 2, 'order', { words: ['cooking', 'she', 'was'] })];
  await render(<ExercisePlayer items={items} submit={submit} play={jest.fn()} onDone={jest.fn()} />);
  await userEvent.press(screen.getByLabelText('Palavra she'));
  await userEvent.press(screen.getByLabelText('Palavra cooking'));
  await userEvent.press(screen.getByLabelText('Remover cooking'));
  await userEvent.press(screen.getByLabelText('Palavra was'));
  await userEvent.press(screen.getByLabelText('Palavra cooking'));
  await userEvent.press(screen.getByText('Verificar'));
  expect(submit).toHaveBeenCalledWith(items[0], 'she was cooking', expect.any(Number));
});

test('moving from block 1 to block 2 shows the transition screen', async () => {
  const submit = jest.fn().mockResolvedValue(FEEDBACK);
  const items = [item('e09', 1, 'gap'), item('e10', 2, 'gap')];
  await render(<ExercisePlayer items={items} submit={submit} play={jest.fn()} onDone={jest.fn()} />);
  await userEvent.type(screen.getByPlaceholderText('Sua resposta'), 'went');
  await userEvent.press(screen.getByText('Verificar'));
  await userEvent.press(await screen.findByText('Próximo'));
  expect(screen.getByText('Bloco 2 · Praticar')).toBeTruthy();
  await userEvent.press(screen.getByText('Começar'));
  expect(screen.getByText('Prompt e10')).toBeTruthy();
});

test('translation toggle and glossary work without the network', async () => {
  const items = [item('e01', 1, 'choice', { prompt: 'I went to the park', options: ['a', 'b'], glossary: { park: 'parque' } })];
  await render(<ExercisePlayer items={items} submit={jest.fn()} play={jest.fn()} onDone={jest.fn()} />);
  await userEvent.press(screen.getByText('Ver tradução'));
  expect(screen.getByText('Tradução e01')).toBeTruthy();
  await userEvent.press(screen.getByText('park'));
  expect(await screen.findByText('parque')).toBeTruthy();
  expect(apiMock).not.toHaveBeenCalled();
});

test('exam mode gives no feedback and moves straight on', async () => {
  const submit = jest.fn().mockResolvedValue(null);
  const onDone = jest.fn();
  const items = [item('q01', 1, 'gap'), item('q02', 1, 'gap')];
  await render(
    <ExercisePlayer items={items} submit={submit} play={jest.fn()} onDone={onDone} instantFeedback={false} title="Prova B1" />,
  );
  expect(screen.getByText('Prova B1 · 1 de 2')).toBeTruthy();
  await userEvent.type(screen.getByPlaceholderText('Sua resposta'), 'x');
  await userEvent.press(screen.getByText('Responder'));
  expect(await screen.findByText('Prompt q02')).toBeTruthy();
  expect(screen.queryByText('Correto!')).toBeNull();
  await userEvent.type(screen.getByPlaceholderText('Sua resposta'), 'y');
  await userEvent.press(screen.getByText('Responder'));
  await waitFor(() => expect(onDone).toHaveBeenCalled());
});

test('TappableText in glossary mode shows the sentence translation for other words', async () => {
  await render(<TappableText text="She was cooking dinner" glossary={{ dinner: 'jantar' }} promptPt="Ela estava fazendo o jantar" />);
  await userEvent.press(screen.getByText('cooking'));
  expect(await screen.findByText('Tradução da frase: Ela estava fazendo o jantar')).toBeTruthy();
});

const MODULE = {
  id: 'b1_a', level: 'B1', title: 'Past simple', completed: false, theory_md: '# Past simple\n- Regular verbs',
  scenario: { title: 'Weekend', character: 'A friend', goal: 'Talk' }, target_structures: ['past simple'],
};

test('lesson: last answer shows the module score and the next review', async () => {
  apiMock.mockImplementation(async (path: string) => {
    if (path === '/modules/b1_a') return MODULE;
    if (path === '/modules/b1_a/exercises') return [item('e27', 3, 'gap')];
    if (path === '/exercises/b1_a/e27/answer')
      return { ...FEEDBACK, module_completed: true, score: 89, next_due: '2026-11-04' };
    throw new Error(`unexpected ${path}`);
  });
  await render(<LessonScreen />);
  await userEvent.press(await screen.findByText('Pular teoria'));
  await userEvent.type(await screen.findByPlaceholderText('Sua resposta'), 'went');
  await userEvent.press(screen.getByText('Verificar'));
  await userEvent.press(await screen.findByText('Ver resultado'));
  expect(await screen.findByText('89%')).toBeTruthy();
  expect(screen.getByText('Próxima revisão: 04/11')).toBeTruthy();
});
