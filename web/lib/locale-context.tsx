'use client';

import { createContext, useContext, useState, type ReactNode } from 'react';
import type { Locale, TranslationKey } from './i18n';
import { t as translate } from './i18n';

interface LocaleContextType {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: TranslationKey) => string;
}

const LocaleContext = createContext<LocaleContextType>({
  locale: 'zh',
  setLocale: () => {},
  t: (key) => key,
});

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>('zh');
  const t = (key: TranslationKey) => translate(locale, key);

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  return useContext(LocaleContext);
}

export function LangSwitch() {
  const { locale, setLocale } = useLocale();
  return (
    <div className="flex gap-0.5 bg-[#0a0e1a] rounded-lg p-0.5">
      <button
        onClick={() => setLocale('en')}
        className={`px-2.5 py-1 rounded-md text-[10px] font-semibold transition-all ${
          locale === 'en'
            ? 'bg-blue-500 text-white'
            : 'text-[#475569] hover:text-[#94a3b8]'
        }`}
      >
        EN
      </button>
      <button
        onClick={() => setLocale('zh')}
        className={`px-2.5 py-1 rounded-md text-[10px] font-semibold transition-all ${
          locale === 'zh'
            ? 'bg-blue-500 text-white'
            : 'text-[#475569] hover:text-[#94a3b8]'
        }`}
      >
        中文
      </button>
    </div>
  );
}
