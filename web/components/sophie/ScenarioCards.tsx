'use client';

import type { ScenarioConfig } from '@/lib/sophie-types';
import { SCENARIOS } from '@/lib/sophie-types';
import { useLocale } from '@/lib/locale-context';

export function ScenarioCards({ onSelect, disabled }: { onSelect: (s: ScenarioConfig) => void; disabled?: boolean }) {
  const { locale } = useLocale();
  const zh = locale === 'zh';

  if (disabled) return null;

  return (
    <div className="mt-4 space-y-3">
      {SCENARIOS.map((s) => (
        <button
          key={s.id}
          onClick={() => onSelect(s)}
          className="w-full text-left p-5 bg-[#0d1117] border border-[#1e293b] rounded-2xl hover:border-blue-500/60 hover:bg-blue-500/5 transition-all group"
        >
          <div className="flex items-start gap-4">
            <span className="text-3xl mt-1">{s.icon}</span>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-bold text-[#e2e8f0] group-hover:text-blue-300 mb-0.5">
                {zh ? s.nameZh : s.name}
              </div>
              <div className="text-[13px] text-blue-400/80 font-medium mb-2">
                {zh ? s.taglineZh : s.tagline}
              </div>
              <p className="text-[13px] text-[#94a3b8] leading-relaxed mb-2">
                {zh ? s.descriptionZh : s.description}
              </p>
              <div className="text-xs text-[#64748b]">
                <span className="font-semibold">{zh ? '例如：' : 'e.g. '}</span>
                {zh ? s.examplesZh : s.examples}
              </div>
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}
