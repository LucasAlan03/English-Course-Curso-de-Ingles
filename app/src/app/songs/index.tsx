import { describeError } from '@/errors';
import { router } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';

import { api } from '@/api';
import { Button, Card, ErrorText, Muted, Screen, SectionTitle, Text } from '@/components/ui';
import { useTheme } from '@/theme';
import { Song } from '@/types';
import { useApi } from '@/useApi';

export default function SongsScreen() {
  const theme = useTheme();
  const songs = useApi<Song[]>('/songs');
  const [error, setError] = useState('');

  async function run(action: () => Promise<unknown>) {
    setError('');
    try {
      await action();
      await songs.reload();
    } catch (e) {
      setError(describeError(e));
    }
  }

  return (
    <Screen gap={12}>
      <SectionTitle>Minhas músicas</SectionTitle>
      {songs.error || error ? <ErrorText>{songs.error || error}</ErrorText> : null}
      {songs.data?.length === 0 ? <Muted>Nenhuma música ainda.</Muted> : null}
      {songs.data?.map((s) => (
        <Card key={s.id} style={{ gap: 8 }}>
          <Text style={{ color: theme.text, fontSize: 17, fontWeight: '700' }}>{`${s.is_current ? '★ ' : ''}${s.title}`}</Text>
          <Muted>{`${s.artist} · ${s.done_chunks}/${s.total_chunks} trechos`}</Muted>
          <View style={{ height: 8, borderRadius: 4, backgroundColor: theme.border, overflow: 'hidden' }}>
            <View style={{ width: `${s.total_chunks ? (100 * s.done_chunks) / s.total_chunks : 0}%`, height: '100%', backgroundColor: theme.good }} />
          </View>
          {!s.is_current ? (
            <Button label="Tornar música do momento" kind="secondary" onPress={() => run(() => api(`/songs/${s.id}/current`, { method: 'PUT' }))} />
          ) : null}
          <Button label="Excluir" kind="secondary" onPress={() => run(() => api(`/songs/${s.id}`, { method: 'DELETE' }))} />
        </Card>
      ))}
      <Button label="Cadastrar música" onPress={() => router.push('/songs/new')} />
    </Screen>
  );
}
