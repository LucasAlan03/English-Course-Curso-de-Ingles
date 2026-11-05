import { router } from 'expo-router';

import TrailMap from '@/components/TrailMap';
import { ErrorText, Muted, Screen, Text } from '@/components/ui';
import { useTheme } from '@/theme';
import { Modules } from '@/types';
import { useApi } from '@/useApi';

export default function TracksScreen() {
  const theme = useTheme();
  const { data, error } = useApi<Modules>('/modules');
  const suggestedId = data?.levels
    .filter((l) => l.unlocked !== false)
    .flatMap((l) => l.modules)
    .find((m) => !m.completed)?.id;

  return (
    <Screen gap={16}>
      <Text accessibilityRole="header" style={{ color: theme.text, fontSize: 30, fontWeight: '800', letterSpacing: -0.8 }}>
        Sua trilha
      </Text>
      {error ? <ErrorText>{error}</ErrorText> : null}
      {data?.levels.length === 0 ? <Muted>Nenhum módulo encontrado.</Muted> : null}
      {data ? <TrailMap levels={data.levels} suggestedId={suggestedId} onOpen={(id) => router.push(`/lesson/${id}`)}
        onExam={(level) => router.push(`/exam/${level}`)} /> : null}
    </Screen>
  );
}
