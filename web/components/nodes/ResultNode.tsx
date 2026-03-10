'use client';

import { memo, useState } from 'react';
import { Handle, Position } from '@xyflow/react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie,
} from 'recharts';
import type { ResultData } from '@/lib/types';
import type { AgentLog } from '@/lib/api';
import { useLocale } from '@/lib/locale-context';

const COLORS = ['#3b82f6', '#a855f7', '#22c55e', '#f97316', '#ef4444', '#06b6d4', '#eab308', '#ec4899'];

function ResultNodeInner({ data }: { id: string; data: ResultData }) {
  const [tab, setTab] = useState<'distribution' | 'breakdown' | 'quotes'>('distribution');
  const { t } = useLocale();
  const result = data.result;
  const isRunning = data.status === 'running' || data.status === 'sampling' || data.status === 'queued';

  const distData = result
    ? Object.entries(result.overall.choice_distribution).map(([name, count]) => ({
        name: name.length > 40 ? name.slice(0, 37) + '...' : name,
        fullName: name,
        count,
        pct: Math.round((count / result.n_respondents) * 100),
      }))
    : [];

  const ageData = result
    ? Object.entries(result.breakdowns.by_age).map(([age, d]) => ({
        name: age,
        n: d.n,
        positive_rate: Math.round(d.positive_rate * 100),
      }))
    : [];

  return (
    <div className="w-[480px] bg-[#111827] border border-[#1e293b] rounded-xl shadow-2xl overflow-hidden">
      <Handle type="target" position={Position.Left} className="!bg-green-500 !border-green-400" />

      {/* Header */}
      <div className="bg-gradient-to-r from-green-600/20 to-cyan-600/20 px-4 py-3 border-b border-[#1e293b]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center text-green-400 text-sm font-bold">
              &#x1F4CA;
            </div>
            <div>
              <div className="text-xs font-bold text-green-400 uppercase tracking-wider">{t('results')}</div>
              <div className="text-[10px] text-[#94a3b8]">
                {data.status === 'done' && result
                  ? `${result.n_respondents} ${t('respondents')} · $${result.cost.total_cost_usd.toFixed(3)}`
                  : data.status === 'idle'
                  ? t('waitingForSimulation')
                  : data.status === 'error'
                  ? t('errorOccurred')
                  : `${data.status}...`}
              </div>
            </div>
          </div>
          {result?.quality?.available && (
            <div className="text-[10px] px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
              {result.quality.high_quality_pct}% {t('highQuality')}
            </div>
          )}
        </div>
      </div>

      {/* Progress */}
      {isRunning && (
        <div className="px-4 py-2 border-b border-[#1e293b]">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-[#94a3b8]">{data.status === 'queued' ? t('queued') : t('surveyingAgents')}</span>
            <span className="text-[10px] text-blue-400 font-mono">{data.progress ?? 0}/{data.total ?? '?'}</span>
          </div>
          <div className="w-full h-1.5 bg-[#0a0e1a] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-300"
              style={{ width: `${data.total ? ((data.progress ?? 0) / data.total) * 100 : 0}%` }}
            />
          </div>
        </div>
      )}

      {/* Error */}
      {data.status === 'error' && (
        <div className="px-4 py-3 bg-red-500/5 border-b border-red-500/20">
          <p className="text-xs text-red-400">{data.error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="nodrag">
          <div className="flex border-b border-[#1e293b]">
            {(['distribution', 'breakdown', 'quotes'] as const).map((tb) => (
              <button
                key={tb}
                onClick={() => setTab(tb)}
                className={`flex-1 py-2 text-[10px] font-semibold uppercase tracking-wider transition-all ${
                  tab === tb
                    ? 'text-green-400 border-b-2 border-green-400 bg-green-500/5'
                    : 'text-[#475569] hover:text-[#94a3b8]'
                }`}
              >
                {tb === 'distribution' ? t('distribution') : tb === 'breakdown' ? t('byAge') : t('quotes')}
              </button>
            ))}
          </div>

          <div className="p-4" style={{ minHeight: 200 }}>
            {tab === 'distribution' && (
              <div>
                <div className="mb-3 text-[11px] text-[#94a3b8]">
                  {t('population')}: {result.total_population?.toLocaleString()} &rarr; {t('eligibleLabel')}: {result.eligible_count?.toLocaleString()} &rarr; {t('sampled')}: {result.n_respondents}
                </div>
                <ResponsiveContainer width="100%" height={distData.length * 32 + 20}>
                  <BarChart data={distData} layout="vertical" margin={{ left: 10, right: 30 }}>
                    <XAxis type="number" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                    <YAxis type="category" dataKey="name" width={160} tick={{ fontSize: 9, fill: '#94a3b8' }} />
                    <Tooltip
                      contentStyle={{ background: '#111827', border: '1px solid #1e293b', borderRadius: 8, fontSize: 11 }}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      formatter={(value: any, _: any, props: any) => [`${value} (${props?.payload?.pct ?? 0}%)`, t('count')]}
                      labelFormatter={(label) => {
                        const item = distData.find((d) => d.name === label);
                        return item?.fullName || String(label);
                      }}
                    />
                    <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                      {distData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>

                <div className="mt-4 flex justify-center">
                  <PieChart width={200} height={140}>
                    <Pie data={distData} cx={100} cy={70} outerRadius={55} innerRadius={30} dataKey="count" stroke="#1e293b" strokeWidth={2}>
                      {distData.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: '#111827', border: '1px solid #1e293b', borderRadius: 8, fontSize: 10 }}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      formatter={(_value: any, _name: any, props: any) => [`${props?.payload?.pct ?? 0}%`, '']}
                    />
                  </PieChart>
                </div>
              </div>
            )}

            {tab === 'breakdown' && (
              <div>
                <div className="mb-2 text-[10px] text-[#94a3b8] uppercase tracking-wider">{t('positiveRateByAge')}</div>
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={ageData} margin={{ left: 0, right: 20 }}>
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                    <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} domain={[0, 100]} />
                    <Tooltip
                      contentStyle={{ background: '#111827', border: '1px solid #1e293b', borderRadius: 8, fontSize: 11 }}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      formatter={(value: any) => [`${value}%`, t('positiveRate')]}
                    />
                    <Bar dataKey="positive_rate" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>

                {Object.keys(result.breakdowns.by_income).length > 0 && (
                  <div className="mt-4">
                    <div className="mb-2 text-[10px] text-[#94a3b8] uppercase tracking-wider">{t('byIncome')}</div>
                    <div className="space-y-1">
                      {Object.entries(result.breakdowns.by_income).map(([label, d]) => (
                        <div key={label} className="flex items-center gap-2">
                          <span className="text-[10px] text-[#94a3b8] w-16">{label}</span>
                          <div className="flex-1 h-3 bg-[#0a0e1a] rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500 rounded-full" style={{ width: `${Math.round(d.positive_rate * 100)}%` }} />
                          </div>
                          <span className="text-[10px] text-[#e2e8f0] font-mono w-10 text-right">{Math.round(d.positive_rate * 100)}%</span>
                          <span className="text-[10px] text-[#475569] w-8 text-right">n={d.n}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {tab === 'quotes' && (
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {result.agent_log.slice(0, 20).map((agent: AgentLog, i: number) => (
                  <div key={i} className="p-2.5 bg-[#0a0e1a] rounded-lg border border-[#1e293b]">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-bold text-blue-400">
                        {agent.gender === 'M' ? '&#x2642;' : '&#x2640;'} {agent.age}yo
                      </span>
                      <span className="text-[10px] text-[#475569]">{agent.ethnicity}</span>
                      <span className="text-[10px] text-[#475569]">S${agent.income.toLocaleString()}/mo</span>
                      <span className="text-[10px] text-[#475569]">{agent.housing}</span>
                      {agent.reward !== null && (
                        <span className={`text-[9px] ml-auto px-1.5 py-0.5 rounded ${
                          agent.reward > -5 ? 'bg-green-500/10 text-green-400' :
                          agent.reward > -15 ? 'bg-yellow-500/10 text-yellow-400' :
                          'bg-red-500/10 text-red-400'
                        }`}>
                          {agent.reward.toFixed(1)}
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-[#e2e8f0]">
                      &rarr; <span className="font-medium text-purple-300">{agent.choice}</span>
                    </div>
                  </div>
                ))}
                {result.reasoning_samples.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-[#1e293b]">
                    <div className="text-[10px] text-[#94a3b8] uppercase tracking-wider mb-2">{t('sampleReasoning')}</div>
                    {result.reasoning_samples.map((r: string, i: number) => (
                      <div key={i} className="text-[11px] text-[#94a3b8] italic mb-2 pl-2 border-l-2 border-[#1e293b]">
                        &ldquo;{r}&rdquo;
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="px-4 py-2 bg-[#0a0e1a] border-t border-[#1e293b] flex items-center justify-between text-[10px] text-[#475569]">
            <span>{t('tokens')}: {result.cost.total_tokens.toLocaleString()}</span>
            <span>{t('cost')}: ${result.cost.total_cost_usd.toFixed(4)}</span>
            <span>{result.timestamp.split('.')[0]}</span>
          </div>
        </div>
      )}

      {data.status === 'idle' && (
        <div className="p-8 text-center">
          <div className="text-2xl mb-2 opacity-30">&#x1F4CA;</div>
          <p className="text-[11px] text-[#475569]">{t('connectNodes')}</p>
        </div>
      )}
    </div>
  );
}

export const ResultNode = memo(ResultNodeInner);
