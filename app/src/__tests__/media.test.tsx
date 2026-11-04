import { render, screen, userEvent, within } from '@testing-library/react-native';

import { api } from '../api';
import MediaForm from '../components/MediaForm';
import MediaSummary from '../components/MediaSummary';
import WritingScreen from '../app/writing';

jest.mock('../api', () => ({ api: jest.fn(), audioUrl: (p: string) => p, ApiError: class extends Error {} }));
jest.mock('expo-router', () => {
  const React = require('react');
  return { router: { push: jest.fn(), replace: jest.fn() }, useFocusEffect: (cb: () => void) => React.useEffect(cb, []) };
});

const apiMock = api as jest.Mock;

beforeEach(() => apiMock.mockReset());

test('MediaForm blocks minutes <= 0', async () => {
  const onSubmit = jest.fn();
  await render(<MediaForm date="2026-11-03" onSubmit={onSubmit} />);
  await userEvent.type(screen.getByPlaceholderText('Título'), 'Friends');
  await userEvent.type(screen.getByPlaceholderText('Minutos'), '0');
  await userEvent.press(screen.getByText('Salvar'));
  expect(onSubmit).not.toHaveBeenCalled();
  expect(await screen.findByText('Informe os minutos (de 1 a 1440).')).toBeTruthy();
});

test('MediaForm requires a title', async () => {
  const onSubmit = jest.fn();
  await render(<MediaForm date="2026-11-03" onSubmit={onSubmit} />);
  await userEvent.type(screen.getByPlaceholderText('Minutos'), '20');
  await userEvent.press(screen.getByText('Salvar'));
  expect(onSubmit).not.toHaveBeenCalled();
  expect(await screen.findByText('Informe o título.')).toBeTruthy();
});

test('MediaForm submits a watch entry with episode', async () => {
  const onSubmit = jest.fn();
  await render(<MediaForm date="2026-11-03" onSubmit={onSubmit} />);
  await userEvent.type(screen.getByPlaceholderText('Título'), 'Friends');
  await userEvent.type(screen.getByPlaceholderText('Episódio (opcional)'), 'S01E02');
  await userEvent.type(screen.getByPlaceholderText('Minutos'), '22');
  await userEvent.press(screen.getByText('Salvar'));
  expect(onSubmit).toHaveBeenCalledWith({
    date: '2026-11-03', type: 'watch', category: 'series', title: 'Friends',
    episode: 'S01E02', minutes: 22, pages: null,
  });
});

test('MediaForm switches to reading categories and pages', async () => {
  const onSubmit = jest.fn();
  await render(<MediaForm date="2026-11-03" onSubmit={onSubmit} />);
  await userEvent.press(screen.getByText('Ler'));
  await userEvent.press(screen.getByText('HQ'));
  await userEvent.type(screen.getByPlaceholderText('Título'), 'Maus');
  await userEvent.type(screen.getByPlaceholderText('Minutos'), '15');
  await userEvent.type(screen.getByPlaceholderText('Páginas (opcional)'), '12');
  await userEvent.press(screen.getByText('Salvar'));
  expect(onSubmit).toHaveBeenCalledWith({
    date: '2026-11-03', type: 'read', category: 'hq', title: 'Maus', episode: null, minutes: 15, pages: 12,
  });
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
