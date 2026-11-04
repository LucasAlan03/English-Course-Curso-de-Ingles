import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet } from 'react-native';

import { api } from '@/api';
import ReportView from '@/components/ReportView';
import { Button, ErrorText, Muted } from '@/components/ui';
import { FinishResult } from '@/types';

export default function ReportScreen() {
  const { sessionId } = useLocalSearchParams<{ sessionId: string }>();
  const [result, setResult] = useState<FinishResult | null>(null);
  const [error, setError] = useState('');

  // Finishing is idempotent on the server, so reopening this screen shows the same report.
  useEffect(() => {
    api<FinishResult>(`/sessions/${sessionId}/finish`, { method: 'POST' })
      .then(setResult)
      .catch((e) => setError((e as { detail?: string }).detail ?? String(e)));
  }, [sessionId]);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {!result && !error ? <Muted>Gerando o relatório…</Muted> : null}
      {error ? <ErrorText>{error}</ErrorText> : null}
      {result ? <ReportView result={result} /> : null}
      <Button label="Voltar ao início" onPress={() => router.replace('/')} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({ container: { padding: 16, gap: 12 } });
