import { render, screen, userEvent, waitFor, within } from '@testing-library/react-native';

import { api } from '../api';
import HomeScreen from '../app/(tabs)/index';
import NextBlockCard from '../components/NextBlockCard';
import { remindersToSchedule } from '../reminders';
import { DayPlan } from '../types';

jest.mock('../api', () => ({ api: jest.fn(), audioUrl: (p: string) => p, ApiError: class extends Error {} }));
jest.mock('../reminders', () => ({ ...jest.requireActual('../reminders'), syncReminders: jest.fn() }));
jest.mock('expo-router', () => {
  const React = require('react');
  return { router: { push: jest.fn() }, useFocusEffect: (cb: () => void) => React.useEffect(cb, []) };
});

const apiMock = api as jest.Mock;
const { router } = jest.requireMock('expo-router');

function plan(statuses: Partial<Record<string, string>> = {}, extra: Partial<DayPlan> = {}): DayPlan {
  const keys = ['grammar', 'music', 'call1', 'watch', 'read', 'call2', 'anki'] as const;
  const titles = ['Gramática', 'Música', 'Ligação 1', 'Assistir', 'Ler', 'Ligação 2', 'Anki'];
  const blocks = keys.map((key, i) => ({
    key, title: titles[i], status: (statuses[key] ?? 'pending') as DayPlan['blocks'][number]['status'],
    minutes: key === 'music' || key === 'anki' ? null : 0, target: { grammar: 20, call1: 10, watch: 45, read: 40, call2: 10 }[key as string] ?? null,
  }));
  const current = blocks.find((b) => b.status === 'current')?.key ?? null;
  return { date: '2026-11-03', blocks, current, complete: blocks.every((b) => b.status === 'done'), ...extra };
}

const HOME = (today: DayPlan) => ({
  reviews_due: [], next_module: { id: 'b1_verb_to', title: 'Verbo + to', level: 'B1' }, today, streak: 2,
  usage: { total: 0, warn: 45, cap: 50, level: 'ok' },
});

beforeEach(() => {
  apiMock.mockReset();
  router.push.mockClear();
});

test('reminders: only later times today, listing what is missing', () => {
  const now = new Date(2026, 10, 3, 20, 0);
  const items = remindersToSchedule(['19:00', '21:00', '22:30'], now, plan({ grammar: 'done', music: 'current' }));
  expect(items.map((i) => i.at.getHours())).toEqual([21, 22]);
  expect(items[0].body).toBe('Faltam: Música, Ligação 1, Assistir, Ler, Ligação 2, Anki');
});

test('reminders: nothing when the day is complete', () => {
  const done = plan(Object.fromEntries(['grammar', 'music', 'call1', 'watch', 'read', 'call2', 'anki'].map((k) => [k, 'done'])));
  expect(remindersToSchedule(['21:00'], new Date(2026, 10, 3, 8, 0), done)).toEqual([]);
});

test('home shows the 7 blocks with the current one highlighted', async () => {
  apiMock.mockResolvedValue(HOME(plan({ grammar: 'done', music: 'current' })));
  await render(<HomeScreen />);
  await waitFor(() => expect(screen.getAllByTestId(/^block-/)).toHaveLength(7));
  expect(within(screen.getByTestId('block-music')).getByText('Agora')).toBeTruthy();
  expect(within(screen.getByTestId('block-grammar')).getByText('✓')).toBeTruthy();
  expect(screen.getByText('2 dias seguidos')).toBeTruthy();
});

test('pressing Pular posts the skip and reloads the day', async () => {
  apiMock.mockResolvedValue(HOME(plan({ grammar: 'current' })));
  await render(<HomeScreen />);
  await userEvent.press(await screen.findByText('Pular'));
  expect(apiMock).toHaveBeenCalledWith('/today/grammar/skip', expect.objectContaining({ method: 'POST' }));
  expect(apiMock.mock.calls.filter(([p]) => p === '/home').length).toBeGreaterThan(1);
});

test('skipped block offers Voltar and the Anki block has a check', async () => {
  apiMock.mockResolvedValue(HOME(plan({ grammar: 'skipped', music: 'current' })));
  await render(<HomeScreen />);
  await userEvent.press(await screen.findByText('Voltar'));
  expect(apiMock).toHaveBeenCalledWith('/today/grammar/unskip', expect.objectContaining({ method: 'POST' }));
  await userEvent.press(screen.getByLabelText('Marcar Anki como feito'));
  expect(apiMock).toHaveBeenCalledWith('/today/anki', expect.objectContaining({ json: { checked: true } }));
});

test('next block card celebrates a block that was just finished', async () => {
  const before = plan({ grammar: 'current' });
  const after = plan({ grammar: 'done', music: 'current' });
  await render(<NextBlockCard plan={after} previous={before} nextModuleId="b1_verb_to" />);
  expect(screen.getByText('Boa! Agora: Música')).toBeTruthy();
  await userEvent.press(screen.getByText('Ir'));
  expect(router.push).toHaveBeenCalledWith('/songs/today');
});

test('next block card routes grammar to the next lesson and call 2 to teach', async () => {
  await render(<NextBlockCard plan={plan({ grammar: 'current' })} previous={null} nextModuleId="b1_verb_to" />);
  expect(screen.getByText('Agora: Gramática')).toBeTruthy();
  await userEvent.press(screen.getByText('Ir'));
  expect(router.push).toHaveBeenCalledWith('/lesson/b1_verb_to');
  router.push.mockClear();
  await render(<NextBlockCard plan={plan({ grammar: 'done', music: 'done', call1: 'done', watch: 'done', read: 'done', call2: 'current' })} previous={null} nextModuleId="b1_verb_to" />);
  await userEvent.press(screen.getByText('Ir'));
  expect(router.push).toHaveBeenCalledWith('/teach');
});

test('reminder times can be edited in settings', async () => {
  const { default: RemindersSection } = require('../components/RemindersSection');
  apiMock.mockResolvedValue({ times: ['19:00', '21:00'] });
  await render(<RemindersSection />);
  const input = await screen.findByDisplayValue('19:00, 21:00');
  await userEvent.clear(input);
  await userEvent.type(input, '07:30, 20:00');
  await userEvent.press(screen.getByText('Salvar horários'));
  expect(apiMock).toHaveBeenCalledWith('/settings/reminders', expect.objectContaining({
    method: 'PUT', json: { times: ['07:30', '20:00'] },
  }));
});
