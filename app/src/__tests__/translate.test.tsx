import { render, screen, userEvent } from '@testing-library/react-native';

import { api } from '../api';
import TranslatableText from '../components/TranslatableText';
import TappableText from '../components/TappableText';
import WordsSection from '../components/WordsSection';
import { saveText } from '../download';
import { sentenceAround } from '../sentence';

jest.mock('../api', () => ({
  api: jest.fn(), apiText: jest.fn().mockResolvedValue('grim;sombrio\n'), audioUrl: (p: string) => p,
  ApiError: class extends Error {},
}));
jest.mock('../download', () => ({ saveText: jest.fn().mockResolvedValue(undefined) }));
jest.mock('expo-router', () => {
  const React = require('react');
  return { router: { push: jest.fn() }, useFocusEffect: (cb: () => void) => React.useEffect(cb, []) };
});

const apiMock = api as jest.Mock;
beforeEach(() => apiMock.mockReset());

test('sentenceAround picks the sentence that holds the word', () => {
  const text = 'First one. How many people done doubted you? Last one!';
  expect(sentenceAround(text, text.indexOf('done'))).toBe('How many people done doubted you?');
  expect(sentenceAround('line one\nline two here', 12)).toBe('line two here');
});

test('tapping a word asks the AI with its sentence and can save it', async () => {
  apiMock.mockImplementation(async (path: string) => {
    if (path === '/translate') return { translation: 'já', note: 'informal, rap', cached: false };
    if (path === '/words') return { id: 1 };
    throw new Error(path);
  });
  await render(<TranslatableText text="Hello there. How many people done doubted you?" />);
  await userEvent.press(screen.getByText('done'));
  expect(await screen.findByText('já')).toBeTruthy();
  expect(screen.getByText('informal, rap')).toBeTruthy();
  expect(apiMock).toHaveBeenCalledWith('/translate', expect.objectContaining({
    method: 'POST', json: { word: 'done', sentence: 'How many people done doubted you?' },
  }));
  await userEvent.press(screen.getByText('Salvar palavra'));
  expect(apiMock).toHaveBeenCalledWith('/words', expect.objectContaining({
    method: 'POST', json: expect.objectContaining({ word: 'done', translation: 'já', source: 'tap' }),
  }));
  expect(await screen.findByText('Salva!')).toBeTruthy();
});

test('translation error offers a retry', async () => {
  apiMock.mockRejectedValueOnce(new Error('down')).mockResolvedValueOnce({ translation: 'casa', note: '', cached: false });
  await render(<TranslatableText text="home" />);
  await userEvent.press(screen.getByText('home'));
  await userEvent.press(await screen.findByText('Tentar de novo'));
  expect(await screen.findByText('casa')).toBeTruthy();
});

test('glossary mode never calls the API', async () => {
  await render(<TappableText text="a grim night" glossary={{ grim: 'sombrio' }} promptPt="uma noite sombria" />);
  await userEvent.press(screen.getByText('grim'));
  expect(await screen.findByText('sombrio')).toBeTruthy();
  await userEvent.press(screen.getByText('night'));
  expect(await screen.findByText('Tradução da frase: uma noite sombria')).toBeTruthy();
  expect(apiMock).not.toHaveBeenCalled();
});

test('words section lists words and exports the CSV for Anki', async () => {
  apiMock.mockResolvedValue([{ id: 1, word: 'grim', sentence: '', translation: 'sombrio', note: '', source: 'tap', created_at: 'x' }]);
  await render(<WordsSection />);
  expect(await screen.findByText('Palavras novas (1)')).toBeTruthy();
  expect(screen.getByText('grim — sombrio')).toBeTruthy();
  await userEvent.press(screen.getByText('Exportar para o Anki'));
  expect(saveText).toHaveBeenCalledWith('palavras.csv', 'grim;sombrio\n', 'text/csv');
});
