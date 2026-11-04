
import { useTheme } from '@/theme';
import { UsageStatus } from '@/types';

import { Card, Text } from './ui';

export function brl(value: number): string {
  return `R$ ${value.toFixed(2).replace('.', ',')}`;
}

/** Only shows up when paid providers are close to, or at, the monthly cap. */
export default function UsageBanner({ usage }: { usage: UsageStatus }) {
  const theme = useTheme();
  if (usage.level === 'ok') return null;
  const blocked = usage.level === 'blocked';
  return (
    <Card style={{ borderColor: blocked ? theme.bad : theme.warn }}>
      <Text testID="usage-banner" style={{ color: blocked ? theme.bad : theme.warn, fontWeight: '600' }}>
        {blocked
          ? `Teto mensal atingido (${brl(usage.cap)}). Chamadas pagas estão bloqueadas.`
          : `Gasto no mês: ${brl(usage.total)} de ${brl(usage.cap)}`}
      </Text>
    </Card>
  );
}
