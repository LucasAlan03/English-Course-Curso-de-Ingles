import { StyleSheet, View } from 'react-native';

import { useTheme } from '@/theme';
import { PillarKey, Pillars } from '@/types';

import { Text } from './ui';

const LABELS: Record<PillarKey, string> = {
  grammar: 'Gramática',
  speak: 'Falar',
  write: 'Escrever',
  read: 'Ler',
  watch: 'Assistir',
};
const ORDER: PillarKey[] = ['grammar', 'speak', 'write', 'read', 'watch'];

/** The five daily habits as a row of stops: filled when done today. */
export default function PillarBar({ pillars }: { pillars: Pillars }) {
  const theme = useTheme();
  return (
    <View style={styles.row}>
      {ORDER.map((key) => {
        const done = pillars[key];
        return (
          <View key={key} testID={`pillar-${key}`} accessibilityState={{ checked: done }} style={styles.item}>
            <View
              style={[
                styles.dot,
                { backgroundColor: done ? theme.good : theme.card, borderColor: done ? theme.good : theme.border },
              ]}
            >
              <Text style={{ color: done ? '#fff' : theme.border, fontWeight: '800', fontSize: 18 }}>{done ? '✓' : ''}</Text>
            </View>
            <Text style={{ color: done ? theme.text : theme.muted, fontSize: 12.5, fontWeight: done ? '700' : '500' }}>
              {LABELS[key]}
            </Text>
          </View>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', justifyContent: 'space-between', gap: 4 },
  item: { alignItems: 'center', gap: 6, flex: 1 },
  dot: { width: 46, height: 46, borderRadius: 23, borderWidth: 2, alignItems: 'center', justifyContent: 'center' },
});
