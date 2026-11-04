import { router } from 'expo-router';
import { ScrollView, StyleSheet, Text, View } from 'react-native';

import ModuleCard from '@/components/ModuleCard';
import { ErrorText, Muted } from '@/components/ui';
import { useTheme } from '@/theme';
import { Modules } from '@/types';
import { useApi } from '@/useApi';

export default function TracksScreen() {
  const theme = useTheme();
  const { data, error } = useApi<Modules>('/modules');
  const suggestedId = data?.levels.flatMap((l) => l.modules).find((m) => !m.completed)?.id;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {error ? <ErrorText>{error}</ErrorText> : null}
      {data?.levels.length === 0 ? <Muted>Nenhum módulo encontrado.</Muted> : null}
      {data?.levels.map((level) => (
        <View key={level.level} style={styles.level}>
          <View style={styles.levelHeader}>
            <Text style={{ color: theme.text, fontSize: 20, fontWeight: '700' }}>{level.level}</Text>
            <Text style={{ color: theme.muted }}>{`${level.completed}/${level.total}`}</Text>
          </View>
          {level.modules.map((module) => (
            <ModuleCard
              key={module.id}
              module={module}
              suggested={module.id === suggestedId}
              onPress={() => router.push(`/lesson/${module.id}`)}
            />
          ))}
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, gap: 18 },
  level: { gap: 8 },
  levelHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
});
