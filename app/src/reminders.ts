import { Platform } from 'react-native';

import { DayPlan } from './types';

export type Reminder = { at: Date; body: string };

/** Today's reminders still ahead of `now`; none once the day is complete. */
export function remindersToSchedule(times: string[], now: Date, plan: DayPlan): Reminder[] {
  if (plan.complete) return [];
  const missing = plan.blocks.filter((b) => b.status !== 'done').map((b) => b.title);
  const body = `Faltam: ${missing.join(', ')}`;
  return times
    .map((t) => {
      const [h, m] = t.split(':').map(Number);
      return new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m);
    })
    .filter((at) => at > now)
    .map((at) => ({ at, body }));
}

let permissionAsked = false;

/** Android/iOS only: replace the scheduled local reminders with today's. The web has the in-app card only. */
export async function syncReminders(plan: DayPlan, times: string[]): Promise<void> {
  if (Platform.OS === 'web') return;
  const Notifications = await import('expo-notifications');
  await Notifications.cancelAllScheduledNotificationsAsync();
  const items = remindersToSchedule(times, new Date(), plan);
  if (!items.length) return;
  if (!permissionAsked) {
    permissionAsked = true;
    const { granted } = await Notifications.requestPermissionsAsync();
    if (!granted) return;
  }
  for (const item of items) {
    await Notifications.scheduleNotificationAsync({
      content: { title: 'Seu dia de inglês', body: item.body },
      trigger: { type: Notifications.SchedulableTriggerInputTypes.DATE, date: item.at },
    });
  }
}
