import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ScrollView, StyleSheet, Switch, Text, TextInput, View } from 'react-native';

import { api, audioUrl } from '@/api';
import { Recording, appendAudio, playUrl } from '@/audio';
import ChatBubble from '@/components/ChatBubble';
import PushToTalk from '@/components/PushToTalk';
import { Button, ErrorText, Muted } from '@/components/ui';
import { useTheme } from '@/theme';
import { TurnResult } from '@/types';

type Bubble = { role: 'user' | 'assistant'; text: string };

export default function ChatScreen() {
  const theme = useTheme();
  const { sessionId } = useLocalSearchParams<{ sessionId: string }>();
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [typed, setTyped] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [listen, setListen] = useState(true);
  const opened = useRef(false);

  async function send(text?: string, recording?: Recording) {
    setBusy(true);
    setError('');
    try {
      const form = new FormData();
      if (text) form.append('text', text);
      if (recording) await appendAudio(form, recording);
      form.append('want_audio', String(listen));
      const result = await api<TurnResult>(`/sessions/${sessionId}/turn`, { method: 'POST', body: form });
      setBubbles((current) => [
        ...current,
        ...(result.user_text ? [{ role: 'user' as const, text: result.user_text }] : []),
        { role: 'assistant' as const, text: result.reply_text },
      ]);
      if (listen && result.reply_audio_url) playUrl(audioUrl(result.reply_audio_url));
    } catch (e) {
      const err = e as { code?: string; detail?: string };
      if (err.code !== 'empty_message') setError(err.detail ?? String(e)); // empty_message: the chat was already opened
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (opened.current) return;
    opened.current = true;
    send();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function submitTyped() {
    const text = typed.trim();
    if (!text || busy) return;
    setTyped('');
    send(text);
  }

  return (
    <View style={styles.screen}>
      <View style={styles.topRow}>
        <Muted>Ouvir respostas</Muted>
        <Switch value={listen} onValueChange={setListen} />
      </View>

      <ScrollView contentContainerStyle={styles.messages}>
        {bubbles.map((b, i) => (
          <ChatBubble key={i} role={b.role} text={b.text} />
        ))}
        {busy ? <Muted>…</Muted> : null}
        {error ? <ErrorText>{error}</ErrorText> : null}
      </ScrollView>

      <View style={styles.composer}>
        <PushToTalk disabled={busy} onRecorded={(r) => send(undefined, r)} />
        <View style={styles.inputRow}>
          <TextInput
            value={typed}
            onChangeText={setTyped}
            placeholder="Escreva em inglês"
            placeholderTextColor={theme.muted}
            onSubmitEditing={submitTyped}
            style={[styles.input, { color: theme.text, borderColor: theme.border, backgroundColor: theme.card }]}
          />
          <Button label="Enviar" onPress={submitTyped} disabled={busy || !typed.trim()} />
        </View>
        <Button label="Encerrar e ver relatório" kind="secondary" onPress={() => router.replace(`/report/${sessionId}`)} />
        <Text style={{ color: theme.muted, fontSize: 12, textAlign: 'center' }}>
          Sem limite de trocas. Encerre quando quiser.
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  topRow: { flexDirection: 'row', justifyContent: 'flex-end', alignItems: 'center', gap: 8, padding: 12 },
  messages: { padding: 16, gap: 10 },
  composer: { padding: 12, gap: 10 },
  inputRow: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  input: { flex: 1, borderWidth: 1, borderRadius: 12, padding: 12, fontSize: 16 },
});
