import { router } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { useTheme } from '@/theme';
import { BlockKey, DayPlan } from '@/types';

import { Button, Text } from './ui';

type Props = {
  plan: DayPlan;
  /** The plan seen before the latest reload, to celebrate a block that just turned done. */
  previous: DayPlan | null;
  nextModuleId?: string | null;
  firstReviewId?: string | null;
  examLevel?: string | null;
  onAnki?: () => void;
};

export function blockRoute(block: BlockKey, p: Pick<Props, 'nextModuleId' | 'firstReviewId' | 'examLevel'>): string | null {
  switch (block) {
    case 'grammar':
      if (p.examLevel) return `/exam/${p.examLevel}`;
      if (p.nextModuleId) return `/lesson/${p.nextModuleId}`;
      return p.firstReviewId ? `/review/${p.firstReviewId}` : null;
    case 'music':
      return '/songs/today';
    case 'call1':
      return p.nextModuleId ? `/teach?kind=lesson&module=${p.nextModuleId}` : '/free';
    case 'call2':
      return '/teach';
    case 'watch':
    case 'read':
      return '/media';
    default:
      return null;
  }
}

export default function NextBlockCard({ plan, previous, onAnki, ...routes }: Props) {
  const theme = useTheme();
  if (plan.complete) {
    return (
      <View style={[styles.card, { backgroundColor: theme.pine }]}>
        <Text style={{ color: theme.sun, fontSize: 20, fontWeight: '800' }}>Dia completo! 🎉</Text>
        <Text style={{ color: theme.onPine, fontSize: 15 }}>Os 7 blocos estão feitos. Amanhã tem mais.</Text>
      </View>
    );
  }
  const current = plan.blocks.find((b) => b.key === plan.current);
  if (!current) return null;
  const justDone = previous?.blocks.some(
    (old) => old.status !== 'done' && plan.blocks.find((b) => b.key === old.key)?.status === 'done',
  );
  const route = blockRoute(current.key, routes);
  return (
    <View style={[styles.card, { backgroundColor: theme.pine }]}>
      <Text style={{ color: theme.onPine, fontSize: 20, fontWeight: '800' }}>
        {justDone ? `Boa! Agora: ${current.title}` : `Agora: ${current.title}`}
      </Text>
      {current.target ? (
        <Text style={{ color: theme.onPine, opacity: 0.8, fontSize: 14 }}>{`${current.minutes ?? 0} de ${current.target} min`}</Text>
      ) : null}
      <View style={{ alignSelf: 'flex-start', minWidth: 140 }}>
        <Button label="Ir" kind="sun" onPress={() => (current.key === 'anki' ? onAnki?.() : route && router.push(route))} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({ card: { borderRadius: 24, padding: 20, gap: 8 } });
