import { render, screen, userEvent, waitFor } from '@testing-library/react-native';

import { api } from '../api';
import { playUrl } from '../audio';
import ReportView from '../components/ReportView';
import ChatScreen from '../app/chat/[sessionId]';
import FreeScreen from '../app/free';
import ReportScreen from '../app/report/[sessionId]';
import ReviewScreen from '../app/review/[id]';

let mockParams: Record<string, string> = { sessionId: '5' };

jest.mock('../api', () => ({ api: jest.fn(), audioUrl: (p: string) => `http://x${p}`, ApiError: class extends Error {} }));
jest.mock('../audio', () => ({
  playUrl: jest.fn().mockResolvedValue(undefined),
  appendAudio: jest.fn().mockResolvedValue(undefined),
  useVoiceRecorder: () => {
    const React = require('react');
    const [isRecording, setIsRecording] = React.useState(false);
    return {
      start: async () => {
        setIsRecording(true);
        return true;
      },
      stop: async () => {
        setIsRecording(false);
        return { uri: 'file://clip', mime: 'audio/webm' };
      },
      isRecording,
      denied: false,
    };
  },
}));
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

const REPORT = {
  report: {
    mistakes: [{ said: 'I goed home', corrected: 'I went home', explanation: 'Passado irregular.', module_id: 'b1_a' }],
    natural_expressions: ['How was your weekend?'],
    strengths: ['Bom vocabulário'],
    score: 82,
  },
  listening_score: 80,
  conversation_score: 82,
  final_score: 81,
  next_due: '2026-11-04',
};

const ERR = (code: string, detail: string) => Object.assign(new Error(detail), { code, detail });

beforeEach(() => {
  apiMock.mockReset();
  (playUrl as jest.Mock).mockClear();
  router.replace.mockClear();
  mockParams = { sessionId: '5' };
});

function turnReplies(...replies: Array<{ user_text: string; reply_text: string; reply_audio_url?: string | null } | Error>) {
  const queue = [...replies];
  apiMock.mockImplementation(async (path: string) => {
    if (path !== '/sessions/5/turn') throw new Error(`unexpected ${path}`);
    const next = queue.shift()!;
    if (next instanceof Error) throw next;
    return { reply_audio_url: null, ...next };
  });
}

test('the AI opens the conversation', async () => {
  turnReplies({ user_text: '', reply_text: 'Hi! What can I get you?' });
  await render(<ChatScreen />);
  expect(await screen.findByText('Hi! What can I get you?')).toBeTruthy();
});

test('chat sends typed text and shows both sides', async () => {
  turnReplies({ user_text: '', reply_text: 'Hello!' }, { user_text: 'I went home', reply_text: 'Nice, why?' });
  await render(<ChatScreen />);
  await screen.findByText('Hello!');
  await userEvent.type(screen.getByPlaceholderText('Escreva em inglês'), 'I went home');
  await userEvent.press(screen.getByText('Enviar'));
  expect(await screen.findByText('I went home')).toBeTruthy();
  expect(await screen.findByText('Nice, why?')).toBeTruthy();
});

test('tap once to record and tap again to send; empty_transcript shows a retry message', async () => {
  turnReplies(
    { user_text: '', reply_text: 'Hello!' },
    ERR('empty_transcript', 'Não consegui ouvir nada. Repita, por favor.'),
  );
  await render(<ChatScreen />);
  await screen.findByText('Hello!');
  await userEvent.press(screen.getByText('Toque para falar'));
  expect(await screen.findByText('Gravando… toque para enviar')).toBeTruthy();
  expect(apiMock).toHaveBeenCalledTimes(1); // nothing is sent while recording
  await userEvent.press(screen.getByText('Gravando… toque para enviar'));
  expect(await screen.findByText('Não consegui ouvir nada. Repita, por favor.')).toBeTruthy();
  expect(await screen.findByText('Toque para falar')).toBeTruthy();
});

