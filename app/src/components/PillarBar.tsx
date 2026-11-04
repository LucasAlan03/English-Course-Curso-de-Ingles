import { StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@/theme';
import { PillarKey, Pillars } from '@/types';

const LABELS: Record<PillarKey, string> = {
  grammar: 'Gramática',
  speak: 'Falar',
  write: 'Escrever',
  read: 'Ler',
  watch: 'Assistir',
};
const ORDER: PillarKey[] = ['grammar', 'speak', 'write', 'read', 'watch'];

export default function PillarBar({ pillars, streak }: { pillars: Pillars; streak: number }) {
  const theme = useTheme();
  return (
    <View style={styles.wrapper}>
      <View style={styles.row}>
        {ORDER.map((key) => {
          const done = pillars[key];
          return (
            <View
              key={key}
              testID={`pillar-${key}`}
              accessibilityState={{ checked: done }}
              style={[
                styles.pillar,
                { backgroundColor: done ? theme.good : theme.card, borderColor: done ? theme.good : theme.border },
              ]}
            >
              <Text style={{ color: done ? theme.onPrimary : theme.muted, fontSize: 12, fontWeight: '600' }}>
                {done ? '✓ ' : ''}
                {LABELS[key]}
              </Text>
            </View>
          );
        })}
      </View>
      <Text style={{ color: theme.muted }}>{streak === 1 ? '1 dia seguido' : `${streak} dias seguidos`}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: 8 },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  pillar: { borderWidth: 1, borderRadius: 999, paddingVertical: 6, paddingHorizontal: 10 },
});
