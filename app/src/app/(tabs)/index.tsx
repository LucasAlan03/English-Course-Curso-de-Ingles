import { describeError } from '@/errors';
import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { api } from '@/api';
import DayTrail from '@/components/DayTrail';
import NextBlockCard, { blockRoute } from '@/components/NextBlockCard';
import ReviewList from '@/components/ReviewList';
import Ridge from '@/components/Ridge';
import UsageBanner from '@/components/UsageBanner';
import { Button, Card, ErrorText, Muted, Screen, SectionTitle, Text } from '@/components/ui';
import { useTheme } from '@/theme';
import { syncReminders } from '@/reminders';
import { BlockKey, DayPlan, Home } from '@/types';
import { useApi } from '@/useApi';

const REGION: Record<string, string> = { A1: 'No vale', A2: 'Na trilha', B1: 'Na mata', B2: 'Na serra', C1: 'No cume' };

function PracticeTile({ title, hint, onPress }: { title: string; hint: string; onPress: () => void }) {
  const theme = useTheme();
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={({ pressed }) => [
        styles.tile,
        { backgroundColor: theme.card, borderColor: theme.border, opacity: pressed ? 0.85 : 1 },
      ]}
    >
      <Text style={{ color: theme.text, fontWeight: '800', fontSize: 17 }}>{title}</Text>
      <Text style={{ color: theme.muted, fontSize: 14, lineHeight: 19 }}>{hint}</Text>
    </Pressable>
  );
}

export default function HomeScreen() {
  const theme = useTheme();
  const { data, error, reload } = useApi<Home>('/home');
  const [actionError, setActionError] = useState('');
  const previous = useRef<DayPlan | null>(null);
  const shown = useRef<DayPlan | null>(null);
  if (data && data.today !== shown.current) {
    previous.current = shown.current;
    shown.current = data.today;
  }

  useEffect(() => {
    if (!data) return;
    api<{ times: string[] }>('/settings/reminders')
      .then((r) => (Array.isArray(r?.times) ? syncReminders(data.today, r.times) : undefined))
      .catch(() => undefined);
  }, [data]);

  async function act(path: string, json?: unknown) {
    setActionError('');
    try {
      await api(path, { method: 'POST', ...(json === undefined ? {} : { json }) });
      await reload();
    } catch (e) {
      setActionError(describeError(e));
    }
  }

  const routes = {
    nextModuleId: data?.next_module?.id ?? null,
    firstReviewId: data?.reviews_due[0]?.module_id ?? null,
    examLevel: data?.exam_ready ?? null,
  };
  const anki = data?.today.blocks.find((b) => b.key === 'anki');
  const toggleAnki = () => act('/today/anki', { checked: anki?.status !== 'done' });
  const open = (block: BlockKey) => {
    if (block === 'anki') return toggleAnki();
    const route = blockRoute(block, routes);
    if (route) router.push(route);
  };

  return (
    <Screen gap={14}>
      <View style={styles.header}>
        <Text accessibilityRole="header" style={{ color: theme.text, fontSize: 30, fontWeight: '800', letterSpacing: -0.8 }}>
          Vamos praticar
        </Text>
        {data ? (
          <View style={[styles.streak, { backgroundColor: data.streak > 0 ? theme.sun : theme.tint }]}>
            <Text style={{ color: data.streak > 0 ? theme.onSun : theme.muted, fontWeight: '700', fontSize: 14 }}>
              {data.streak === 1 ? '1 dia seguido' : `${data.streak} dias seguidos`}
            </Text>
          </View>
        ) : null}
      </View>

      {error || actionError ? <ErrorText>{error || actionError}</ErrorText> : null}
      {data ? (
        <>
          <UsageBanner usage={data.usage} />

          <NextBlockCard plan={data.today} previous={previous.current} onAnki={toggleAnki} {...routes} />

          <SectionTitle>Seu dia</SectionTitle>
          <DayTrail
            plan={data.today}
            onOpen={open}
            onSkip={(b) => act(`/today/${b}/skip`)}
            onUnskip={(b) => act(`/today/${b}/unskip`)}
            onAnki={(checked) => act('/today/anki', { checked })}
          />

          {data.next_module ? (
            <View style={[styles.hero, { backgroundColor: theme.pine }]}>
              <Ridge width={200} height={110} />
              <View style={[styles.chip, { backgroundColor: theme.pineSoft }]}>
                <Text style={{ color: theme.onPine, fontWeight: '700', fontSize: 13 }}>
                  {`${data.next_module.level}, ${REGION[data.next_module.level] ?? 'na trilha'}`}
                </Text>
              </View>
              <Text style={{ color: theme.onPine, fontSize: 30, fontWeight: '800', letterSpacing: -0.8, lineHeight: 34 }}>
                {data.next_module.title}
              </Text>
              <View style={{ alignSelf: 'flex-start', minWidth: 160, marginTop: 8 }}>
                <Button label="Começar" kind="sun" onPress={() => router.push(`/lesson/${data.next_module!.id}`)} />
              </View>
            </View>
          ) : (
            <Card>
              <Muted>Você concluiu todos os módulos. Continue com as revisões.</Muted>
            </Card>
          )}

          <SectionTitle>Revisões de hoje</SectionTitle>
          <ReviewList reviews={data.reviews_due} onOpen={(id) => router.push(`/review/${id}`)} />

          <SectionTitle>Praticar</SectionTitle>
          <View style={styles.tiles}>
            <PracticeTile title="Conversa livre" hint="Fale sobre qualquer assunto" onPress={() => router.push('/free')} />
            <PracticeTile title="Escrever um texto" hint="Receba o texto corrigido" onPress={() => router.push('/writing')} />
          </View>
        </>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' },
  streak: { borderRadius: 999, paddingVertical: 6, paddingHorizontal: 12 },
  hero: { borderRadius: 28, padding: 22, gap: 10, overflow: 'hidden', minHeight: 220, justifyContent: 'flex-end' },
  chip: { alignSelf: 'flex-start', borderRadius: 999, paddingVertical: 4, paddingHorizontal: 12 },
  tiles: { flexDirection: 'row', gap: 12 },
  tile: { flex: 1, borderWidth: 1, borderRadius: 20, padding: 16, gap: 4, minHeight: 96 },
});
