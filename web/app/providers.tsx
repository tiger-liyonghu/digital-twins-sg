'use client';

import { LocaleProvider } from '@/lib/locale-context';

export function Providers({ children }: { children: React.ReactNode }) {
  return <LocaleProvider>{children}</LocaleProvider>;
}
