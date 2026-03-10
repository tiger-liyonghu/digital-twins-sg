'use client';

import { useState, useEffect } from 'react';
import type { IndustryOption } from '@/lib/sophie-types';
import type { Industry } from '@/lib/sophie-ontology';
import { getIndustries } from '@/lib/sophie-ontology';
import { useLocale } from '@/lib/locale-context';

export function IndustryCards({ onSelect, disabled }: { onSelect: (i: IndustryOption) => void; disabled?: boolean }) {
  const { locale } = useLocale();
  const zh = locale === 'zh';
  const [industries, setIndustries] = useState<Industry[]>([]);

  useEffect(() => {
    getIndustries().then(setIndustries).catch(console.error);
  }, []);

  if (disabled) return null;

  return (
    <div className="mt-4 grid grid-cols-2 gap-2">
      {industries.map((ind) => (
        <button
          key={ind.id}
          onClick={() => onSelect({ id: ind.id, name: ind.name, name_zh: ind.name_zh, icon: ind.icon, is_other: ind.is_other })}
          className={`text-left px-4 py-3 bg-[#0d1117] border border-[#1e293b] rounded-xl hover:border-blue-500/60 hover:bg-blue-500/5 transition-all group ${
            ind.is_other ? 'col-span-2' : ''
          }`}
        >
          <div className="flex items-center gap-2.5">
            <span className="text-xl">{ind.icon}</span>
            <span className="text-sm text-[#e2e8f0] group-hover:text-blue-300 font-medium">
              {zh ? ind.name_zh : ind.name}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}
