import { Link } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@/theme';

// Temporary entry screen; the Home tab replaces it in the next task.
export default function Index() {
  const theme = useTheme();
  return (
    <View style={styles.container}>
      <Text style={{ color: theme.text, fontSize: 20 }}>English</Text>
      <Link href="/voice-test" style={{ color: theme.primary }}>
        Testar microfone
      </Link>
    </View>
  );
}

const styles = StyleSheet.create({ container: { flex: 1, padding: 16, gap: 12 } });