test('replies are played when listening is on', async () => {
  turnReplies({ user_text: '', reply_text: 'Hello!', reply_audio_url: '/audio/r.wav' });
  await render(<ChatScreen />);
  await screen.findByText('Hello!');
  await waitFor(() => expect(playUrl).toHaveBeenCalledWith('http://x/audio/r.wav'));
});

test('finish navigates to the report', async () => {
  turnReplies({ user_text: '', reply_text: 'Hello!' });
  await render(<ChatScreen />);
  await screen.findByText('Hello!');
  await userEvent.press(screen.getByText('Encerrar e ver relatório'));
  expect(router.replace).toHaveBeenCalledWith('/report/5');
});

test('ReportView lists mistakes with corrections and the next review', async () => {
  await render(<ReportView result={REPORT} />);
  expect(screen.getByText('81')).toBeTruthy();
  expect(screen.getByText('I goed home')).toBeTruthy();
  expect(screen.getByText('I went home')).toBeTruthy();
  expect(screen.getByText('Passado irregular.')).toBeTruthy();
  expect(screen.getByText('How was your weekend?')).toBeTruthy();
  expect(screen.getByText(/04\/11/)).toBeTruthy();
});

test('ReportView celebrates a clean conversation', async () => {
  await render(<ReportView result={{ ...REPORT, report: { ...REPORT.report, mistakes: [] } }} />);
  expect(screen.getByText('Nenhum erro encontrado. Muito bem!')).toBeTruthy();
});

test('ReportScreen finishes the session and shows the report', async () => {
  apiMock.mockResolvedValue(REPORT);
  await render(<ReportScreen />);
  expect(await screen.findByText('I goed home')).toBeTruthy();
  expect(apiMock).toHaveBeenCalledWith('/sessions/5/finish', expect.objectContaining({ method: 'POST' }));
});

test('ReportScreen explains when there was nothing to report', async () => {
  apiMock.mockRejectedValue(ERR('no_user_messages', 'Fale ou escreva algo antes de encerrar.'));
  await render(<ReportScreen />);
  expect(await screen.findByText('Fale ou escreva algo antes de encerrar.')).toBeTruthy();
});

test('FreeScreen creates a free session and opens the chat', async () => {
  apiMock.mockResolvedValue({ id: 9 });
  await render(<FreeScreen />);
  await userEvent.type(screen.getByPlaceholderText('Assunto (opcional)'), 'football');
  await userEvent.press(screen.getByText('Começar conversa'));
  await waitFor(() => expect(router.replace).toHaveBeenCalledWith('/chat/9'));
  expect(apiMock).toHaveBeenCalledWith('/sessions', expect.objectContaining({ json: { kind: 'free', topic: 'football' } }));
});

test('ReviewScreen starts a review session and its short listening', async () => {
  mockParams = { id: 'b1_a' };
  apiMock.mockImplementation(async (path: string) => {
    if (path === '/sessions') return { id: 11 };
    if (path === '/sessions/11/listening')
      return [{ id: 1, kind: 'choice', prompt: 'Pick one', options: ['a', 'b', 'c'], audio_url: '/audio/a.wav' }];
    throw new Error(`unexpected ${path}`);
  });
  await render(<ReviewScreen />);
  expect(await screen.findByText('Pick one')).toBeTruthy();
  expect(apiMock).toHaveBeenCalledWith('/sessions', expect.objectContaining({ json: { kind: 'review', module_id: 'b1_a' } }));
});

test('ReportScreen offers a retry after an error and then shows the report', async () => {
  apiMock
    .mockRejectedValueOnce(ERR('invalid_ai_output', 'A IA devolveu uma resposta inválida. Tente de novo.'))
    .mockResolvedValueOnce(REPORT);
  await render(<ReportScreen />);
  await userEvent.press(await screen.findByText('Tentar de novo'));
  expect(await screen.findByText('I goed home')).toBeTruthy();
  expect(apiMock).toHaveBeenCalledTimes(2);
});

test('ReportScreen asks for the report only once per visit', async () => {
  apiMock.mockResolvedValue(REPORT);
  await render(<ReportScreen />);
  await screen.findByText('I goed home');
  expect(apiMock).toHaveBeenCalledTimes(1);
});
