import { Pressable, StyleSheet, View } from 'react-native';

import { useTheme } from '@/theme';
import { ReviewDue } from '@/types';

import { Card, Muted, Text } from './ui';

function overdueLabel(days: number) {
  if (days <= 0) return 'Para hoje';
  return days === 1 ? '1 dia de atraso' : `${days} dias de atraso`;
}

export default function ReviewList({ reviews, onOpen }: { reviews: ReviewDue[]; onOpen: (moduleId: string) => void }) {
  const theme = useTheme();
  if (reviews.length === 0) return <Muted>Nenhuma revisão para hoje.</Muted>;
  return (
    <>
      {reviews.map((r) => (
        <Pressable key={r.module_id} testID="review-item" accessibilityRole="button" onPress={() => onOpen(r.module_id)}>
          <Card style={styles.card}>
            <View style={[styles.icon, { backgroundColor: r.overdue_days > 0 ? theme.sun : theme.tint }]}>
              <Text style={{ color: r.overdue_days > 0 ? theme.onSun : theme.pine, fontWeight: '800', fontSize: 20 }}>↻</Text>
            </View>
            <View style={{ flex: 1, gap: 2 }}>
              <Text style={{ color: theme.text, fontWeight: '700', fontSize: 16 }}>{r.title}</Text>
              <Text style={{ color: r.overdue_days > 0 ? theme.warn : theme.muted, fontSize: 14 }}>
                {overdueLabel(r.overdue_days)}
              </Text>
            </View>
          </Card>
        </Pressable>
      ))}
    </>
  );
}

const styles = StyleSheet.create({
  card: { flexDirection: 'row', alignItems: 'center', gap: 14, paddingVertical: 12 },
  icon: { width: 42, height: 42, borderRadius: 21, alignItems: 'center', justifyContent: 'center' },
});
