import { Pressable, Text } from 'react-native';

import { useTheme } from '@/theme';
import { ReviewDue } from '@/types';

import { Card, Muted } from './ui';

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
        <Pressable key={r.module_id} testID="review-item" onPress={() => onOpen(r.module_id)}>
          <Card>
            <Text style={{ color: theme.text, fontWeight: '600', fontSize: 16 }}>{r.title}</Text>
            <Text style={{ color: r.overdue_days > 0 ? theme.warn : theme.muted }}>{overdueLabel(r.overdue_days)}</Text>
          </Card>
        </Pressable>
      ))}
    </>
  );
}
