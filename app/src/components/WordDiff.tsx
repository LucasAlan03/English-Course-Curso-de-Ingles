import { StyleSheet, View } from 'react-native';

import { useTheme } from '@/theme';

import { Text } from './ui';

export type DiffToken = { word: string; status: 'ok' | 'missing' | 'wrong' | 'extra' };

const LABEL = { ok: 'certa', missing: 'faltou', wrong: 'errada', extra: 'sobrou' };

/** Word-by-word comparison: right words plain, missing struck through, wrong in red, extra in italics. */
export default function WordDiff({ tokens }: { tokens: DiffToken[] }) {
  const theme = useTheme();
  const look = {
    ok: { color: theme.text },
    missing: { color: theme.muted, textDecorationLine: 'line-through' as const },
    wrong: { color: theme.bad, fontWeight: '700' as const },
    extra: { color: theme.muted, fontStyle: 'italic' as const },
  };
  return (
    <View style={styles.row}>
      {tokens.map((t, i) => (
        <Text key={i} accessibilityLabel={`${t.word} (${LABEL[t.status]})`} style={[{ fontSize: 18 }, look[t.status]]}>
          {t.word}
        </Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({ row: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 } });
