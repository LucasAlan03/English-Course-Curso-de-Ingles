import { useColorScheme } from 'react-native';

const light = {
  background: '#f6f7f9',
  card: '#ffffff',
  text: '#16181d',
  muted: '#6a7280',
  primary: '#2f6df6',
  onPrimary: '#ffffff',
  border: '#e2e5ea',
  good: '#1f9d55',
  warn: '#d98a00',
  bad: '#d64545',
};

const dark: typeof light = {
  background: '#0f1115',
  card: '#1a1d24',
  text: '#f1f3f6',
  muted: '#9aa3b2',
  primary: '#6c9bff',
  onPrimary: '#0f1115',
  border: '#2a2f39',
  good: '#4cc38a',
  warn: '#f0b429',
  bad: '#ff7a7a',
};

export type Theme = typeof light;

export function useTheme(): Theme {
  return useColorScheme() === 'dark' ? dark : light;
}
