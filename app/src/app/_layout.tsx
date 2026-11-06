import {
  BricolageGrotesque_400Regular,
  BricolageGrotesque_500Medium,
  BricolageGrotesque_600SemiBold,
  BricolageGrotesque_700Bold,
  BricolageGrotesque_800ExtraBold,
  useFonts,
} from '@expo-google-fonts/bricolage-grotesque';
import { Stack } from 'expo-router';
import { View } from 'react-native';

import { fonts, useTheme } from '@/theme';

export default function RootLayout() {
  const theme = useTheme();
  const [loaded, failed] = useFonts({
    BricolageGrotesque_400Regular,
    BricolageGrotesque_500Medium,
    BricolageGrotesque_600SemiBold,
    BricolageGrotesque_700Bold,
    BricolageGrotesque_800ExtraBold,
  });
  if (!loaded && !failed) return <View style={{ flex: 1, backgroundColor: theme.background }} />;

  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: theme.background },
        headerShadowVisible: false,
        headerTintColor: theme.text,
        headerTitleStyle: { fontFamily: fonts[700], fontSize: 18 },
        headerBackTitle: 'Voltar',
        contentStyle: { backgroundColor: theme.background },
      }}
    >
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="lesson/[id]" options={{ headerShown: false }} />
      <Stack.Screen name="review/[id]" options={{ headerShown: false }} />
      <Stack.Screen name="voice-test" options={{ title: 'Teste de voz' }} />
      <Stack.Screen name="chat/[sessionId]" options={{ title: 'Conversa', headerBackVisible: false }} />
      <Stack.Screen name="report/[sessionId]" options={{ title: 'Relatório', headerBackVisible: false }} />
      <Stack.Screen name="free" options={{ title: 'Conversa livre' }} />
      <Stack.Screen name="writing" options={{ title: 'Escrever um texto' }} />
      <Stack.Screen name="exam/[level]" options={{ headerShown: false }} />
      <Stack.Screen name="teach" options={{ title: 'Ligação' }} />
      <Stack.Screen name="songs/index" options={{ title: 'Minhas músicas' }} />
      <Stack.Screen name="songs/new" options={{ title: 'Nova música' }} />
      <Stack.Screen name="songs/today" options={{ title: 'Música do dia' }} />
    </Stack>
  );
}
