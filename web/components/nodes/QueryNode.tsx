'use client';

import { memo, useCallback } from 'react';
import { Handle, Position, useReactFlow } from '@xyflow/react';
import type { QueryData } from '@/lib/types';
import { SCENARIO_PRESETS } from '@/lib/types';
import { useLocale } from '@/lib/locale-context';

function QueryNodeInner({ id, data }: { id: string; data: QueryData }) {
  const { updateNodeData } = useReactFlow();
  const { t } = useLocale();

  const update = useCallback(
    (key: keyof QueryData, value: unknown) => {
      updateNodeData(id, { [key]: value });
    },
    [id, updateNodeData]
  );

  const loadPreset = useCallback(
    (presetId: string) => {
      const preset = SCENARIO_PRESETS.find((p) => p.id === presetId);
      if (!preset) return;
      updateNodeData(id, {
        presetId: preset.id,
        question: preset.question,
        options: preset.options,
        context: preset.context,
      });
    },
    [id, updateNodeData]
  );

  const updateOption = useCallback(
    (index: number, value: string) => {
      const newOptions = [...data.options];
      newOptions[index] = value;
      update('options', newOptions);
    },
    [data.options, update]
  );

  const addOption = useCallback(() => {
    update('options', [...data.options, '']);
  }, [data.options, update]);

  const removeOption = useCallback(
    (index: number) => {
      update('options', data.options.filter((_, i) => i !== index));
    },
    [data.options, update]
  );

  return (
    <div className="w-[380px] bg-[#111827] border border-[#1e293b] rounded-xl shadow-2xl overflow-hidden">
      <Handle type="target" position={Position.Left} className="!bg-purple-500 !border-purple-400" />

      <div className="bg-gradient-to-r from-purple-600/20 to-cyan-600/20 px-4 py-3 border-b border-[#1e293b]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400 text-sm font-bold">
            ?
          </div>
          <div>
            <div className="text-xs font-bold text-purple-400 uppercase tracking-wider">{t('surveyQueryTitle')}</div>
            <div className="text-[10px] text-[#94a3b8]">{t('defineQuestion')}</div>
          </div>
        </div>
      </div>

      <div className="px-4 pt-3 nodrag">
        <label className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wider">{t('quickLoadPreset')}</label>
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          {SCENARIO_PRESETS.map((p) => (
            <button
              key={p.id}
              onClick={() => loadPreset(p.id)}
              className={`text-[10px] px-2 py-1 rounded-md border transition-all ${
                data.presetId === p.id
                  ? 'border-purple-500 bg-purple-500/20 text-purple-300'
                  : 'border-[#1e293b] bg-[#0a0e1a] text-[#94a3b8] hover:border-purple-500/50'
              }`}
            >
              <span className="font-bold">{p.id}</span>
              <span className="ml-1 text-[#475569]">{p.name}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 space-y-3 nodrag">
        <div>
          <label className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wider">{t('question')}</label>
          <textarea
            value={data.question}
            onChange={(e) => update('question', e.target.value)}
            rows={3}
            className="w-full mt-1 bg-[#0a0e1a] border border-[#1e293b] rounded-lg px-3 py-2 text-xs text-[#e2e8f0] outline-none focus:border-purple-500 resize-none"
            placeholder={t('questionPlaceholder')}
          />
        </div>

        <div>
          <div className="flex items-center justify-between">
            <label className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wider">{t('options')}</label>
            <button onClick={addOption} className="text-[10px] text-purple-400 hover:text-purple-300 font-medium">
              {t('add')}
            </button>
          </div>
          <div className="mt-1.5 space-y-1.5">
            {data.options.map((opt, i) => (
              <div key={i} className="flex gap-1.5 items-center">
                <span className="text-[10px] text-[#475569] font-mono w-4 text-right flex-shrink-0">{i + 1}</span>
                <input
                  value={opt}
                  onChange={(e) => updateOption(i, e.target.value)}
                  className="flex-1 bg-[#0a0e1a] border border-[#1e293b] rounded-lg px-3 py-1.5 text-[11px] text-[#e2e8f0] outline-none focus:border-purple-500"
                />
                {data.options.length > 2 && (
                  <button onClick={() => removeOption(i)} className="text-[#475569] hover:text-red-400 text-xs">
                    &times;
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        <details className="group">
          <summary className="text-[10px] font-semibold text-[#94a3b8] uppercase tracking-wider cursor-pointer select-none hover:text-[#e2e8f0]">
            {t('contextInjection')} <span className="text-[#475569]">({data.context.length} {t('chars')})</span>
          </summary>
          <textarea
            value={data.context}
            onChange={(e) => update('context', e.target.value)}
            rows={5}
            className="w-full mt-1.5 bg-[#0a0e1a] border border-[#1e293b] rounded-lg px-3 py-2 text-[11px] text-[#e2e8f0] outline-none focus:border-purple-500 resize-y font-mono leading-relaxed"
            placeholder={t('contextPlaceholder')}
          />
        </details>
      </div>

      <Handle type="source" position={Position.Right} className="!bg-purple-500 !border-purple-400" />
    </div>
  );
}

export const QueryNode = memo(QueryNodeInner);
