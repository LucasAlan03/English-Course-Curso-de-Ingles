import { StyleSheet, View } from 'react-native';
import { Text } from '@/components/ui';

import { useTheme } from '@/theme';
import { FinishResult } from '@/types';

import { Card, Muted, SectionTitle } from './ui';

function shortDate(iso: string) {
  const [, month, day] = iso.split('-');
  return `${day}/${month}`;
}

export default function ReportView({ result }: { result: FinishResult }) {
  const theme = useTheme();
  const { report } = result;
  return (
    <View style={styles.container}>
      <Card style={styles.scoreCard}>
        <Muted>Nota final</Muted>
        <Text style={{ color: theme.primary, fontSize: 48, fontWeight: '800' }}>{String(result.final_score)}</Text>
        {result.next_due ? <Muted>{`Próxima revisão: ${shortDate(result.next_due)}`}</Muted> : null}
      </Card>

      <SectionTitle>Erros e correções</SectionTitle>
      {report.mistakes.length === 0 ? <Muted>Nenhum erro encontrado. Muito bem!</Muted> : null}
      {report.mistakes.map((m, i) => (
        <Card key={i}>
          <Text style={{ color: theme.bad, textDecorationLine: 'line-through' }}>{m.said}</Text>
          <Text style={{ color: theme.good, fontWeight: '600' }}>{m.corrected}</Text>
          <Text style={{ color: theme.text }}>{m.explanation}</Text>
        </Card>
      ))}

      {report.natural_expressions.length > 0 ? (
        <>
          <SectionTitle>Expressões mais naturais</SectionTitle>
          {report.natural_expressions.map((e, i) => (
            <Text key={i} style={{ color: theme.text, fontSize: 16 }}>
              {e}
            </Text>
          ))}
        </>
      ) : null}

      {report.strengths.length > 0 ? (
        <>
          <SectionTitle>Pontos fortes</SectionTitle>
          {report.strengths.map((s, i) => (
            <Text key={i} style={{ color: theme.text, fontSize: 16 }}>
              {`• ${s}`}
            </Text>
          ))}
        </>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 10 },
  scoreCard: { alignItems: 'center' },
});
