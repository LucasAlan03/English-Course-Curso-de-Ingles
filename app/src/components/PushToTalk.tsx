import { Pressable, StyleSheet, Text } from 'react-native';

import { Recording, useVoiceRecorder } from '@/audio';
import { useTheme } from '@/theme';

import { ErrorText } from './ui';

/** Hold to record, release to send. */
export default function PushToTalk({ onRecorded, disabled }: { onRecorded: (r: Recording) => void; disabled?: boolean }) {
  const theme = useTheme();
  const { start, stop, isRecording, denied } = useVoiceRecorder();

  async function release() {
    const recording = await stop();
    if (recording) onRecorded(recording);
  }

  return (
    <>
      {denied ? <ErrorText>Permissão do microfone negada. Libere nas configurações do aparelho.</ErrorText> : null}
      <Pressable
        disabled={disabled}
        onPressIn={start}
        onPressOut={release}
        style={[
          styles.button,
          { backgroundColor: isRecording ? theme.bad : theme.primary },
          disabled && { opacity: 0.5 },
        ]}
      >
        <Text style={{ color: theme.onPrimary, fontWeight: '700' }}>
          {isRecording ? 'Gravando… solte para enviar' : 'Segurar para falar'}
        </Text>
      </Pressable>
    </>
  );
}

const styles = StyleSheet.create({ button: { padding: 18, borderRadius: 14, alignItems: 'center' } });
