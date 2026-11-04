import { render, screen, waitFor, within } from '@testing-library/react-native';

import { api } from '../api';
import PillarBar from '../components/PillarBar';
import HomeScreen from '../app/(tabs)/index';
import TracksScreen from '../app/(tabs)/tracks';

jest.mock('../api', () => ({ api: jest.fn(), audioUrl: (p: string) => p, ApiError: class extends Error {} }));
jest.mock('expo-router', () => {
  const React = require('react');
  return {
    router: { push: jest.fn() },
    useFocusEffect: (cb: () => void) => React.useEffect(cb, []),
  };
});

const apiMock = api as jest.Mock;

function respondWith(routes: Record<string, unknown>) {
  apiMock.mockImplementation(async (path: string) => routes[path]);
}

const HOME = {
  reviews_due: [
    { module_id: 'b1_a', title: 'Past simple', next_due: '2026-11-01', overdue_days: 2 },
    { module_id: 'b1_b', title: 'Futuros', next_due: '2026-11-03', overdue_days: 0 },
  ],
  next_module: { id: 'b1_c', title: 'Condicionais', level: 'B1' },
  pillars: { grammar: true, speak: false, write: false, read: true, watch: false },
  streak: 3,
  usage: { total: 0, warn: 45, cap: 50, level: 'ok' },
};

const MODULES = {
  levels: [
    {
      level: 'B1', total: 2, completed: 1,
      modules: [
        { id: 'b1_a', title: 'Past simple', order: 1, completed: true },
        { id: 'b1_b', title: 'Futuros', order: 2, completed: false },
      ],
    },
    { level: 'B2', total: 1, completed: 0, modules: [{ id: 'b2_a', title: 'Voz passiva', order: 1, completed: false }] },
  ],
};

beforeEach(() => apiMock.mockReset());

test('PillarBar renders 5 pillars with done state', async () => {
  await render(<PillarBar pillars={HOME.pillars} />);
  for (const key of ['grammar', 'speak', 'write', 'read', 'watch']) {
    expect(screen.getByTestId(`pillar-${key}`)).toBeTruthy();
  }
  expect(screen.getByTestId('pillar-grammar').props.accessibilityState.checked).toBe(true);
  expect(screen.getByTestId('pillar-speak').props.accessibilityState.checked).toBe(false);
  expect(screen.getByText(/Gramática/)).toBeTruthy();
});

test('Home shows overdue reviews first and the next module', async () => {
  respondWith({ '/home': HOME });
  await render(<HomeScreen />);
  await waitFor(() => expect(screen.getAllByTestId('review-item')).toHaveLength(2));
  const items = screen.getAllByTestId('review-item');
  expect(within(items[0]).getByText('Past simple')).toBeTruthy();
  expect(within(items[0]).getByText('2 dias de atraso')).toBeTruthy();
  expect(within(items[1]).getByText('Futuros')).toBeTruthy();
  expect(screen.getByText('Condicionais')).toBeTruthy();
});

test('Home says so when there is nothing to review', async () => {
  respondWith({ '/home': { ...HOME, reviews_due: [] } });
  await render(<HomeScreen />);
  expect(await screen.findByText('Nenhuma revisão para hoje.')).toBeTruthy();
});

test('Home shows an error message when the server is unreachable', async () => {
  apiMock.mockRejectedValue(Object.assign(new Error('x'), { detail: 'Não consegui falar com o servidor.' }));
  await render(<HomeScreen />);
  expect(await screen.findByText('Não consegui falar com o servidor.')).toBeTruthy();
});

test('Tracks marks the suggested next module and the completed ones', async () => {
  respondWith({ '/modules': MODULES });
  await render(<TracksScreen />);
  await screen.findByText('Futuros');
  expect(within(screen.getByTestId('module-b1_b')).getByText('Próximo')).toBeTruthy();
  expect(within(screen.getByTestId('module-b1_a')).getByText('Concluído')).toBeTruthy();
  expect(within(screen.getByTestId('module-b2_a')).queryByText('Próximo')).toBeNull();
  expect(screen.getByText('1/2')).toBeTruthy();
});
