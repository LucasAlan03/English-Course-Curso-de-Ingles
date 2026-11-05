import { fireEvent, render, screen, userEvent, within } from '@testing-library/react-native';

import { api } from '../api';
import MediaForm from '../components/MediaForm';
import MediaSummary from '../components/MediaSummary';
import WritingScreen from '../app/writing';
import MediaScreen from '../app/(tabs)/media';

jest.mock('../api', () => ({ api: jest.fn(), audioUrl: (p: string) => p, ApiError: class extends Error {} }));
jest.mock('expo-router', () => {
  const React = require('react');
  return { router: { push: jest.fn(), replace: jest.fn() }, useFocusEffect: (cb: () => void) => React.useEffect(cb, []) };
});

const apiMock = api as jest.Mock;

beforeEach(() => apiMock.mockReset());

test('MediaForm blocks video minutes <= 0', async () => {
  const onSubmit = jest.fn();
  await render(<MediaForm date="2026-11-03" category="video" onSubmit={onSubmit} />);
  await userEvent.type(screen.getByPlaceholderText('Título'), 'Some video');
  await userEvent.type(screen.getByPlaceholderText('Minutos'), '0');
  await userEvent.press(screen.getByText('Salvar'));
  expect(onSubmit).not.toHaveBeenCalled();
  expect(await screen.findByText('Informe os minutos (de 1 a 1440).')).toBeTruthy();
});

test('MediaForm requires a title', async () => {
  const onSubmit = jest.fn();
  await render(<MediaForm date="2026-11-03" category="video" onSubmit={onSubmit} />);
  await userEvent.type(screen.getByPlaceholderText('Minutos'), '20');
  await userEvent.press(screen.getByText('Salvar'));
  expect(onSubmit).not.toHaveBeenCalled();
  expect(await screen.findByText('Informe o título.')).toBeTruthy();
});

test('series: episodes stepper multiplies the minutes per episode', async () => {
  const onSubmit = jest.fn();
  await render(<MediaForm date="2026-11-03" category="series" onSubmit={onSubmit} />);
  await userEvent.type(screen.getByPlaceholderText('Título'), 'Friends');
  await userEvent.type(screen.getByPlaceholderText('Min por episódio'), '22');
  await userEvent.press(screen.getByLabelText('Mais um episódio'));
  await userEvent.press(screen.getByLabelText('Mais um episódio'));
  expect(screen.getByText('3 × 22 = 66 min')).toBeTruthy();
  await userEvent.press(screen.getByText('Salvar'));
  expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
    date: '2026-11-03', type: 'watch', category: 'series', title: 'Friends', unit_minutes: 22, count: 3, minutes: 66,
  }));
});

test('video: pasting a YouTube link fills the title', async () => {
  apiMock.mockResolvedValue({ title: 'How I Went From Zero English to C2' });
  const onSubmit = jest.fn();
  await render(<MediaForm date="2026-11-03" category="video" onSubmit={onSubmit} />);
  const link = screen.getByPlaceholderText('Link do YouTube');
  await userEvent.type(link, 'https://youtu.be/3bh6Gb0oBN0');
  fireEvent(link, 'blur');
  expect(await screen.findByDisplayValue('How I Went From Zero English to C2')).toBeTruthy();
  expect(apiMock).toHaveBeenCalledWith(`/media/youtube-title?url=${encodeURIComponent('https://youtu.be/3bh6Gb0oBN0')}`);
  await userEvent.type(screen.getByPlaceholderText('Minutos'), '12');
  await userEvent.press(screen.getByText('Salvar'));
  expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
    category: 'video', title: 'How I Went From Zero English to C2', minutes: 12, url: 'https://youtu.be/3bh6Gb0oBN0',
  }));
});

test('reading saves pages and new words', async () => {
  const onSubmit = jest.fn();
  await render(<MediaForm date="2026-11-03" category="hq" onSubmit={onSubmit} />);
  await userEvent.type(screen.getByPlaceholderText('Título'), 'Batman');
  await userEvent.type(screen.getByPlaceholderText('Minutos'), '20');
  await userEvent.type(screen.getByPlaceholderText('Páginas'), '8');
  await userEvent.type(screen.getByPlaceholderText('Palavras novas (opcional)'), 'grim, vigilante');
  await userEvent.press(screen.getByText('Salvar'));
  expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
    type: 'read', category: 'hq', title: 'Batman', minutes: 20, pages: 8, new_words: 'grim, vigilante',
  }));
});

