import { ReactNode } from 'react';
import {
  Pressable,
  ScrollView,
  StyleProp,
  StyleSheet,
  Text as RNText,
  TextProps,
  TextStyle,
  View,
  ViewStyle,
} from 'react-native';

import { fonts, useTheme } from '@/theme';

/**
 * Drop-in replacement for react-native's Text: maps fontWeight onto the matching
 * Bricolage Grotesque file (custom fonts need one family per weight on native).
 */
export function Text({ style, ...rest }: TextProps) {
  const flat = (StyleSheet.flatten(style) ?? {}) as TextStyle;
  const weight = String(flat.fontWeight ?? '400');
  const key = weight === 'bold' ? 700 : weight === 'normal' ? 400 : Number(weight);
  const family = fonts[(Math.min(800, Math.max(400, Math.round(key / 100) * 100)) as keyof typeof fonts) ?? 400];
  return <RNText {...rest} style={[style as StyleProp<TextStyle>, { fontFamily: family, fontWeight: undefined }]} />;
}

/** Scrolling page body, capped to a readable column so wide browser windows don't stretch everything. */
export function Screen({ children, gap = 12 }: { children: ReactNode; gap?: number }) {
  return (
    <ScrollView contentContainerStyle={[styles.screen, { gap }]} keyboardShouldPersistTaps="handled">
      {children}
    </ScrollView>
  );
}

export function Card({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) {
  const theme = useTheme();
  return (
    <View style={[styles.card, { backgroundColor: theme.card, borderColor: theme.border }, style]}>{children}</View>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  const theme = useTheme();
  return (
    <Text accessibilityRole="header" style={[styles.sectionTitle, { color: theme.text }]}>
      {children}
    </Text>
  );
}

export function Muted({ children }: { children: ReactNode }) {
  const theme = useTheme();
  return <Text style={{ color: theme.muted, fontSize: 15, lineHeight: 21 }}>{children}</Text>;
}

export function ErrorText({ children }: { children: ReactNode }) {
  const theme = useTheme();
  return <Text style={{ color: theme.bad, fontSize: 15, lineHeight: 21 }}>{children}</Text>;
}

export function Button({
  label,
  onPress,
  kind = 'primary',
  disabled,
}: {
  label: string;
  onPress: () => void;
  kind?: 'primary' | 'secondary' | 'sun';
  disabled?: boolean;
}) {
  const theme = useTheme();
  const palette = {
    primary: { bg: theme.primary, fg: theme.onPrimary, edge: 'rgba(0,0,0,0.28)' },
    sun: { bg: theme.sun, fg: theme.onSun, edge: 'rgba(120,70,0,0.35)' },
    secondary: { bg: theme.card, fg: theme.text, edge: theme.border },
  }[kind];
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      style={({ pressed }) => [
        styles.button,
        {
          backgroundColor: palette.bg,
          borderColor: kind === 'secondary' ? theme.border : palette.bg,
          borderBottomColor: palette.edge,
          borderBottomWidth: pressed ? 2 : 4,
          marginTop: pressed ? 2 : 0,
          marginBottom: pressed ? 2 : 0,
        },
        disabled && { opacity: 0.45 },
      ]}
    >
      <Text style={{ color: palette.fg, fontWeight: '700', fontSize: 16 }}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { padding: 16, paddingBottom: 40, width: '100%', maxWidth: 640, alignSelf: 'center' },
  card: { borderWidth: 1, borderRadius: 20, padding: 16, gap: 6 },
  sectionTitle: { fontSize: 22, fontWeight: '800', marginTop: 10, letterSpacing: -0.4 },
  button: { borderWidth: 1, borderRadius: 16, paddingVertical: 14, paddingHorizontal: 18, alignItems: 'center' },
});
