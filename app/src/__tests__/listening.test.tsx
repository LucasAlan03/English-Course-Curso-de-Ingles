import { render, screen, userEvent, waitFor } from '@testing-library/react-native';

import { api } from '../api';
import { playUrl } from '../audio';
import ListeningStep from '../components/ListeningStep';
import MarkdownText from '../components/MarkdownText';
import LessonScreen from '../app/lesson/[id]';

jest.mock('../api', () => ({ api: jest.fn(), audioUrl: (p: string) => `http://x${p}`, ApiError: class extends Error {} }));
jest.mock('../audio', () => ({ playUrl: jest.fn().mockResolvedValue(undefined), appendAudio: jest.fn(), useVoiceRecorder: jest.fn() }));
jest.mock('expo-router', () => {
  const React = require('react');
  return {
    router: { push: jest.fn(), replace: jest.fn() },
    useLocalSearchParams: () => ({ id: 'b1_a' }),
    useFocusEffect: (cb: () => void) => React.useEffect(cb, []),
  };
});

const apiMock = api as jest.Mock;
const { router } = jest.requireMock('expo-router');

const MODULE = {
  id: 'b1_a', level: 'B1', title: 'Past simple', completed: false,
  theory_md: '# Past simple\n- Regular verbs end in **-ed**\n- Irregular verbs change',
  scenario: { title: 'Weekend', character: 'A friend', goal: 'Talk about the weekend' },
  target_structures: ['past simple'],
};

const CHOICE = { id: 1, kind: 'choice' as const, prompt: 'What did she do?', options: ['went', 'go', 'gone'], audio_url: '/audio/a.wav' };
const GAP = { id: 2, kind: 'gap' as const, prompt: 'She ___ out.', options: null, audio_url: '/audio/b.wav' };

beforeEach(() => {
  apiMock.mockReset();
  (playUrl as jest.Mock).mockClear();
  router.replace.mockClear();
});

test('MarkdownText renders headings, bullets and bold text', async () => {
  await render(<MarkdownText text={'# Title\n- first point\n- uses **bold** words'} />);
  expect(screen.getByText('Title')).toBeTruthy();
  expect(screen.getByText(/first point/)).toBeTruthy();
  expect(screen.getByText('bold')).toBeTruthy();
});

test('Theory skip button goes to the listening step', async () => {
  apiMock.mockImplementation(async (path: string) => {
    if (path === '/modules/b1_a') return MODULE;
    if (path === '/sessions') return { id: 7 };
    if (path === '/sessions/7/listening') return [CHOICE];
    throw new Error(`unexpected ${path}`);
  });
  await render(<LessonScreen />);
  await screen.findByText('Regular verbs end in', { exact: false });
  await userEvent.press(screen.getByText('Pular teoria'));
  expect(await screen.findByText('What did she do?')).toBeTruthy();
  expect(apiMock).toHaveBeenCalledWith('/sessions', expect.objectContaining({ method: 'POST', json: { kind: 'lesson', module_id: 'b1_a' } }));
});

test('ListeningStep shows the correction after answering', async () => {
  const checkAnswer = jest.fn().mockResolvedValue({ correct: false, correct_answer: 'went', explanation: 'Passado simples de go.' });
  await render(<ListeningStep items={[CHOICE]} checkAnswer={checkAnswer} play={jest.fn()} onFinish={jest.fn()} />);
  await userEvent.press(screen.getByText('gone'));
  expect(checkAnswer).toHaveBeenCalledWith(1, 'gone');
  expect(await screen.findByText('Resposta certa: went')).toBeTruthy();
  expect(screen.getByText('Passado simples de go.')).toBeTruthy();
});

test('a gap item accepts a typed answer', async () => {
  const checkAnswer = jest.fn().mockResolvedValue({ correct: true, correct_answer: 'went', explanation: 'Isso!' });
  await render(<ListeningStep items={[GAP]} checkAnswer={checkAnswer} play={jest.fn()} onFinish={jest.fn()} />);
  await userEvent.type(screen.getByPlaceholderText('Digite a palavra'), 'went');
  await userEvent.press(screen.getByText('Verificar'));
  expect(checkAnswer).toHaveBeenCalledWith(2, 'went');
  expect(await screen.findByText('Correto!')).toBeTruthy();
});

test('the last item leads to the conversation', async () => {
  const onFinish = jest.fn();
  const checkAnswer = jest.fn().mockResolvedValue({ correct: true, correct_answer: 'went', explanation: 'ok' });
  await render(<ListeningStep items={[CHOICE]} checkAnswer={checkAnswer} play={jest.fn()} onFinish={onFinish} />);
  await userEvent.press(screen.getByText('went'));
  await userEvent.press(await screen.findByText('Ir para a conversa'));
  expect(onFinish).toHaveBeenCalledTimes(1);
});

test('the audio button plays the item clip', async () => {
  const play = jest.fn();
  await render(<ListeningStep items={[CHOICE]} checkAnswer={jest.fn()} play={play} onFinish={jest.fn()} />);
  await userEvent.press(screen.getByText('Ouvir'));
  expect(play).toHaveBeenCalledWith('/audio/a.wav');
});

test('finishing the lesson listening opens the chat of the created session', async () => {
  apiMock.mockImplementation(async (path: string) => {
    if (path === '/modules/b1_a') return MODULE;
    if (path === '/sessions') return { id: 7 };
    if (path === '/sessions/7/listening') return [CHOICE];
    if (path === '/listening/1/answer') return { correct: true, correct_answer: 'went', explanation: 'ok' };
    throw new Error(`unexpected ${path}`);
  });
  await render(<LessonScreen />);
  await userEvent.press(await screen.findByText('Continuar'));
  await userEvent.press(await screen.findByText('went'));
  await userEvent.press(await screen.findByText('Ir para a conversa'));
  await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/chat/7'));
});

test('MarkdownText never shows raw asterisks, even for nested examples', async () => {
  await render(<MarkdownText text={'- Past simple: *I **watched** a movie.*\n- Erro: *I was go* ou *I goed*.'} />);
  expect(screen.getByText('watched')).toBeTruthy();
  expect(screen.queryByText(/\*/)).toBeNull();
});
