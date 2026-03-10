'use client';

import { useState } from 'react';
import type { AudienceConfig } from '@/lib/sophie-types';
import { SAMPLE_SIZE_OPTIONS } from '@/lib/sophie-types';
import { useLocale } from '@/lib/locale-context';

const FC = 'w-full bg-[#0d1117] border border-[#1e293b] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60';

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
  const [sampleSize, setSampleSize] = useState(20);
  const [showAudience, setShowAudience] = useState(false);
  const [launched, setLaunched] = useState(false);

  if (disabled || launched) {
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

  const doLaunch = () => {
    if (!canLaunch) return;
    setLaunched(true);
    onLaunch(question, options.filter(o => o.trim()), audience, sampleSize);
  };

  const estCost = (sampleSize * 0.0003).toFixed(2);
  const estTime = sampleSize <= 20 ? '<1' : Math.ceil(sampleSize * 0.12 / 60).toString();

  return (
    <div className="mt-3 bg-[#0d1117] border border-[#1e293b] rounded-2xl overflow-hidden">
      <div className="p-5 space-y-4">
        {/* Question */}
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

        {/* Audience */}
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
              <AudField label={zh ? '最小年龄' : 'Age Min'}>
                <input type="number" value={audience.ageMin} onChange={(e) => updateAud('ageMin', +e.target.value)}
                  className={FC} />
              </AudField>
              <AudField label={zh ? '最大年龄' : 'Age Max'}>
                <input type="number" value={audience.ageMax} onChange={(e) => updateAud('ageMax', +e.target.value)}
                  className={FC} />
              </AudField>
              <AudField label={zh ? '性别' : 'Gender'}>
                <select value={audience.gender} onChange={(e) => updateAud('gender', e.target.value)} className={FC}>
                  <option value="all">{zh ? '全部' : 'All'}</option>
                  <option value="M">{zh ? '男' : 'Male'}</option>
                  <option value="F">{zh ? '女' : 'Female'}</option>
                </select>
              </AudField>
              <AudField label={zh ? '种族' : 'Ethnicity'}>
                <select value={audience.ethnicity} onChange={(e) => updateAud('ethnicity', e.target.value)} className={FC}>
                  <option value="all">{zh ? '全部' : 'All'}</option>
                  <option value="Chinese">{zh ? '华族' : 'Chinese'}</option>
                  <option value="Malay">{zh ? '马来族' : 'Malay'}</option>
                  <option value="Indian">{zh ? '印度族' : 'Indian'}</option>
                  <option value="Others">{zh ? '其他' : 'Others'}</option>
                </select>
              </AudField>
              <AudField label={zh ? '住房类型' : 'Housing'}>
                <select value={audience.housing} onChange={(e) => updateAud('housing', e.target.value)} className={FC}>
                  <option value="all">{zh ? '全部' : 'All'}</option>
                  <option value="HDB_1_2_ROOM">HDB 1-2 Room</option>
                  <option value="HDB_3_ROOM">HDB 3 Room</option>
                  <option value="HDB_4_ROOM">HDB 4 Room</option>
                  <option value="HDB_5_ROOM">HDB 5 Room / Exec</option>
                  <option value="CONDO">Condo</option>
                  <option value="LANDED">Landed</option>
                </select>
              </AudField>
              <AudField label={zh ? '婚姻状况' : 'Marital'}>
                <select value={audience.marital} onChange={(e) => updateAud('marital', e.target.value)} className={FC}>
                  <option value="all">{zh ? '全部' : 'All'}</option>
                  <option value="Single">{zh ? '单身' : 'Single'}</option>
                  <option value="Married">{zh ? '已婚' : 'Married'}</option>
                  <option value="Divorced">{zh ? '离异' : 'Divorced'}</option>
                  <option value="Widowed">{zh ? '丧偶' : 'Widowed'}</option>
                </select>
              </AudField>
              <AudField label={zh ? '教育程度' : 'Education'}>
                <select value={audience.education} onChange={(e) => updateAud('education', e.target.value)} className={FC}>
                  <option value="all">{zh ? '全部' : 'All'}</option>
                  <option value="No_Formal">{zh ? '无正式学历' : 'No Formal'}</option>
                  <option value="Primary">{zh ? '小学' : 'Primary'}</option>
                  <option value="Secondary">{zh ? '中学' : 'Secondary'}</option>
                  <option value="Post_Secondary">{zh ? '大专' : 'Post Secondary'}</option>
                  <option value="Polytechnic">{zh ? '理工学院' : 'Polytechnic'}</option>
                  <option value="University">{zh ? '大学' : 'University'}</option>
                </select>
              </AudField>
              <AudField label={zh ? '收入下限' : 'Income Min'}>
                <select value={audience.incomeMin} onChange={(e) => updateAud('incomeMin', +e.target.value)} className={FC}>
                  <option value={0}>{zh ? '不限' : 'No min'}</option>
                  <option value={1000}>S$1,000</option>
                  <option value={3000}>S$3,000</option>
                  <option value={5000}>S$5,000</option>
                  <option value={7000}>S$7,000</option>
                  <option value={10000}>S$10,000</option>
                  <option value={15000}>S$15,000</option>
                </select>
              </AudField>
            </div>
          )}
        </div>

        {/* Sample size */}
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
        onClick={doLaunch}
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

function AudField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="text-xs text-[#64748b] font-medium mb-1 block">{label}</label>
      {children}
    </div>
  );
}
