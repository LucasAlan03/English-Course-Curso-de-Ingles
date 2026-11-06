import { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { api } from '@/api';
import { useTheme } from '@/theme';

import { Text } from './ui';

function clock(seconds: number) {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
}

/** Active call time from the server (pauses longer than 3 min count 3 min), ticking locally in between. */
export default function CallTimer({ sessionId, target = 10 }: { sessionId: string; target?: number }) {
  const theme = useTheme();
  const [seconds, setSeconds] = useState<number | null>(null);

  useEffect(() => {
    let alive = true;
    const sync = () =>
      api<{ seconds: number }>(`/sessions/${sessionId}/elapsed`)
        .then((r) => alive && setSeconds(r.seconds))
        .catch(() => undefined);
    sync();
    const syncEvery = setInterval(sync, 30000);
    const tick = setInterval(() => setSeconds((s) => (s === null ? s : s + 1)), 1000);
    return () => {
      alive = false;
      clearInterval(syncEvery);
      clearInterval(tick);
    };
  }, [sessionId]);

  if (seconds === null) return null;
  const done = seconds >= target * 60;
  return (
    <View style={[styles.pill, { backgroundColor: done ? theme.good + '22' : theme.tint }]}>
      <Text style={{ color: done ? theme.good : theme.text, fontWeight: '700', fontSize: 14 }}>
        {`${clock(seconds)} / ${clock(target * 60)}`}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: { borderRadius: 999, paddingVertical: 4, paddingHorizontal: 12, alignSelf: 'flex-start' },
});