const SERIES = {
  id: 5, date: '2026-11-03', type: 'watch', category: 'series', title: 'Friends', episode: null, minutes: 44,
  pages: null, unit_minutes: 22, count: 2, url: null, new_words: null,
};

function mediaRoutes(extra: Record<string, unknown> = {}) {
  apiMock.mockImplementation(async (path: string, init?: { method?: string }) => {
    if (path.startsWith('/media?date=')) return [SERIES];
    if (path.startsWith('/media/summary')) return EMPTY_SUMMARY;
    if (path.startsWith('/calls?date=')) return { app_minutes: 4, external: [], total_minutes: 4 };
    if (path in extra) return extra[path];
    if (init?.method) return {};
    throw new Error(`unexpected ${path}`);
  });
}

const EMPTY = { total_minutes: 0, by_type: {}, by_category: {} };
const EMPTY_SUMMARY = { day: EMPTY, week: EMPTY, month: EMPTY };

test('media screen: + episode on a saved series updates its count', async () => {
  mediaRoutes();
  await render(<MediaScreen />);
  expect(await screen.findByText('2 × 22 = 44 min')).toBeTruthy();
  await userEvent.press(screen.getByLabelText('Mais um episódio de Friends'));
  expect(apiMock).toHaveBeenCalledWith('/media/5', expect.objectContaining({
    method: 'PUT', json: expect.objectContaining({ count: 3, unit_minutes: 22 }),
  }));
});

test('media screen: + outra série opens a new series form and an outside call is saved', async () => {
  mediaRoutes();
  await render(<MediaScreen />);
  await userEvent.press(await screen.findByText('+ outra série'));
  expect(screen.getByPlaceholderText('Min por episódio')).toBeTruthy();
  await userEvent.press(screen.getByText('+ lançar ligação'));
  await userEvent.type(screen.getByPlaceholderText('Onde (ex.: Be Confident)'), 'Be Confident');
  await userEvent.type(screen.getByPlaceholderText('Minutos da ligação'), '25');
  await userEvent.press(screen.getByText('Salvar ligação'));
  expect(apiMock).toHaveBeenCalledWith('/calls/external', expect.objectContaining({
    method: 'POST', json: expect.objectContaining({ source: 'Be Confident', minutes: 25 }),
  }));
  expect(screen.getByText('Ligações hoje: 4 min')).toBeTruthy();
});

test('MediaSummary shows totals by category for day, week and month', async () => {
  const summary = {
    day: { total_minutes: 62, by_type: { watch: 47, read: 15 }, by_category: { series: 47, hq: 15 } },
    week: { total_minutes: 92, by_type: { watch: 77, read: 15 }, by_category: { series: 47, hq: 15, podcast: 30 } },
    month: { total_minutes: 132, by_type: {}, by_category: {} },
  };
  await render(<MediaSummary summary={summary} />);
  const day = screen.getByTestId('summary-day');
  expect(within(day).getByText('62 min')).toBeTruthy();
  expect(within(day).getByText('Série: 47 min')).toBeTruthy();
  expect(within(day).getByText('HQ: 15 min')).toBeTruthy();
  expect(within(screen.getByTestId('summary-week')).getByText('Podcast: 30 min')).toBeTruthy();
  expect(within(screen.getByTestId('summary-month')).getByText('132 min')).toBeTruthy();
});

test('Writing: gets a topic, sends the text and shows the correction', async () => {
  apiMock.mockImplementation(async (path: string) => {
    if (path === '/writing/prompt') return { session_id: 3, prompt: 'Describe your last weekend.' };
    if (path === '/writing/submit')
      return {
        corrected_text: 'Last weekend I went to the beach.',
        improved_text: 'Last weekend I spent a lovely day at the beach.',
        mistakes: [{ said: 'I goed', corrected: 'I went', explanation: 'Passado irregular.', module_id: null }],
        score: 75,
      };
    throw new Error(`unexpected ${path}`);
  });
  await render(<WritingScreen />);
  expect(await screen.findByText('Describe your last weekend.')).toBeTruthy();
  await userEvent.type(screen.getByPlaceholderText('Escreva seu texto em inglês'), 'Last weekend I goed to the beach.');
  await userEvent.press(screen.getByText('Enviar para correção'));
  expect(await screen.findByText('Last weekend I went to the beach.')).toBeTruthy();
  expect(screen.getByText('Last weekend I spent a lovely day at the beach.')).toBeTruthy();
  expect(screen.getByText('Passado irregular.')).toBeTruthy();
  expect(apiMock).toHaveBeenCalledWith('/writing/submit', expect.objectContaining({ json: { session_id: 3, text: 'Last weekend I goed to the beach.' } }));
});
