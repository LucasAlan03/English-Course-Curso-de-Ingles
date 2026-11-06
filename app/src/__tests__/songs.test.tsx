import { render, screen, userEvent } from '@testing-library/react-native';

import { api } from '../api';
import WordDiff from '../components/WordDiff';
import SongToday from '../app/songs/today';
import NewSong from '../app/songs/new';

jest.mock('../api', () => ({ api: jest.fn(), audioUrl: (p: string) => p, ApiError: class extends Error {} }));
jest.mock('../audio', () => ({ playUrl: jest.fn(), appendAudio: jest.fn(), useVoiceRecorder: () => ({ start: jest.fn(), stop: jest.fn(), isRecording: false, denied: false }) }));
jest.mock('expo-router', () => {
  const React = require('react');
  return {
    router: { push: jest.fn(), replace: jest.fn(), back: jest.fn() },
    useLocalSearchParams: () => ({}),
    useFocusEffect: (cb: () => void) => React.useEffect(cb, []),
  };
});

const apiMock = api as jest.Mock;
const { router } = jest.requireMock('expo-router');

const SONG = { id: 1, title: 'Rain Song', artist: 'Nobody', link: 'https://youtu.be/x', grammar_status: 'done',
  is_current: true, total_chunks: 3, done_chunks: 1 };
const CHUNK = { id: 7, idx: 1, text: 'I was walking home\nwhen the rain began',
  highlights: [{ phrase: 'I was walking', module_id: 'b1_past_continuous' }], module_titles: ['Past continuous'] };

function today(stage: string, extra = {}) {
  return { song: SONG, chunk: CHUNK, review_chunks: [], progress: { done: 1, total: 3 }, stage, ...extra };
}

beforeEach(() => apiMock.mockReset());

test('WordDiff marks each word status', async () => {
  await render(<WordDiff tokens={[{ word: 'his', status: 'ok' }, { word: 'palms', status: 'wrong' }, { word: 'sweaty', status: 'missing' }]} />);
  expect(screen.getByLabelText('palms (errada)')).toBeTruthy();
  expect(screen.getByLabelText('sweaty (faltou)')).toBeTruthy();
});

test('no song yet shows the add button', async () => {
  apiMock.mockResolvedValue({ song: null, chunk: null, review_chunks: [], progress: { done: 0, total: 0 }, stage: 'no_song' });
  await render(<SongToday />);
  await userEvent.press(await screen.findByText('Cadastrar música'));
  expect(router.push).toHaveBeenCalledWith('/songs/new');
});

test('dictation hides the lyrics and shows the word diff after sending', async () => {
  apiMock.mockImplementation(async (path: string) => {
    if (path === '/songs/current/today') return today('dictation');
    if (path === '/songs/chunks/7/dictation')
      return { score: 50, expected: CHUNK.text, tokens: [{ word: 'i', status: 'ok' }, { word: 'rain', status: 'missing' }] };
    throw new Error(path);
  });
  await render(<SongToday />);
  expect(await screen.findByText('Rain Song · 1/3 trechos')).toBeTruthy();
  expect(screen.queryByText(/walking home/)).toBeNull();
  await userEvent.type(screen.getByPlaceholderText('Escreva o que você ouviu'), 'I was walking');
  await userEvent.press(screen.getByText('Comparar'));
  expect(await screen.findByText('50% das palavras')).toBeTruthy();
  expect(screen.getByLabelText('rain (faltou)')).toBeTruthy();
});

test('shadow stage shows the lyrics with the grammar chip', async () => {
  apiMock.mockResolvedValue(today('shadow'));
  await render(<SongToday />);
  expect(await screen.findByText('Past continuous')).toBeTruthy();
  expect(screen.getAllByText(/walking/).length).toBeGreaterThan(0);
  expect(screen.getByText('Toque para falar')).toBeTruthy();
});

test('new song posts the lyrics and warns when grammar is pending', async () => {
  apiMock.mockResolvedValue({ ...SONG, grammar_status: 'pending' });
  await render(<NewSong />);
  await userEvent.type(screen.getByPlaceholderText('Título'), 'Rain Song');
  await userEvent.type(screen.getByPlaceholderText('Artista'), 'Nobody');
  await userEvent.type(screen.getByPlaceholderText('Cole a letra aqui'), 'line one');
  await userEvent.press(screen.getByText('Salvar música'));
  expect(apiMock).toHaveBeenCalledWith('/songs', expect.objectContaining({
    method: 'POST', json: expect.objectContaining({ title: 'Rain Song', artist: 'Nobody', lyrics: 'line one' }),
  }));
  expect(await screen.findByText('Marcação de gramática pendente')).toBeTruthy();
});
