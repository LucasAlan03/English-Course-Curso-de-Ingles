import {
  AudioModule,
  RecordingPresets,
  createAudioPlayer,
  setAudioModeAsync,
  useAudioRecorder,
} from 'expo-audio';
import { useState } from 'react';
import { Platform } from 'react-native';

export type Recording = { uri: string; mime: string };

/** Push-to-talk recording: call start() on press and stop() on release. */
export function useVoiceRecorder() {
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const [isRecording, setIsRecording] = useState(false);
  const [denied, setDenied] = useState(false);

  async function start(): Promise<boolean> {
    const permission = await AudioModule.requestRecordingPermissionsAsync();
    if (!permission.granted) {
      setDenied(true);
      return false;
    }
    setDenied(false);
    await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
    await recorder.prepareToRecordAsync();
    recorder.record();
    setIsRecording(true);
    return true;
  }

  async function stop(): Promise<Recording | null> {
    if (!isRecording) return null;
    setIsRecording(false);
    await recorder.stop();
    await setAudioModeAsync({ allowsRecording: false });
    const uri = recorder.uri;
    if (!uri) return null;
    return { uri, mime: Platform.OS === 'web' ? 'audio/webm' : 'audio/mp4' };
  }

  return { start, stop, isRecording, denied };
}

/** Adds the recording to a multipart form under the field name the backend expects. */
export async function appendAudio(form: FormData, recording: Recording): Promise<void> {
  if (Platform.OS === 'web') {
    const blob = await (await fetch(recording.uri)).blob();
    form.append('audio', blob, 'clip.webm');
  } else {
    form.append('audio', { uri: recording.uri, name: 'clip.m4a', type: recording.mime } as unknown as Blob);
  }
}

/** Plays a remote clip and resolves when it finishes. */
export function playUrl(url: string): Promise<void> {
  return new Promise((resolve) => {
    const player = createAudioPlayer(url);
    const subscription = player.addListener('playbackStatusUpdate', (status) => {
      if (status.didJustFinish) {
        subscription.remove();
        player.release();
        resolve();
      }
    });
    player.play();
  });
}
