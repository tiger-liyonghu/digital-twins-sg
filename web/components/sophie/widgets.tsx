'use client';

import { useState, useEffect } from 'react';
import type { ScenarioConfig, AudienceConfig, IndustryOption } from '@/lib/sophie-types';
import { SCENARIOS, SAMPLE_SIZE_OPTIONS } from '@/lib/sophie-types';
import type { Industry } from '@/lib/sophie-ontology';
import { getIndustries } from '@/lib/sophie-ontology';
import { useLocale } from '@/lib/locale-context';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie,
} from 'recharts';
import type { SurveyResult, AgentLog } from '@/lib/api';

const COLORS = ['#3b82f6', '#a855f7', '#22c55e', '#f97316', '#ef4444', '#06b6d4', '#eab308', '#ec4899'];

// ─── Scenario Cards ───────────────────────────────
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

// ─── Industry Cards (loaded from Supabase) ──────────────────────────────
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

// ─── Survey Config Card (all-in-one: question + options + audience + sample size) ──
export function SurveyConfigCard({
  question: initialQuestion,
  options: initialOptions,
  audience: initialAudience,
  onLaunch,
  disabled,
}: {
  question: string;
  options: string[];
  audience: AudienceConfig;
  onLaunch: (question: string, options: string[], audience: AudienceConfig, sampleSize: number) => void;
  disabled?: boolean;
}) {
  const { locale } = useLocale();
  const zh = locale === 'zh';

  const [question, setQuestion] = useState(initialQuestion);
  const [options, setOptions] = useState(initialOptions);
  const [audience, setAudience] = useState<AudienceConfig>(initialAudience);
  const [sampleSize, setSampleSize] = useState(20); // default to test run
  const [showAudience, setShowAudience] = useState(false);
  const [launched, setLaunched] = useState(false);

  if (disabled || launched) {
    // Show readonly summary after launch
    return (
      <div className="mt-3 bg-[#0d1117] border border-[#1e293b]/60 rounded-2xl p-5 text-sm text-[#64748b]">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-green-400">&#10003;</span>
          <span className="text-[#94a3b8] font-medium">{zh ? '调研已启动' : 'Survey launched'}</span>
        </div>
        <div className="text-[13px] text-[#475569] line-clamp-1">{question}</div>
      </div>
    );
  }

  const updateOpt = (i: number, v: string) => {
    const o = [...options]; o[i] = v; setOptions(o);
  };
  const addOpt = () => setOptions([...options, '']);
  const removeOpt = (i: number) => setOptions(options.filter((_, j) => j !== i));
  const updateAud = (key: keyof AudienceConfig, val: string | number) =>
    setAudience((a) => ({ ...a, [key]: val }));

  const canLaunch = question.trim() && options.filter(o => o.trim()).length >= 2;

  const handleLaunch = () => {
    if (!canLaunch) return;
    setLaunched(true);
    onLaunch(question, options.filter(o => o.trim()), audience, sampleSize);
  };

  const estCost = (sampleSize * 0.0003).toFixed(2);
  const estTime = sampleSize <= 20 ? '<1' : Math.ceil(sampleSize * 0.12 / 60).toString();

  return (
    <div className="mt-3 bg-[#0d1117] border border-[#1e293b] rounded-2xl overflow-hidden">
      {/* Question */}
      <div className="p-5 space-y-4">
        <div>
          <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-1.5 block">
            {zh ? '调研问题' : 'Survey Question'}
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
            className="w-full bg-[#111827] border border-[#1e293b] rounded-xl px-4 py-3 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60 resize-none leading-relaxed"
          />
        </div>

        {/* Options */}
        <div>
          <div className="flex justify-between items-center mb-1.5">
            <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider">
              {zh ? '选项' : 'Options'}
            </label>
            <button onClick={addOpt} className="text-xs text-blue-400 hover:text-blue-300 font-medium">
              + {zh ? '添加' : 'Add'}
            </button>
          </div>
          <div className="space-y-1.5">
            {options.map((opt, i) => (
              <div key={i} className="flex gap-2 items-center">
                <span className="text-xs text-[#475569] w-5 text-right font-mono">{i + 1}</span>
                <input
                  value={opt}
                  onChange={(e) => updateOpt(i, e.target.value)}
                  className="flex-1 bg-[#111827] border border-[#1e293b] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60"
                />
                {options.length > 2 && (
                  <button onClick={() => removeOpt(i)} className="text-[#475569] hover:text-red-400 text-sm px-1">&times;</button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Audience chip + expandable */}
        <div>
          <button
            onClick={() => setShowAudience(!showAudience)}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#111827] border border-[#1e293b] text-xs text-[#94a3b8] hover:border-blue-500/40 transition-all"
          >
            <span>{zh ? '受众' : 'Audience'}:</span>
            <span className="text-[#e2e8f0]">
              {audience.ageMin}-{audience.ageMax}{zh ? '岁' : 'yo'}
              {audience.gender !== 'all' && `, ${audience.gender === 'M' ? (zh ? '男' : 'Male') : (zh ? '女' : 'Female')}`}
              {audience.ethnicity !== 'all' && `, ${audience.ethnicity}`}
              {audience.housing !== 'all' && `, ${audience.housing}`}
              {audience.marital !== 'all' && `, ${audience.marital}`}
              {audience.education !== 'all' && `, ${audience.education}`}
            </span>
            <span className="text-[10px]">{showAudience ? '▲' : '▼'}</span>
          </button>

          {showAudience && (
            <div className="mt-2 bg-[#111827] border border-[#1e293b] rounded-xl p-4 grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-[#64748b] font-medium mb-1 block">{zh ? '最小年龄' : 'Age Min'}</label>
                <input type="number" value={audience.ageMin} onChange={(e) => updateAud('ageMin', +e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#1e293b] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60" />
              </div>
              <div>
                <label className="text-xs text-[#64748b] font-medium mb-1 block">{zh ? '最大年龄' : 'Age Max'}</label>
                <input type="number" value={audience.ageMax} onChange={(e) => updateAud('ageMax', +e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#1e293b] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60" />
              </div>
              <div>
                <label className="text-xs text-[#64748b] font-medium mb-1 block">{zh ? '性别' : 'Gender'}</label>
                <select value={audience.gender} onChange={(e) => updateAud('gender', e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#1e293b] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60">
                  <option value="all">{zh ? '全部' : 'All'}</option>
                  <option value="M">{zh ? '男' : 'Male'}</option>
                  <option value="F">{zh ? '女' : 'Female'}</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-[#64748b] font-medium mb-1 block">{zh ? '种族' : 'Ethnicity'}</label>
                <select value={audience.ethnicity} onChange={(e) => updateAud('ethnicity', e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#1e293b] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60">
                  <option value="all">{zh ? '全部' : 'All'}</option>
                  <option value="Chinese">{zh ? '华族' : 'Chinese'}</option>
                  <option value="Malay">{zh ? '马来族' : 'Malay'}</option>
                  <option value="Indian">{zh ? '印度族' : 'Indian'}</option>
                  <option value="Others">{zh ? '其他' : 'Others'}</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-[#64748b] font-medium mb-1 block">{zh ? '住房类型' : 'Housing'}</label>
                <select value={audience.housing} onChange={(e) => updateAud('housing', e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#1e293b] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60">
                  <option value="all">{zh ? '全部' : 'All'}</option>
                  <option value="HDB_1_2_ROOM">HDB 1-2 Room</option>
                  <option value="HDB_3_ROOM">HDB 3 Room</option>
                  <option value="HDB_4_ROOM">HDB 4 Room</option>
                  <option value="HDB_5_ROOM">HDB 5 Room / Exec</option>
                  <option value="CONDO">Condo</option>
                  <option value="LANDED">Landed</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-[#64748b] font-medium mb-1 block">{zh ? '婚姻状况' : 'Marital'}</label>
                <select value={audience.marital} onChange={(e) => updateAud('marital', e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#1e293b] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60">
                  <option value="all">{zh ? '全部' : 'All'}</option>
                  <option value="Single">{zh ? '单身' : 'Single'}</option>
                  <option value="Married">{zh ? '已婚' : 'Married'}</option>
                  <option value="Divorced">{zh ? '离异' : 'Divorced'}</option>
                  <option value="Widowed">{zh ? '丧偶' : 'Widowed'}</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-[#64748b] font-medium mb-1 block">{zh ? '教育程度' : 'Education'}</label>
                <select value={audience.education} onChange={(e) => updateAud('education', e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#1e293b] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60">
                  <option value="all">{zh ? '全部' : 'All'}</option>
                  <option value="No_Formal">{zh ? '无正式学历' : 'No Formal'}</option>
                  <option value="Primary">{zh ? '小学' : 'Primary'}</option>
                  <option value="Secondary">{zh ? '中学' : 'Secondary'}</option>
                  <option value="Post_Secondary">{zh ? '大专' : 'Post Secondary'}</option>
                  <option value="Polytechnic">{zh ? '理工学院' : 'Polytechnic'}</option>
                  <option value="University">{zh ? '大学' : 'University'}</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-[#64748b] font-medium mb-1 block">{zh ? '收入下限' : 'Income Min'}</label>
                <select value={audience.incomeMin} onChange={(e) => updateAud('incomeMin', +e.target.value)}
                  className="w-full bg-[#0d1117] border border-[#1e293b] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60">
                  <option value={0}>{zh ? '不限' : 'No min'}</option>
                  <option value={1000}>S$1,000</option>
                  <option value={3000}>S$3,000</option>
                  <option value={5000}>S$5,000</option>
                  <option value={7000}>S$7,000</option>
                  <option value={10000}>S$10,000</option>
                  <option value={15000}>S$15,000</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Sample size + launch */}
        <div>
          <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-2 block">
            {zh ? '样本量' : 'Sample Size'}
          </label>
          <div className="flex flex-wrap gap-2 mb-4">
            {SAMPLE_SIZE_OPTIONS.map((n) => (
              <button
                key={n}
                onClick={() => setSampleSize(n)}
                className={`px-4 py-2 rounded-xl text-sm font-medium border transition-all ${
                  n === sampleSize
                    ? 'border-blue-500 bg-blue-500/20 text-blue-300'
                    : 'border-[#1e293b] bg-[#111827] text-[#94a3b8] hover:border-blue-500/40'
                }`}
              >
                {n === 172000 ? (zh ? '全部 172K' : 'All 172K') : n.toLocaleString()}
                {n === 20 && <span className="ml-1.5 text-xs text-blue-400/70">{zh ? '试跑' : 'test'}</span>}
              </button>
            ))}
          </div>

          <div className="flex items-center justify-between text-xs text-[#64748b] mb-4">
            <span>{zh ? '预估费用' : 'Est. cost'}: <span className="text-green-400">${estCost}</span></span>
            <span>{zh ? '预估时间' : 'Est. time'}: ~{estTime} min</span>
          </div>
        </div>
      </div>

      {/* Launch button */}
      <button
        onClick={handleLaunch}
        disabled={!canLaunch}
        className="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-base font-bold hover:shadow-lg hover:shadow-blue-500/25 transition-all disabled:opacity-30"
      >
        {sampleSize <= 20
          ? (zh ? `试跑 ${sampleSize} 个居民` : `Test Run — ${sampleSize} Citizens`)
          : (zh ? `启动调研 — ${sampleSize.toLocaleString()} 个居民` : `Launch Survey — ${sampleSize.toLocaleString()} Citizens`)}
      </button>
    </div>
  );
}

// ─── Progress Bar ──────────────────────────────────
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

// ─── Results Display ───────────────────────────────
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
      {/* Summary bar */}
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

      {/* Action buttons for test results */}
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
