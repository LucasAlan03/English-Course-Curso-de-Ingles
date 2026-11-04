import { StyleSheet, Text, View } from 'react-native';

import { CATEGORY_LABELS } from '@/labels';
import { useTheme } from '@/theme';
import { MediaSummary as Summary, MediaTotals } from '@/types';

import { Card, Muted } from './ui';

function Block({ id, title, totals }: { id: string; title: string; totals: MediaTotals }) {
  const theme = useTheme();
  return (
    <View testID={id} style={styles.block}>
      <Card>
        <Muted>{title}</Muted>
        <Text style={{ color: theme.text, fontSize: 22, fontWeight: '700' }}>{`${totals.total_minutes} min`}</Text>
        {Object.entries(totals.by_category).map(([category, minutes]) => (
          <Text key={category} style={{ color: theme.muted }}>
            {`${CATEGORY_LABELS[category] ?? category}: ${minutes} min`}
          </Text>
        ))}
      </Card>
    </View>
  );
}

export default function MediaSummary({ summary }: { summary: Summary }) {
  return (
    <View style={styles.row}>
      <Block id="summary-day" title="Hoje" totals={summary.day} />
      <Block id="summary-week" title="Semana" totals={summary.week} />
      <Block id="summary-month" title="Mês" totals={summary.month} />
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  block: { flexGrow: 1, flexBasis: 140 },
});
