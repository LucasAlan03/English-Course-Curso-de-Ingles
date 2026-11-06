import { Platform, Share } from 'react-native';

/** Web: downloads a file. Phone: opens the share sheet with the text (save to Files, send by WhatsApp…). */
export async function saveText(filename: string, text: string, mime: string): Promise<void> {
  if (Platform.OS === 'web') {
    const url = URL.createObjectURL(new Blob([text], { type: `${mime};charset=utf-8` }));
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    return;
  }
  await Share.share({ message: text, title: filename });
}
