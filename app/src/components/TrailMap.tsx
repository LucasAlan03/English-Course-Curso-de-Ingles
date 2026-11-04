import { useEffect, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, LayoutChangeEvent, Pressable, StyleSheet, View } from 'react-native';

import { useTheme } from '@/theme';
import { LevelSummary, ModuleSummary } from '@/types';

import Ridge from './Ridge';
import { Text } from './ui';

const ROW = 96;
const NODE = 58;
const NODE_NEXT = 70;

const REGION: Record<string, string> = { A1: 'No vale', A2: 'Na trilha', B1: 'Na mata', B2: 'Na serra', C1: 'No cume' };

/** The one looping motion in the app: a slow halo on "you are here". */
function Halo({ size }: { size: number }) {
  const theme = useTheme();
  const pulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    let loop: Animated.CompositeAnimation | undefined;
    let cancelled = false;
    AccessibilityInfo.isReduceMotionEnabled?.()
      .then((reduce) => {
        if (cancelled || reduce) return;
        loop = Animated.loop(Animated.timing(pulse, { toValue: 1, duration: 1800, useNativeDriver: true }));
        loop.start();
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
      loop?.stop();
    };
  }, [pulse]);
  return (
    <Animated.View
      pointerEvents="none"
      style={{
        position: 'absolute',
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: theme.sun,
        opacity: pulse.interpolate({ inputRange: [0, 1], outputRange: [0.35, 0] }),
        transform: [{ scale: pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.55] }) }],
      }}
    />
  );
}

function Node({ module, suggested }: { module: ModuleSummary; suggested: boolean }) {
  const theme = useTheme();
  const size = suggested ? NODE_NEXT : NODE;
  const filled = module.completed || suggested;
  const bg = module.completed ? theme.pine : suggested ? theme.sun : theme.card;
  const fg = module.completed ? theme.onPine : suggested ? theme.onSun : theme.muted;
  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      {suggested ? <Halo size={size} /> : null}
      <View
        style={{
          width: size,
          height: size,
          borderRadius: size / 2,
          backgroundColor: bg,
          borderWidth: filled ? 0 : 2,
          borderColor: theme.border,
          borderBottomWidth: filled ? 5 : 4,
          borderBottomColor: module.completed ? '#0a211a' : suggested ? '#b97f0c' : theme.border,
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Text style={{ color: fg, fontWeight: '800', fontSize: suggested ? 24 : 20 }}>
          {module.completed ? '✓' : module.order}
        </Text>
      </View>
    </View>
  );
}

function Level({
  level,
  suggestedId,
  onOpen,
  width,
}: {
  level: LevelSummary;
  suggestedId?: string;
  onOpen: (id: string) => void;
  width: number;
}) {
  const theme = useTheme();
  const amp = Math.min(width * 0.24, 96);
  const xs = level.modules.map((_, i) => width / 2 + Math.sin(i * 1.15) * amp);
  const dots: { x: number; y: number; done: boolean }[] = [];
  level.modules.forEach((m, i) => {
    if (i === level.modules.length - 1) return;
    for (let t = 0.36; t <= 0.64; t += 0.07) {
      dots.push({
        x: xs[i] + (xs[i + 1] - xs[i]) * t,
        y: i * ROW + ROW / 2 + ROW * t,
        done: m.completed,
      });
    }
  });
  const pct = level.total ? level.completed / level.total : 0;

  return (
    <View style={{ gap: 10 }}>
      <View style={[styles.banner, { backgroundColor: theme.pine }]}>
        <Ridge />
        <Text style={{ color: theme.sun, fontSize: 44, fontWeight: '800', letterSpacing: -1.5, lineHeight: 48 }}>
          {level.level}
        </Text>
        <Text style={{ color: theme.onPine, fontSize: 16, fontWeight: '600' }}>{REGION[level.level] ?? 'Na trilha'}</Text>
        <View style={styles.progressRow}>
          <View style={[styles.track, { backgroundColor: theme.pineSoft }]}>
            <View style={{ width: `${pct * 100}%`, height: '100%', backgroundColor: theme.sun, borderRadius: 4 }} />
          </View>
          <Text style={{ color: theme.onPine, fontWeight: '600', fontSize: 14 }}>{`${level.completed}/${level.total}`}</Text>
        </View>
      </View>

      <View style={{ height: level.modules.length * ROW, width }}>
        {dots.map((d, i) => (
          <View
            key={i}
            pointerEvents="none"
            style={{
              position: 'absolute',
              left: d.x - 4,
              top: d.y - 4,
              width: 8,
              height: 8,
              borderRadius: 4,
              backgroundColor: d.done ? theme.pine : theme.border,
            }}
          />
        ))}
        {level.modules.map((module, i) => {
          const suggested = module.id === suggestedId;
          const size = suggested ? NODE_NEXT : NODE;
          const left = xs[i] - size / 2;
          const labelOnRight = xs[i] < width / 2;
          const label = (
            <View style={[styles.label, labelOnRight ? { marginLeft: 12 } : { marginRight: 12, alignItems: 'flex-end' }]}>
              <Text
                numberOfLines={3}
                style={{
                  color: theme.text,
                  fontWeight: suggested ? '800' : '600',
                  fontSize: 16,
                  lineHeight: 21,
                  textAlign: labelOnRight ? 'left' : 'right',
                }}
              >
                {module.title}
              </Text>
              {module.completed || suggested ? (
                <View style={[styles.badge, { backgroundColor: module.completed ? theme.tint : theme.sun }]}>
                  <Text style={{ color: module.completed ? theme.good : theme.onSun, fontWeight: '700', fontSize: 12 }}>
                    {module.completed ? 'Concluído' : 'Próximo'}
                  </Text>
                </View>
              ) : null}
            </View>
          );
          return (
            <Pressable
              key={module.id}
              testID={`module-${module.id}`}
              accessibilityRole="button"
              onPress={() => onOpen(module.id)}
              style={[styles.row, { top: i * ROW, width }]}
            >
              {labelOnRight ? (
                <>
                  <View style={{ width: left }} />
                  <Node module={module} suggested={suggested} />
                  {label}
                </>
              ) : (
                <>
                  <View style={{ width: left, alignItems: 'flex-end' }}>{label}</View>
                  <Node module={module} suggested={suggested} />
                </>
              )}
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

export default function TrailMap({
  levels,
  suggestedId,
  onOpen,
}: {
  levels: LevelSummary[];
  suggestedId?: string;
  onOpen: (id: string) => void;
}) {
  const [width, setWidth] = useState(0);
  const onLayout = (e: LayoutChangeEvent) => setWidth(Math.floor(e.nativeEvent.layout.width));
  return (
    <View onLayout={onLayout} style={{ gap: 28 }}>
      {levels.map((level) => (
        <Level key={level.level} level={level} suggestedId={suggestedId} onOpen={onOpen} width={width || 340} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  banner: { borderRadius: 24, padding: 18, gap: 2, overflow: 'hidden' },
  progressRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 10, width: '55%' },
  track: { flex: 1, height: 8, borderRadius: 4, overflow: 'hidden' },
  row: { position: 'absolute', left: 0, height: ROW, flexDirection: 'row', alignItems: 'center' },
  label: { flex: 1, gap: 6 },
  badge: { alignSelf: 'flex-start', borderRadius: 999, paddingVertical: 2, paddingHorizontal: 10 },
});
