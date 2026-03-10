'use client';

import { useLocale } from '@/lib/locale-context';

export function ProgressBar({
  progress,
  total,
  isTest,
  interim,
}: {
  progress: number;
  total: number;
  isTest: boolean;
  interim?: Record<string, number>;
}) {
  const { locale } = useLocale();
  const zh = locale === 'zh';
  const pct = total > 0 ? Math.round((progress / total) * 100) : 0;
  const remaining = total > 0 ? Math.ceil((total - progress) * 0.12 / 60) : 0;

  return (
    <div className="mt-3 bg-[#0d1117] border border-[#1e293b] rounded-2xl p-5">
      <div className="flex justify-between mb-2">
        <span className="text-sm text-[#94a3b8] font-medium">
          {isTest ? (zh ? '试运行' : 'Test Run') : (zh ? '正式调研' : 'Full Survey')}
        </span>
        <span className="text-sm text-blue-400 font-mono">{progress}/{total} ({pct}%)</span>
      </div>
      <div className="w-full h-2.5 bg-[#111827] rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      {remaining > 0 && !isTest && (
        <div className="mt-2 text-sm text-[#64748b]">
          {zh ? `预计还需 ~${remaining} 分钟` : `~${remaining} min remaining`}
        </div>
      )}
      {interim && Object.keys(interim).length > 0 && (
        <div className="mt-3 space-y-1">
          <div className="text-xs text-[#64748b] uppercase tracking-wider font-semibold mb-1.5">
            {zh ? '中间结果' : 'Interim Results'}
          </div>
          {Object.entries(interim).slice(0, 6).map(([opt, cnt]) => (
            <div key={opt} className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-[#111827] rounded-full overflow-hidden">
                <div className="h-full bg-blue-500/60 rounded-full" style={{ width: `${progress > 0 ? (cnt / progress) * 100 : 0}%` }} />
              </div>
              <span className="text-xs text-[#94a3b8] w-10 text-right font-mono">{progress > 0 ? Math.round((cnt / progress) * 100) : 0}%</span>
              <span className="text-xs text-[#64748b] w-40 truncate">{opt}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
