import { View } from 'react-native';

import { useTheme } from '@/theme';
import { ExamRun } from '@/types';

import { Button, Card, Muted, Text } from './ui';

const NEXT: Record<string, string> = { B1: 'B2', B2: 'C1' };

export default function ExamResult({ run, onRetry, onBack }: { run: ExamRun; onRetry: () => void; onBack: () => void }) {
  const theme = useTheme();
  const wrong = (run.results ?? []).filter((r) => !r.correct);
  const headline = run.passed
    ? NEXT[run.level] ? `Aprovado! ${NEXT[run.level]} liberado` : 'Aprovado! Você concluiu o C1'
    : `Faltou pouco: precisa de ${run.pass_percent}%`;
  return (
    <View style={{ gap: 14 }}>
      <Card style={{ padding: 22, gap: 8, alignItems: 'center' }}>
        <Text style={{ color: run.passed ? theme.good : theme.bad, fontSize: 18, fontWeight: '800' }}>{headline}</Text>
        <Text style={{ color: theme.text, fontSize: 44, fontWeight: '800' }}>{`${run.score ?? 0}%`}</Text>
      </Card>
      {wrong.length ? <Text style={{ color: theme.text, fontSize: 20, fontWeight: '800' }}>Para revisar</Text> : null}
      {wrong.map((r) => (
        <Card key={r.id} style={{ gap: 4 }}>
          <Text style={{ color: theme.muted, fontSize: 13, fontWeight: '700' }}>{r.module_title}</Text>
          <Text style={{ color: theme.text, fontSize: 16 }}>{r.prompt}</Text>
          {r.user_answer ? <Muted>{`Você: ${r.user_answer}`}</Muted> : null}
          <Text style={{ color: theme.good, fontSize: 15, fontWeight: '700' }}>{`Certa: ${r.correct_answer}`}</Text>
          <Muted>{r.explanation}</Muted>
        </Card>
      ))}
      {run.passed ? null : <Button label="Refazer prova" onPress={onRetry} />}
      <Button label="Voltar para a trilha" kind="secondary" onPress={onBack} />
    </View>
  );
}
