import { View } from 'react-native';

import { useTheme } from '@/theme';

function Peak({ size, left, color }: { size: number; left: number; color: string }) {
  return (
    <View
      style={{
        position: 'absolute',
        bottom: 0,
        left,
        width: 0,
        height: 0,
        borderLeftWidth: size,
        borderRightWidth: size,
        borderBottomWidth: size * 1.25,
        borderLeftColor: 'transparent',
        borderRightColor: 'transparent',
        borderBottomColor: color,
      }}
    />
  );
}

/** Small decorative ridge line with a low sun, used on the pine surfaces. */
export default function Ridge({ width = 170, height = 90 }: { width?: number; height?: number }) {
  const theme = useTheme();
  return (
    <View pointerEvents="none" style={{ width, height, position: 'absolute', right: 0, bottom: 0, overflow: 'hidden' }}>
      <View
        style={{
          position: 'absolute',
          right: 26,
          top: 12,
          width: 30,
          height: 30,
          borderRadius: 15,
          backgroundColor: theme.sun,
        }}
      />
      <Peak size={58} left={width - 160} color={theme.pineSoft} />
      <Peak size={46} left={width - 70} color="#3a6f5c" />
      <Peak size={34} left={width - 122} color="#1f4d3f" />
    </View>
  );
}
