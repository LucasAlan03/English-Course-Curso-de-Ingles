import { describeError } from '@/errors';
import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, TextInput } from 'react-native';

import { api } from '@/api';
import { Button, Card, ErrorText, Muted, Screen, SectionTitle, Text } from '@/components/ui';
import { useTheme } from '@/theme';
import { Song } from '@/types';

export default function NewSongScreen() {
  const theme = useTheme();
  const [title, setTitle] = useState('');
  const [artist, setArtist] = useState('');
  const [link, setLink] = useState('');
  const [lyrics, setLyrics] = useState('');
  const [saved, setSaved] = useState<Song | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function save() {
    setBusy(true);
    setError('');
    try {
      setSaved(await api<Song>('/songs', {
        method: 'POST',
        json: { title: title.trim(), artist: artist.trim(), link: link.trim() || null, lyrics },
      }));
    } catch (e) {
      setError(describeError(e));
    } finally {
      setBusy(false);
    }
  }

  async function retryTag() {
    if (!saved) return;
    setBusy(true);
    try {
      setSaved(await api<Song>(`/songs/${saved.id}/tag`, { method: 'POST' }));
    } catch (e) {
      setError(describeError(e));
    } finally {
      setBusy(false);
    }
  }

  const input = [styles.input, { color: theme.text, borderColor: theme.border, backgroundColor: theme.card }];

  if (saved) {
    return (
      <Screen gap={14}>
        <SectionTitle>{saved.title}</SectionTitle>
        <Muted>{`${saved.total_chunks} trechos para aprender.`}</Muted>
        {saved.grammar_status === 'pending' ? (
          <Card>
            <Text style={{ color: theme.text, fontWeight: '700' }}>Marcação de gramática pendente</Text>
            <Muted>A IA não respondeu agora. A música já está salva; você pode tentar de novo depois.</Muted>
            <Button label="Tentar de novo" kind="secondary" disabled={busy} onPress={retryTag} />
          </Card>
        ) : null}
        {error ? <ErrorText>{error}</ErrorText> : null}
        <Button label="Ir para o trecho de hoje" onPress={() => router.replace('/songs/today')} />
      </Screen>
    );
  }

  return (
    <Screen gap={12}>
      <SectionTitle>Nova música</SectionTitle>
      <Muted>A letra fica só no seu computador (no banco local), nunca no código.</Muted>
      <TextInput value={title} onChangeText={setTitle} placeholder="Título" placeholderTextColor={theme.muted} style={input} />
      <TextInput value={artist} onChangeText={setArtist} placeholder="Artista" placeholderTextColor={theme.muted} style={input} />
      <TextInput value={link} onChangeText={setLink} placeholder="Link (YouTube ou Spotify)" placeholderTextColor={theme.muted}
        autoCapitalize="none" style={input} />
      <TextInput value={lyrics} onChangeText={setLyrics} placeholder="Cole a letra aqui" placeholderTextColor={theme.muted}
        multiline style={[input, { minHeight: 220, textAlignVertical: 'top' }]} />
      {error ? <ErrorText>{error}</ErrorText> : null}
      <Button label="Salvar música" disabled={busy || !title.trim() || !artist.trim() || !lyrics.trim()} onPress={save} />
    </Screen>
  );
}

const styles = StyleSheet.create({ input: { borderWidth: 1, borderRadius: 12, padding: 12, fontSize: 16 } });
