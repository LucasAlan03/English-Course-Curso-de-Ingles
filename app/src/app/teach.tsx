import { describeError } from '@/errors';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';

import { api } from '@/api';
import { Button, Card, ErrorText, Muted, Screen, SectionTitle, Text } from '@/components/ui';
import { useTheme } from '@/theme';
import { Home, ModuleDetail } from '@/types';
import { useApi } from '@/useApi';

/**
 * Starts a call. Call 1 (kind=lesson): the module's scenario conversation.
 * Call 2 (default, kind=teach): you explain the module to a confused AI student.
 */
export default function TeachScreen() {
  const theme = useTheme();
  const params = useLocalSearchParams<{ kind?: string; module?: string }>();
  const kind = params.kind === 'lesson' ? 'lesson' : 'teach';
  // With a module param we load that module; otherwise the next module from the home screen.
  const home = useApi<Home | ModuleDetail>(params.module ? `/modules/${params.module}` : '/home');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const detail = params.module ? (home.data as ModuleDetail | null) : null;
  const module = detail ? { id: detail.id, title: detail.title } : (home.data as Home | null)?.next_module ?? null;
  const scenario = detail?.scenario;

  async function start() {
    if (!module) return;
    setBusy(true);
    setError('');
    try {
      const session = await api<{ id: number }>('/sessions', { method: 'POST', json: { kind, module_id: module.id } });
      router.replace(`/chat/${session.id}`);
    } catch (e) {
      setError(describeError(e));
      setBusy(false);
    }
  }

  return (
    <Screen gap={14}>
      <SectionTitle>{kind === 'teach' ? 'Ensine a IA' : 'Ligação 1'}</SectionTitle>
      {home.error || error ? <ErrorText>{home.error || error}</ErrorText> : null}
      {module ? (
        <Card style={{ gap: 8 }}>
          <Text style={{ color: theme.text, fontSize: 20, fontWeight: '800' }}>{module.title}</Text>
          {kind === 'teach' ? (
            <Muted>
              Você é o professor. A IA é uma aluna confusa: explique a regra, dê exemplos e corrija os erros dela.
              Ensinar fixa o conteúdo.
            </Muted>
          ) : (
            <Muted>{scenario ? `${scenario.title} · com ${scenario.character}` : 'Conversa do cenário do módulo.'}</Muted>
          )}
          <Muted>Meta: 10 minutos.</Muted>
        </Card>
      ) : !home.loading ? (
        <Muted>Nenhum módulo para praticar agora.</Muted>
      ) : null}
      <Button label={kind === 'teach' ? 'Começar a aula' : 'Começar a ligação'} disabled={!module || busy} onPress={start} />
    </Screen>
  );
}
