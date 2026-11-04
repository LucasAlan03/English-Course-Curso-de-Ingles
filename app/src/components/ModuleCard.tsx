import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@/theme';
import { ModuleSummary } from '@/types';

import { Card } from './ui';

export default function ModuleCard({
  module,
  suggested,
  onPress,
}: {
  module: ModuleSummary;
  suggested: boolean;
  onPress: () => void;
}) {
  const theme = useTheme();
  const badge = module.completed ? 'Concluído' : suggested ? 'Próximo' : '';
  return (
    <Pressable testID={`module-${module.id}`} onPress={onPress}>
      <Card style={suggested ? { borderColor: theme.primary } : undefined}>
        <View style={styles.row}>
          <Text style={{ color: theme.text, fontWeight: '600', fontSize: 16, flex: 1 }}>{module.title}</Text>
          {badge ? (
            <Text style={{ color: module.completed ? theme.good : theme.primary, fontWeight: '600' }}>{badge}</Text>
          ) : null}
        </View>
      </Card>
    </Pressable>
  );
}

const styles = StyleSheet.create({ row: { flexDirection: 'row', alignItems: 'center', gap: 8 } });
