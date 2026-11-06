import { Pressable, StyleSheet, View } from 'react-native';

import { useTheme } from '@/theme';
import { BlockKey, DayPlan } from '@/types';

import { Text } from './ui';

type Props = {
  plan: DayPlan;
  onOpen: (block: BlockKey) => void;
  onSkip: (block: BlockKey) => void;
  onUnskip: (block: BlockKey) => void;
  onAnki: (checked: boolean) => void;
};

/** The 7 blocks of the day, in order, with the current one highlighted. */
export default function DayTrail({ plan, onOpen, onSkip, onUnskip, onAnki }: Props) {
  const theme = useTheme();
  return (
    <View style={{ gap: 8 }}>
      {plan.blocks.map((b, i) => {
        const current = b.status === 'current';
        const done = b.status === 'done';
        return (
          <Pressable key={b.key} testID={`block-${b.key}`} accessibilityRole="button" onPress={() => onOpen(b.key)}
            style={[styles.row, {
              backgroundColor: current ? theme.pine : theme.card,
              borderColor: current ? theme.pine : theme.border,
              opacity: b.status === 'skipped' ? 0.6 : 1,
            }]}>
            <View style={[styles.dot, { backgroundColor: done ? theme.good : current ? theme.sun : theme.border }]}>
              <Text style={{ color: done || current ? '#fff' : theme.muted, fontWeight: '800', fontSize: 14 }}>
                {done ? '✓' : String(i + 1)}
              </Text>
            </View>
            <View style={{ flex: 1, gap: 4 }}>
              <View style={styles.titleRow}>
                <Text style={{ color: current ? theme.onPine : theme.text, fontWeight: '700', fontSize: 16 }}>{b.title}</Text>
                {current ? <Text style={{ color: theme.sun, fontWeight: '800', fontSize: 13 }}>Agora</Text> : null}
                {b.status === 'skipped' ? <Text style={{ color: theme.muted, fontSize: 13 }}>Pulado</Text> : null}
              </View>
              {b.target ? (
                <View style={styles.barRow}>
                  <View style={[styles.track, { backgroundColor: current ? theme.pineSoft : theme.border }]}>
                    <View style={{ width: `${Math.min(1, (b.minutes ?? 0) / b.target) * 100}%`, height: '100%', backgroundColor: theme.sun, borderRadius: 3 }} />
                  </View>
                  <Text style={{ color: current ? theme.onPine : theme.muted, fontSize: 12 }}>{`${b.minutes ?? 0}/${b.target} min`}</Text>
                </View>
              ) : null}
            </View>
            {b.key === 'anki' ? (
              <Pressable accessibilityRole="checkbox" accessibilityLabel="Marcar Anki como feito" accessibilityState={{ checked: done }}
                onPress={() => onAnki(!done)} hitSlop={8}
                style={[styles.check, { borderColor: done ? theme.good : theme.border, backgroundColor: done ? theme.good : 'transparent' }]}>
                {done ? <Text style={{ color: '#fff', fontWeight: '800' }}>✓</Text> : null}
              </Pressable>
            ) : current ? (
              <Pressable accessibilityRole="button" onPress={() => onSkip(b.key)} hitSlop={8}>
                <Text style={{ color: theme.onPine, fontSize: 13, textDecorationLine: 'underline' }}>Pular</Text>
              </Pressable>
            ) : b.status === 'skipped' ? (
              <Pressable accessibilityRole="button" onPress={() => onUnskip(b.key)} hitSlop={8}>
                <Text style={{ color: theme.primary, fontSize: 13, fontWeight: '700' }}>Voltar</Text>
              </Pressable>
            ) : null}
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', gap: 12, borderWidth: 1, borderRadius: 18, padding: 12 },
  dot: { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  barRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  track: { flex: 1, height: 6, borderRadius: 3, overflow: 'hidden' },
  check: { width: 30, height: 30, borderRadius: 8, borderWidth: 2, alignItems: 'center', justifyContent: 'center' },
});
