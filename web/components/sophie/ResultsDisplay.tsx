'use client';

import { useState } from 'react';
import { useLocale } from '@/lib/locale-context';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie,
} from 'recharts';
import type { SurveyResult, AgentLog } from '@/lib/api';

const COLORS = ['#3b82f6', '#a855f7', '#22c55e', '#f97316', '#ef4444', '#06b6d4', '#eab308', '#ec4899'];

export function ResultsDisplay({ result, isTest, onScaleUpN, onRerun }: {
  result: SurveyResult;
  isTest?: boolean;
  onScaleUpN?: (n: number) => void;
  onRerun?: () => void;
}) {
  const [tab, setTab] = useState<'dist' | 'age' | 'quotes'>('dist');
  const { locale } = useLocale();
  const zh = locale === 'zh';

  const distData = Object.entries(result.overall.choice_distribution).map(([name, count]) => ({
    name: name.length > 35 ? name.slice(0, 32) + '...' : name,
    fullName: name,
    count,
    pct: Math.round((count / result.n_respondents) * 100),
  })).sort((a, b) => b.count - a.count);

  const ageData = Object.entries(result.breakdowns.by_age).map(([age, d]) => ({
    name: age, n: d.n, positive_rate: Math.round(d.positive_rate * 100),
  }));

  return (
    <div className="mt-3 bg-[#0d1117] border border-[#1e293b] rounded-2xl overflow-hidden">
      {/* Summary */}
      <div className="px-5 py-3 border-b border-[#1e293b] flex justify-between items-center">
        <span className="text-sm text-[#94a3b8]">
          {result.n_respondents} {zh ? '受访者' : 'respondents'} &middot; ${result.cost.total_cost_usd.toFixed(3)}
        </span>
        {result.quality?.available && (
          <span className="text-xs px-2 py-1 rounded-lg bg-green-500/10 text-green-400 font-medium">
            {result.quality.high_quality_pct}% {zh ? '高质量' : 'high quality'}
          </span>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#1e293b]">
        {(['dist', 'age', 'quotes'] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex-1 py-2.5 text-sm font-semibold tracking-wide ${
              tab === t ? 'text-green-400 border-b-2 border-green-400 bg-green-500/5' : 'text-[#475569] hover:text-[#94a3b8]'
            }`}>
            {t === 'dist' ? (zh ? '分布' : 'Distribution') : t === 'age' ? (zh ? '按年龄' : 'By Age') : (zh ? '个体引用' : 'Quotes')}
          </button>
        ))}
      </div>

      <div className="p-5">
        {tab === 'dist' && (
          <div>
            <ResponsiveContainer width="100%" height={distData.length * 32 + 10}>
              <BarChart data={distData} layout="vertical" margin={{ left: 5, right: 30 }}>
                <XAxis type="number" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1e293b', borderRadius: 12, fontSize: 12 }}
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  formatter={(v: any, _: any, p: any) => [`${v} (${p?.payload?.pct ?? 0}%)`, '']} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {distData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-3 flex justify-center">
              <PieChart width={180} height={140}>
                <Pie data={distData} cx={90} cy={70} outerRadius={55} innerRadius={30} dataKey="count" stroke="#1e293b" strokeWidth={2}>
                  {distData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
              </PieChart>
            </div>
          </div>
        )}

        {tab === 'age' && ageData.length > 0 && (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={ageData} margin={{ left: 0, right: 20 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} domain={[0, 100]} />
              <Tooltip contentStyle={{ background: '#111827', border: '1px solid #1e293b', borderRadius: 12, fontSize: 12 }}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                formatter={(v: any) => [`${v}%`, '']} />
              <Bar dataKey="positive_rate" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}

        {tab === 'quotes' && (
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {result.agent_log.slice(0, 15).map((a: AgentLog, i: number) => (
              <div key={i} className="p-3 bg-[#111827] rounded-xl border border-[#1e293b]">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-bold text-blue-400">{a.gender === 'M' ? '♂' : '♀'} {a.age}yo</span>
                  <span className="text-xs text-[#64748b]">{a.ethnicity}</span>
                  <span className="text-xs text-[#64748b]">S${a.income.toLocaleString()}/mo</span>
                  {a.reward !== null && (
                    <span className={`text-[11px] ml-auto px-1.5 py-0.5 rounded-md ${
                      a.reward > -5 ? 'bg-green-500/10 text-green-400' : a.reward > -15 ? 'bg-yellow-500/10 text-yellow-400' : 'bg-red-500/10 text-red-400'
                    }`}>
                      {a.reward.toFixed(1)}
                    </span>
                  )}
                </div>
                <div className="text-sm text-[#e2e8f0]">&rarr; <span className="text-purple-300">{a.choice}</span></div>
              </div>
            ))}
            {result.reasoning_samples.length > 0 && (
              <div className="mt-3 pt-3 border-t border-[#1e293b]">
                <div className="text-xs text-[#94a3b8] uppercase font-semibold mb-2">{zh ? '推理示例' : 'Sample Reasoning'}</div>
                {result.reasoning_samples.slice(0, 3).map((r: string, i: number) => (
                  <p key={i} className="text-sm text-[#94a3b8] italic mb-2 pl-3 border-l-2 border-[#1e293b] leading-relaxed">&ldquo;{r}&rdquo;</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Scale up actions */}
      {isTest && (onScaleUpN || onRerun) && (
        <div className="px-5 pb-5 space-y-3">
          {onScaleUpN && (
            <div>
              <div className="text-xs text-[#64748b] mb-2">{zh ? '扩大规模' : 'Scale up to'}:</div>
              <div className="flex gap-2 flex-wrap">
                {[1000, 2000, 5000, 20000].map((n) => (
                  <button
                    key={n}
                    onClick={() => onScaleUpN(n)}
                    className="px-4 py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-sm font-bold rounded-xl hover:shadow-lg hover:shadow-blue-500/25 transition-all"
                  >
                    {n.toLocaleString()} {zh ? '人' : ''}
                  </button>
                ))}
              </div>
            </div>
          )}
          {onRerun && (
            <button
              onClick={onRerun}
              className="px-5 py-3 bg-[#111827] border border-[#1e293b] text-[#94a3b8] text-sm font-medium rounded-xl hover:text-[#e2e8f0] transition-all"
            >
              {zh ? '改改再跑' : 'Edit & Rerun'}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
