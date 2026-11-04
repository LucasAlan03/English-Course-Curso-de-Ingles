import { router } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';
import { initialWindowMetrics } from 'react-native-safe-area-context';

import { useTheme } from '@/theme';

import { Text } from './ui';

export type LessonStage = 'theory' | 'listening' | 'chat';
const STAGES: { key: LessonStage; label: string }[] = [
  { key: 'theory', label: 'Teoria' },
  { key: 'listening', label: 'Listening' },
  { key: 'chat', label: 'Conversa' },
];

export function leave() {
  if (router.canGoBack()) router.back();
  else router.replace('/');
}

/** Replaces the raw route header: a close button plus the three stages of a lesson. */
export default function LessonBar({ stage, title }: { stage: LessonStage; title?: string }) {
  const theme = useTheme();
  const current = STAGES.findIndex((s) => s.key === stage);
  return (
    <View style={[styles.bar, { paddingTop: (initialWindowMetrics?.insets.top ?? 0) + 10 }]}>
      <Pressable accessibilityRole="button" accessibilityLabel="Fechar" onPress={leave} hitSlop={12} style={[styles.close, { backgroundColor: theme.tint }]}>
        <Text style={{ color: theme.text, fontSize: 18, fontWeight: '700' }}>✕</Text>
      </Pressable>
      <View style={styles.stages}>
        <View style={styles.segments}>
          {STAGES.map((s, i) => (
            <View
              key={s.key}
              style={[styles.segment, { backgroundColor: i <= current ? theme.sun : theme.border }]}
            />
          ))}
        </View>
        <Text style={{ color: theme.muted, fontSize: 13, fontWeight: '600' }} numberOfLines={1}>
          {title ?? STAGES[current].label}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  bar: { flexDirection: 'row', alignItems: 'center', gap: 14, paddingHorizontal: 16, paddingBottom: 6, width: '100%', maxWidth: 640, alignSelf: 'center' },
  close: { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center' },
  stages: { flex: 1, gap: 4 },
  segments: { flexDirection: 'row', gap: 6 },
  segment: { flex: 1, height: 8, borderRadius: 4 },
});
