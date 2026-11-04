import { Text } from 'react-native';

import { describeError } from '@/errors';
import { useTheme } from '@/theme';

export default function ErrorNotice({ error }: { error: unknown }) {
  const theme = useTheme();
  if (!error) return null;
  return (
    <Text testID="error-notice" style={{ color: theme.bad }}>
      {describeError(error)}
    </Text>
  );
}
