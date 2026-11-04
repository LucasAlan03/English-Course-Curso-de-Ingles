import { describeError } from '@/errors';
import { router, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ScrollView, StyleSheet } from 'react-native';

import { api } from '@/api';
import ReportView from '@/components/ReportView';
import { Button, ErrorText, Muted } from '@/components/ui';
import { FinishResult } from '@/types';

export default function ReportScreen() {
  const { sessionId } = useLocalSearchParams<{ sessionId: string }>();
  const [result, setResult] = useState<FinishResult | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const started = useRef(false);

  // Finishing is safe to repeat: the server keeps one report per session and only counts it once.
  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setResult(await api<FinishResult>(`/sessions/${sessionId}/finish`, { method: 'POST' }));
    } catch (e) {
      setError(describeError(e));
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (started.current) return; // React may run effects twice in development
    started.current = true;
    load();
  }, [load]);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {loading ? <Muted>Gerando o relatório…</Muted> : null}
      {error ? <ErrorText>{error}</ErrorText> : null}
      {error && !loading ? <Button label="Tentar de novo" onPress={load} /> : null}
      {result ? <ReportView result={result} /> : null}
      <Button label="Voltar ao início" kind={result ? 'primary' : 'secondary'} onPress={() => router.replace('/')} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({ container: { padding: 16, gap: 12 } });
