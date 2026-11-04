import { Tabs } from 'expo-router';
import { ColorValue, View } from 'react-native';

import { fonts, useTheme } from '@/theme';

function Mark({ color, focused }: { color: ColorValue; focused: boolean }) {
  const theme = useTheme();
  return (
    <View
      style={{
        width: focused ? 26 : 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: focused ? theme.sun : color,
        opacity: focused ? 1 : 0.45,
      }}
    />
  );
}

export default function TabsLayout() {
  const theme = useTheme();
  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: theme.background },
        headerShadowVisible: false,
        headerTintColor: theme.text,
        headerTitleStyle: { fontFamily: fonts[800], fontSize: 22 },
        headerTitleAlign: 'left',
        sceneStyle: { backgroundColor: theme.background },
        tabBarStyle: { backgroundColor: theme.card, borderTopColor: theme.border, height: 68, paddingTop: 8 },
        tabBarActiveTintColor: theme.text,
        tabBarInactiveTintColor: theme.muted,
        tabBarIcon: ({ color, focused }) => <Mark color={color} focused={focused} />,
        tabBarLabelStyle: { fontSize: 13, marginBottom: 8, fontFamily: fonts[600] },
      }}
    >
      <Tabs.Screen name="index" options={{ title: 'Início', headerShown: false }} />
      <Tabs.Screen name="tracks" options={{ title: 'Trilha', headerShown: false }} />
      <Tabs.Screen name="media" options={{ title: 'Consumo' }} />
      <Tabs.Screen name="settings" options={{ title: 'Ajustes' }} />
    </Tabs>
  );
}
