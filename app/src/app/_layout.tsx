import { Stack } from 'expo-router';

import { useTheme } from '@/theme';

export default function RootLayout() {
  const theme = useTheme();
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: theme.card },
        headerTintColor: theme.text,
        contentStyle: { backgroundColor: theme.background },
      }}
    />
  );
}
