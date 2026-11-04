import { router } from 'expo-router';
import { ScrollView, StyleSheet, Text } from 'react-native';

import PillarBar from '@/components/PillarBar';
import ReviewList from '@/components/ReviewList';
import UsageBanner from '@/components/UsageBanner';
import { Button, Card, ErrorText, Muted, SectionTitle } from '@/components/ui';
import { useApi } from '@/useApi';
import { useTheme } from '@/theme';
import { Home } from '@/types';

export default function HomeScreen() {
  const theme = useTheme();
  const { data, error } = useApi<Home>('/home');

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {error ? <ErrorText>{error}</ErrorText> : null}
      {data ? (
        <>
          <UsageBanner usage={data.usage} />
          <SectionTitle>Hoje</SectionTitle>
          <PillarBar pillars={data.pillars} streak={data.streak} />

          <SectionTitle>Revisões de hoje</SectionTitle>
          <ReviewList reviews={data.reviews_due} onOpen={(id) => router.push(`/review/${id}`)} />

          <SectionTitle>Continuar trilha</SectionTitle>
          {data.next_module ? (
            <Card>
              <Muted>{data.next_module.level}</Muted>
              <Text style={{ color: theme.text, fontWeight: '600', fontSize: 16 }}>{data.next_module.title}</Text>
              <Button label="Começar" onPress={() => router.push(`/lesson/${data.next_module!.id}`)} />
            </Card>
          ) : (
            <Muted>Você concluiu todos os módulos. Continue com as revisões.</Muted>
          )}

          <SectionTitle>Praticar</SectionTitle>
          <Button label="Conversa livre" kind="secondary" onPress={() => router.push('/free')} />
          <Button label="Escrever um texto" kind="secondary" onPress={() => router.push('/writing')} />
        </>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({ container: { padding: 16, gap: 10 } });
