import { router } from 'expo-router';
import { ScrollView, StyleSheet } from 'react-native';
import { Text } from '@/components/ui';

import { Button, Card, Muted, SectionTitle } from '@/components/ui';
import ErrorNotice from '@/components/ErrorNotice';
import { brl } from '@/components/UsageBanner';
import { BASE_URL } from '@/config';
import { useTheme } from '@/theme';
import { UsageStatus } from '@/types';
import { useApi } from '@/useApi';

type SettingsData = {
  profile: string;
  providers: { chat: string; report: string; stt: string; tts: string };
  usage: UsageStatus;
};

const ROLE_LABELS: Record<keyof SettingsData['providers'], string> = {
  chat: 'Conversa',
  report: 'Relatórios e exercícios',
  stt: 'Reconhecimento de voz',
  tts: 'Voz da IA',
};

export default function SettingsScreen() {
  const theme = useTheme();
  const { data, error } = useApi<SettingsData>('/settings');

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <ErrorNotice error={error} />
      {data ? (
        <>
          <SectionTitle>Perfil de IA</SectionTitle>
          <Card>
            <Text style={{ color: theme.text, fontSize: 18, fontWeight: '700' }}>
              {data.profile === 'paid' ? 'Pago' : 'Gratuito'}
            </Text>
            {(Object.keys(ROLE_LABELS) as Array<keyof SettingsData['providers']>).map((role) => (
              <Muted key={role}>{`${ROLE_LABELS[role]}: ${data.providers[role]}`}</Muted>
            ))}
            <Muted>Para trocar, edite PROVIDER_PROFILE no .env do backend e reinicie.</Muted>
          </Card>

          <SectionTitle>Gasto do mês</SectionTitle>
          <Card>
            <Text style={{ color: theme.text, fontSize: 18, fontWeight: '700' }}>{brl(data.usage.total)}</Text>
            <Muted>{`Aviso em ${brl(data.usage.warn)} · teto em ${brl(data.usage.cap)}`}</Muted>
            <Muted>Estimativa do app. O saldo real fica no console de cada provedor.</Muted>
          </Card>
        </>
      ) : null}

      <SectionTitle>Servidor</SectionTitle>
      <Muted>{BASE_URL}</Muted>
      <Button label="Testar microfone" kind="secondary" onPress={() => router.push('/voice-test')} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({ container: { padding: 16, gap: 10 } });
