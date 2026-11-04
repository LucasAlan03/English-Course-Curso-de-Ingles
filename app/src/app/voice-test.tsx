import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { api, ApiError } from '@/api';
import { appendAudio, useVoiceRecorder } from '@/audio';
import { useTheme } from '@/theme';

export default function VoiceTest() {
  const theme = useTheme();
  const { start, stop, isRecording, denied } = useVoiceRecorder();
  const [text, setText] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function toggle() {
    if (!isRecording) {
      await start();
      return;
    }
    const recording = await stop();
    if (!recording) return;
    setBusy(true);
    setError('');
    try {
      const form = new FormData();
      await appendAudio(form, recording);
      const result = await api<{ text: string }>('/stt', { method: 'POST', body: form });
      setText(result.text);
    } catch (e) {
      setText('');
      setError(e instanceof ApiError ? e.detail : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={[styles.hint, { color: theme.muted }]}>
        Toque para começar a gravar, fale (em inglês ou português) e toque de novo para enviar. O texto reconhecido aparece abaixo.
      </Text>
      {denied ? (
        <Text style={{ color: theme.bad }}>Permissão do microfone negada. Libere nas configurações do aparelho.</Text>
      ) : null}
      <Pressable
        onPress={toggle}
        style={[styles.button, { backgroundColor: isRecording ? theme.bad : theme.primary }]}
      >
        <Text style={{ color: theme.onPrimary, fontWeight: '600' }}>
          {isRecording ? 'Gravando… toque para enviar' : busy ? 'Enviando…' : 'Toque para falar'}
        </Text>
      </Pressable>
      {text ? <Text style={[styles.result, { color: theme.text }]}>{text}</Text> : null}
      {error ? <Text style={{ color: theme.bad }}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, gap: 16 },
  hint: { fontSize: 15 },
  button: { padding: 20, borderRadius: 14, alignItems: 'center' },
  result: { fontSize: 20 },
});
