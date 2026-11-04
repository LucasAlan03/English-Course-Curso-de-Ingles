import { useColorScheme } from 'react-native';

/**
 * Palette: a misty-forest trail. Pale sage ground, deep pine for ink and hero surfaces,
 * low-sun amber for "you are here", lake blue for secondary accents, coral for mistakes.
 */
const light = {
  background: '#ecf2ec',
  card: '#ffffff',
  text: '#12312a',
  muted: '#5b766b',
  primary: '#1b4d3e',
  onPrimary: '#ffffff',
  border: '#d3e0d6',
  good: '#2a9468',
  warn: '#c98a10',
  bad: '#d9523f',
  // trail + hero
  pine: '#14382e',
  onPine: '#f2f7f1',
  pineSoft: '#2a5a4a',
  sun: '#f4b63f',
  onSun: '#2b1d00',
  lake: '#2f7fa3',
  tint: '#e0ece3',
};

const dark: typeof light = {
  background: '#0d1914',
  card: '#15261f',
  text: '#e8f2ea',
  muted: '#93ada1',
  primary: '#f4b63f',
  onPrimary: '#2b1d00',
  border: '#24392f',
  good: '#4cc38a',
  warn: '#f0b429',
  bad: '#ff8a76',
  pine: '#14382e',
  onPine: '#f2f7f1',
  pineSoft: '#2a5a4a',
  sun: '#f4b63f',
  onSun: '#2b1d00',
  lake: '#6cb4d6',
  tint: '#1b3027',
};

export type Theme = typeof light;

export function useTheme(): Theme {
  return useColorScheme() === 'dark' ? dark : light;
}

export const fonts = {
  400: 'BricolageGrotesque_400Regular',
  500: 'BricolageGrotesque_500Medium',
  600: 'BricolageGrotesque_600SemiBold',
  700: 'BricolageGrotesque_700Bold',
  800: 'BricolageGrotesque_800ExtraBold',
} as const;
