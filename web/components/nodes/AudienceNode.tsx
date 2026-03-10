'use client';

import { memo, useCallback, useEffect, useRef } from 'react';
import { Handle, Position, useReactFlow } from '@xyflow/react';
import type { AudienceData } from '@/lib/types';
import { getEligibleCount } from '@/lib/api';
import { useLocale } from '@/lib/locale-context';

function AudienceNodeInner({ id, data }: { id: string; data: AudienceData }) {
  const { updateNodeData } = useReactFlow();
  const { t } = useLocale();
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const update = useCallback(
    (key: keyof AudienceData, value: string | number) => {
      updateNodeData(id, { [key]: value });
    },
    [id, updateNodeData]
  );

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await getEligibleCount({
          age_min: data.ageMin,
          age_max: data.ageMax,
          gender: data.gender,
          housing: data.housing,
          income_min: data.incomeMin || undefined,
          income_max: data.incomeMax || undefined,
          marital: data.marital,
          education: data.education,
        });
        updateNodeData(id, {
          eligibleCount: res.eligible_count,
          totalPopulation: res.total_population,
          summary: res.summary,
        });
      } catch {
        // API not running
      }
    }, 600);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [data.ageMin, data.ageMax, data.gender, data.housing, data.incomeMin, data.incomeMax, data.marital, data.education, id, updateNodeData]);

  return (
    <div className="w-[320px] bg-[#111827] border border-[#1e293b] rounded-xl shadow-2xl overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 px-4 py-3 border-b border-[#1e293b]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center text-blue-400 text-sm font-bold">
            &#x1F465;
          </div>
          <div>
            <div className="text-xs font-bold text-blue-400 uppercase tracking-wider">{t('audiencePanelTitle')}</div>
            <div className="text-[10px] text-[#94a3b8]">{t('defineTarget')}</div>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-3 nodrag">
        <div className="flex gap-2">
          <div className="flex-1">
            <label className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wider">{t('ageMin')}</label>
            <input type="number" value={data.ageMin} onChange={(e) => update('ageMin', parseInt(e.target.value) || 0)}
              className="w-full mt-1 bg-[#0a0e1a] border border-[#1e293b] rounded-lg px-3 py-1.5 text-xs text-[#e2e8f0] outline-none focus:border-blue-500" />
          </div>
          <div className="flex-1">
            <label className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wider">{t('ageMax')}</label>
            <input type="number" value={data.ageMax} onChange={(e) => update('ageMax', parseInt(e.target.value) || 100)}
              className="w-full mt-1 bg-[#0a0e1a] border border-[#1e293b] rounded-lg px-3 py-1.5 text-xs text-[#e2e8f0] outline-none focus:border-blue-500" />
          </div>
        </div>

        <div>
          <label className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wider">{t('gender')}</label>
          <select value={data.gender} onChange={(e) => update('gender', e.target.value)}
            className="w-full mt-1 bg-[#0a0e1a] border border-[#1e293b] rounded-lg px-3 py-1.5 text-xs text-[#e2e8f0] outline-none focus:border-blue-500">
            <option value="all">{t('all')}</option>
            <option value="M">{t('male')}</option>
            <option value="F">{t('female')}</option>
          </select>
        </div>

        <div>
          <label className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wider">{t('housingType')}</label>
          <select value={data.housing} onChange={(e) => update('housing', e.target.value)}
            className="w-full mt-1 bg-[#0a0e1a] border border-[#1e293b] rounded-lg px-3 py-1.5 text-xs text-[#e2e8f0] outline-none focus:border-blue-500">
            <option value="all">{t('all')}</option>
            <option value="HDB_1_2_ROOM">{t('hdb12')}</option>
            <option value="HDB_3_ROOM">{t('hdb3')}</option>
            <option value="HDB_4_ROOM">{t('hdb4')}</option>
            <option value="HDB_5_ROOM">{t('hdb5')}</option>
            <option value="CONDO">{t('condo')}</option>
            <option value="LANDED">{t('landed')}</option>
          </select>
        </div>

        <div className="flex gap-2">
          <div className="flex-1">
            <label className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wider">{t('incomeMin')}</label>
            <input type="number" value={data.incomeMin || ''} placeholder="0" onChange={(e) => update('incomeMin', parseInt(e.target.value) || 0)}
              className="w-full mt-1 bg-[#0a0e1a] border border-[#1e293b] rounded-lg px-3 py-1.5 text-xs text-[#e2e8f0] outline-none focus:border-blue-500" />
          </div>
          <div className="flex-1">
            <label className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wider">{t('incomeMax')}</label>
            <input type="number" value={data.incomeMax || ''} placeholder="&infin;" onChange={(e) => update('incomeMax', parseInt(e.target.value) || 0)}
              className="w-full mt-1 bg-[#0a0e1a] border border-[#1e293b] rounded-lg px-3 py-1.5 text-xs text-[#e2e8f0] outline-none focus:border-blue-500" />
          </div>
        </div>

        <div>
          <label className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wider">{t('sampleSize')}</label>
          <input type="number" value={data.sampleSize} min={10} max={500}
            onChange={(e) => update('sampleSize', Math.min(500, Math.max(10, parseInt(e.target.value) || 30)))}
            className="w-full mt-1 bg-[#0a0e1a] border border-[#1e293b] rounded-lg px-3 py-1.5 text-xs text-[#e2e8f0] outline-none focus:border-blue-500" />
        </div>
      </div>

      <div className="px-4 py-2.5 bg-[#0a0e1a] border-t border-[#1e293b] flex items-center justify-between">
        <div className="text-[10px] text-[#94a3b8]">
          {t('eligible')}: <span className="text-blue-400 font-bold">{data.eligibleCount?.toLocaleString() ?? '—'}</span>
          <span className="text-[#475569]"> / {data.totalPopulation?.toLocaleString() ?? '—'}</span>
        </div>
        {data.summary?.age_mean && (
          <div className="text-[10px] text-[#94a3b8]">
            {t('avgAge')}: <span className="text-[#e2e8f0] font-medium">{data.summary.age_mean}</span>
            {data.summary.income_median ? (
              <span> &middot; S${Math.round(data.summary.income_median).toLocaleString()}/mo</span>
            ) : null}
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Right} className="!bg-blue-500 !border-blue-400" />
    </div>
  );
}

export const AudienceNode = memo(AudienceNodeInner);
