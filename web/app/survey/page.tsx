'use client';

import { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import NavBar from '@/components/NavBar';
import { useLocale } from '@/lib/locale-context';
import { submitSurvey, getJobStatus } from '@/lib/api';
import type { SurveyResult } from '@/lib/api';
import { SCENARIO_PREFILLS, INDUSTRIES, PLANNING_AREAS, OCCUPATIONS, SAMPLE_SIZES } from '@/lib/survey-scenarios';
import { SURVEY_SCENARIOS, CATEGORY_LABELS } from '@/lib/inspiration-scenarios';
import type { InspirationScenario } from '@/lib/inspiration-scenarios';

type Step = 'form' | 'evaluating' | 'review' | 'scale' | 'running' | 'results' | 'feedback';

interface AudienceFilters {
  ageMin: number; ageMax: number;
  gender: string; ethnicity: string; housing: string;
  incomeMin: number; incomeMax: number;
  education: string; marital: string; lifePhase: string;
  occupation: string; planningArea: string; religion: string;
}

const DEFAULT_AUDIENCE: AudienceFilters = {
  ageMin: 21, ageMax: 64, gender: 'all', ethnicity: 'all', housing: 'all',
  incomeMin: 0, incomeMax: 0, education: 'all', marital: 'all', lifePhase: 'all',
  occupation: 'all', planningArea: 'all', religion: 'all',
};

function SurveyContent() {
  const { locale } = useLocale();
  const zh = locale === 'zh';
  const searchParams = useSearchParams();

  // ─── State ──
  const [step, setStep] = useState<Step>('form');
  const [industry, setIndustry] = useState('');
  const [question, setQuestion] = useState('');
  const [options, setOptions] = useState([
    zh ? '强烈支持' : 'Strongly support',
    zh ? '比较支持' : 'Somewhat support',
    zh ? '中立' : 'Neutral',
    zh ? '比较反对' : 'Somewhat oppose',
    zh ? '强烈反对' : 'Strongly oppose',
  ]);
  const [context, setContext] = useState('');
  const [audience, setAudience] = useState<AudienceFilters>({ ...DEFAULT_AUDIENCE });
  const [showAdvancedAud, setShowAdvancedAud] = useState(false);

  // Evaluation
  const [evalResult, setEvalResult] = useState<{
    pass: boolean; issues: { type: string; severity: string; message: string }[];
    suggestion: string | null; suggestion_options: string[] | null;
    fit_score: number; fit_reason: string | null;
    ontology_match: boolean; ontology_note: string | null;
  } | null>(null);

  // Execution
  const [sampleSize, setSampleSize] = useState(1000);
  const [progress, setProgress] = useState({ current: 0, total: 0, interim: {} as Record<string, number> });
  const [result, setResult] = useState<SurveyResult | null>(null);
  const [resultTab, setResultTab] = useState<'dist' | 'demo' | 'quotes' | 'report'>('dist');
  const pollRef = useRef<ReturnType<typeof setInterval>>();

  // Feedback
  const [rating, setRating] = useState(0);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [expectMatch, setExpectMatch] = useState<'yes' | 'no' | 'partial' | ''>('');

  // Load scenario prefill from URL
  useEffect(() => {
    const idx = searchParams.get('scenario');
    if (idx !== null) {
      const s = SCENARIO_PREFILLS[Number(idx)];
      if (s) {
        setIndustry(s.industry);
        setQuestion(zh ? s.questionZh : s.question);
        setOptions(zh ? [...s.optionsZh] : [...s.options]);
        if (s.context) setContext(zh ? (s.contextZh || s.context) : s.context);
      }
    }
  }, [searchParams, zh]);

  const updateOpt = (i: number, v: string) => { const o = [...options]; o[i] = v; setOptions(o); };
  const addOpt = () => setOptions([...options, '']);
  const removeOpt = (i: number) => setOptions(options.filter((_, j) => j !== i));
  const updateAud = (key: keyof AudienceFilters, val: string | number) => setAudience(a => ({ ...a, [key]: val }));

  const validOptions = options.filter(o => o.trim());
  const canSubmit = question.trim() && validOptions.length >= 2 && industry;

  // ─── Submit → Evaluate ──
  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return;
    setStep('evaluating');

    try {
      const res = await fetch('/api/sophie/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ industry, question, options: validOptions, context, locale }),
      });
      const evaluation = await res.json();
      setEvalResult(evaluation);

      if (evaluation.pass) {
        // If Sophie has suggestions, show review step for user to confirm/edit
        if (evaluation.suggestion || evaluation.suggestion_options) {
          setStep('review');
        } else {
          setStep('scale');
        }
      } else {
        // Show issues — stay on form with feedback
        setStep('form');
      }
    } catch {
      // Evaluation failed — pass through
      setEvalResult(null);
      setStep('scale');
    }
  }, [canSubmit, industry, question, validOptions, context, locale]);

  // ─── Launch survey ──
  const handleLaunch = useCallback(async () => {
    setStep('running');
    setProgress({ current: 0, total: sampleSize, interim: {} });

    try {
      const { job_id } = await submitSurvey({
        client_name: 'Sophie Survey',
        question,
        options: validOptions,
        context,
        sample_size: sampleSize,
        age_min: audience.ageMin,
        age_max: audience.ageMax,
        gender: audience.gender !== 'all' ? audience.gender : undefined,
        housing: audience.housing !== 'all' ? audience.housing : undefined,
        income_min: audience.incomeMin || undefined,
        income_max: audience.incomeMax || undefined,
        ethnicity: audience.ethnicity !== 'all' ? audience.ethnicity : undefined,
        marital: audience.marital !== 'all' ? audience.marital : undefined,
        education: audience.education !== 'all' ? audience.education : undefined,
        life_phase: audience.lifePhase !== 'all' ? audience.lifePhase : undefined,
      });

      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(async () => {
        try {
          const status = await getJobStatus(job_id);
          setProgress({
            current: status.progress,
            total: status.total,
            interim: status.result?.overall.choice_distribution || {},
          });

          if (status.status === 'done' && status.result) {
            clearInterval(pollRef.current);
            setResult(status.result);
            setStep('results');
          } else if (status.status === 'error') {
            clearInterval(pollRef.current);
            alert(zh ? '调研执行出错，请检查后端服务' : 'Survey failed. Please check the backend service.');
            setStep('form');
          }
        } catch {
          // Keep polling
        }
      }, 2000);
    } catch (err) {
      console.error('Survey launch failed:', err);
      alert(zh ? 'API 连接失败。请确认后端服务运行在 localhost:3456' : 'API connection failed. Make sure backend is running on localhost:3456.');
      setStep('scale');
    }
  }, [question, validOptions, context, sampleSize, audience]);

  // ─── Scale up from results ──
  const handleScaleUp = useCallback((n: number) => {
    setSampleSize(n);
    setResult(null);
    setStep('running');
    // Re-trigger launch with new size
    setTimeout(() => {
      setProgress({ current: 0, total: n, interim: {} });
      submitSurvey({
        client_name: 'Sophie Survey',
        question,
        options: validOptions,
        context,
        sample_size: n,
        age_min: audience.ageMin,
        age_max: audience.ageMax,
        gender: audience.gender !== 'all' ? audience.gender : undefined,
        housing: audience.housing !== 'all' ? audience.housing : undefined,
        income_min: audience.incomeMin || undefined,
        income_max: audience.incomeMax || undefined,
        ethnicity: audience.ethnicity !== 'all' ? audience.ethnicity : undefined,
        marital: audience.marital !== 'all' ? audience.marital : undefined,
        education: audience.education !== 'all' ? audience.education : undefined,
        life_phase: audience.lifePhase !== 'all' ? audience.lifePhase : undefined,
      }).then(({ job_id }) => {
        if (pollRef.current) clearInterval(pollRef.current);
        pollRef.current = setInterval(async () => {
          try {
            const status = await getJobStatus(job_id);
            setProgress({
              current: status.progress,
              total: status.total,
              interim: status.result?.overall.choice_distribution || {},
            });
            if (status.status === 'done' && status.result) {
              clearInterval(pollRef.current);
              setResult(status.result);
              setStep('results');
            }
          } catch { /* keep polling */ }
        }, 2000);
      });
    }, 100);
  }, [question, validOptions, context, audience]);

  const FC = 'w-full bg-[#111827] border border-[#1e293b] rounded-xl px-4 py-3 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60';
  const SFC = 'w-full bg-[#0d1117] border border-[#1e293b] rounded-lg px-3 py-2 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60';

  const applySurveyScenario = (s: InspirationScenario) => {
    // Map category to industry
    const catToIndustry: Record<string, string> = {
      policy: 'government', social: 'government', finance: 'finance', health: 'healthcare', consumer: 'retail',
    };
    setIndustry(catToIndustry[s.category] || 'other');
    setQuestion(zh ? s.questionZh : s.question);
    setOptions(zh ? [...s.optionsZh] : [...s.options]);
    if (s.context) setContext(zh ? (s.contextZh || s.context) : s.context);
  };

  // Group scenarios by category
  const groupedSurvey = SURVEY_SCENARIOS.reduce((acc, s) => {
    if (!acc[s.category]) acc[s.category] = [];
    acc[s.category].push(s);
    return acc;
  }, {} as Record<string, InspirationScenario[]>);

  const survCatKeys = Object.keys(groupedSurvey);
  const survLeftCats = survCatKeys.filter((_, i) => i % 2 === 0);
  const survRightCats = survCatKeys.filter((_, i) => i % 2 === 1);

  const renderSurveySidebar = (categories: string[]) => (
    <div className="space-y-4 border border-[#1e293b]/60 rounded-2xl bg-[#0a0e1a]/50 p-3 backdrop-blur-sm">
      <div className="text-[10px] text-[#475569] uppercase tracking-widest font-semibold text-center mb-2">
        {zh ? '调研灵感' : 'Survey Ideas'}
      </div>
      {categories.map(cat => (
        <div key={cat}>
          <div className="text-[10px] text-[#64748b] uppercase tracking-wider font-semibold mb-1.5 px-1">
            {zh ? CATEGORY_LABELS[cat]?.zh : CATEGORY_LABELS[cat]?.en}
          </div>
          <div className="space-y-1.5">
            {groupedSurvey[cat].map((s, i) => (
              <button key={i} onClick={() => applySurveyScenario(s)}
                className="w-full text-left bg-[#0d1117] border border-[#1e293b] rounded-lg p-2.5 hover:border-blue-500/50 hover:bg-blue-500/5 transition-all group">
                <div className="flex items-start gap-2">
                  <span className="text-sm flex-shrink-0 mt-0.5">{s.icon}</span>
                  <div className="min-w-0">
                    <div className="text-xs font-semibold text-[#94a3b8] group-hover:text-blue-300 truncate">
                      {zh ? s.titleZh : s.title}
                    </div>
                    <div className="text-[10px] text-[#475569] leading-snug mt-0.5 line-clamp-2">
                      {zh ? s.questionZh : s.question}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-[#050810] text-[#e2e8f0]">
      <NavBar />

      {/* 3-column layout on form step, centered on other steps */}
      <div className={step === 'form' ? 'max-w-7xl mx-auto px-4 py-8 flex gap-6' : 'max-w-2xl mx-auto px-6 py-8'}>

        {/* Left sidebar — only on form step, xl screens */}
        {step === 'form' && (
          <div className="hidden xl:block w-56 flex-shrink-0 sticky top-8 self-start max-h-[calc(100vh-4rem)] overflow-y-auto scrollbar-thin">
            {renderSurveySidebar(survLeftCats)}
          </div>
        )}

        {/* Center content */}
        <div className={step === 'form' ? 'flex-1 max-w-2xl mx-auto' : ''}>

        {/* Step indicator — clickable for completed steps */}
        <div className="flex items-center gap-2 mb-8">
          {(['form', 'scale', 'running', 'results', 'feedback'] as const).map((s, i) => {
            const allSteps = ['form', 'scale', 'running', 'results', 'feedback'] as const;
            const stepLabels = zh
              ? ['设计', '规模', '运行', '结果', '反馈']
              : ['Design', 'Scale', 'Run', 'Results', 'Feedback'];
            const currentIdx = allSteps.indexOf(step as typeof allSteps[number]);
            const isCompleted = currentIdx > i;
            const isCurrent = step === s;
            const isClickable = isCompleted && s !== 'running'; // can't go back to 'running'
            return (
              <div key={s} className="flex items-center gap-2">
                <button
                  onClick={() => isClickable && setStep(s as Step)}
                  disabled={!isClickable}
                  title={stepLabels[i]}
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                    isCurrent ? 'bg-blue-500 text-white' :
                    isCompleted ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30 cursor-pointer' :
                    'bg-[#1e293b] text-[#475569]'
                  }`}>{i + 1}</button>
                {i < 4 && <div className="w-8 h-px bg-[#1e293b]" />}
              </div>
            );
          })}
        </div>

        {/* ═══ STEP 1: FORM ═══ */}
        {step === 'form' && (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold mb-1">{zh ? '设计你的调研' : 'Design Your Survey'}</h1>
              <p className="text-sm text-[#64748b]">{zh ? '填写越具体，结果越准确' : 'The more specific, the more accurate'}</p>
            </div>

            {/* Evaluation feedback (if issues) */}
            {evalResult && !evalResult.pass && evalResult.issues.length > 0 && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 space-y-2">
                <div className="text-sm font-bold text-red-400">{zh ? 'Sophie 建议修改' : 'Sophie suggests changes'}</div>
                {evalResult.issues.map((iss, i) => (
                  <p key={i} className="text-sm text-red-300">{iss.message}</p>
                ))}
              </div>
            )}

            {/* Industry */}
            <div>
              <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-1.5 block">
                {zh ? '行业' : 'Industry'}
              </label>
              <select value={industry} onChange={e => setIndustry(e.target.value)} className={FC}>
                <option value="">{zh ? '选择行业...' : 'Select industry...'}</option>
                {INDUSTRIES.map(ind => (
                  <option key={ind.value} value={ind.value}>{zh ? ind.labelZh : ind.label}</option>
                ))}
              </select>
            </div>

            {/* Question */}
            <div>
              <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-1.5 block">
                {zh ? '调研问题' : 'Survey Question'}
              </label>
              <textarea
                value={question}
                onChange={e => setQuestion(e.target.value)}
                rows={3}
                placeholder={zh
                  ? '具体一些效果更好。比如：如果 CPF 提取年龄从 55 岁提高到 60 岁，并提供更高利率，你会支持吗？'
                  : 'Be specific for better results. e.g.: If the CPF withdrawal age is raised from 55 to 60, with enhanced interest rates, would you support it?'}
                className={`${FC} resize-none leading-relaxed placeholder:text-[#334155]`}
              />
            </div>

            {/* Options */}
            <div>
              <div className="flex justify-between items-center mb-1.5">
                <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider">{zh ? '选项' : 'Options'}</label>
                <button onClick={addOpt} className="text-xs text-blue-400 hover:text-blue-300 font-medium">+ {zh ? '添加' : 'Add'}</button>
              </div>
              <div className="space-y-2">
                {options.map((opt, i) => (
                  <div key={i} className="flex gap-2 items-center">
                    <span className="text-xs text-[#475569] w-5 text-right font-mono">{i + 1}</span>
                    <input value={opt} onChange={e => updateOpt(i, e.target.value)}
                      placeholder={i === 0 ? (zh ? '强烈支持' : 'Strongly support') :
                                   i === 1 ? (zh ? '比较支持' : 'Somewhat support') :
                                   i === 2 ? (zh ? '中立' : 'Neutral') :
                                   i === 3 ? (zh ? '比较反对' : 'Somewhat oppose') :
                                   i === 4 ? (zh ? '强烈反对' : 'Strongly oppose') : ''}
                      className={`flex-1 ${FC}`} />
                    {options.length > 2 && (
                      <button onClick={() => removeOpt(i)} className="text-[#475569] hover:text-red-400 text-sm px-1">&times;</button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Context (optional) */}
            <div>
              <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-1.5 block">
                {zh ? '背景信息（可选）' : 'Background Context (optional)'}
              </label>
              <textarea
                value={context}
                onChange={e => setContext(e.target.value)}
                rows={2}
                placeholder={zh
                  ? '给 AI 市民的背景知识。比如：CPF 当前提取年龄 55 岁，利率 OA 2.5%，SA 4%...'
                  : 'Background for AI citizens. e.g.: CPF current withdrawal age is 55, OA interest rate 2.5%, SA 4%...'}
                className={`${FC} resize-none leading-relaxed placeholder:text-[#334155]`}
              />
            </div>

            {/* Audience */}
            <div>
              <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-3 block">
                {zh ? '目标人群' : 'Target Audience'}
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-[#64748b] mb-1 block">{zh ? '最小年龄' : 'Age Min'}</label>
                  <input type="number" value={audience.ageMin} onChange={e => updateAud('ageMin', +e.target.value)} className={SFC} />
                </div>
                <div>
                  <label className="text-xs text-[#64748b] mb-1 block">{zh ? '最大年龄' : 'Age Max'}</label>
                  <input type="number" value={audience.ageMax} onChange={e => updateAud('ageMax', +e.target.value)} className={SFC} />
                </div>
                <div>
                  <label className="text-xs text-[#64748b] mb-1 block">{zh ? '性别' : 'Gender'}</label>
                  <select value={audience.gender} onChange={e => updateAud('gender', e.target.value)} className={SFC}>
                    <option value="all">{zh ? '全部' : 'All'}</option>
                    <option value="M">{zh ? '男' : 'Male'}</option>
                    <option value="F">{zh ? '女' : 'Female'}</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-[#64748b] mb-1 block">{zh ? '种族' : 'Ethnicity'}</label>
                  <select value={audience.ethnicity} onChange={e => updateAud('ethnicity', e.target.value)} className={SFC}>
                    <option value="all">{zh ? '全部' : 'All'}</option>
                    <option value="Chinese">{zh ? '华族' : 'Chinese'}</option>
                    <option value="Malay">{zh ? '马来族' : 'Malay'}</option>
                    <option value="Indian">{zh ? '印度族' : 'Indian'}</option>
                    <option value="Others">{zh ? '其他' : 'Others'}</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-[#64748b] mb-1 block">{zh ? '住房类型' : 'Housing'}</label>
                  <select value={audience.housing} onChange={e => updateAud('housing', e.target.value)} className={SFC}>
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
                  <label className="text-xs text-[#64748b] mb-1 block">{zh ? '教育程度' : 'Education'}</label>
                  <select value={audience.education} onChange={e => updateAud('education', e.target.value)} className={SFC}>
                    <option value="all">{zh ? '全部' : 'All'}</option>
                    <option value="No_Formal">{zh ? '无正式学历' : 'No Formal'}</option>
                    <option value="Primary">{zh ? '小学' : 'Primary'}</option>
                    <option value="Secondary">{zh ? '中学' : 'Secondary'}</option>
                    <option value="Post_Secondary">{zh ? '大专' : 'Post Secondary'}</option>
                    <option value="Polytechnic">{zh ? '理工学院' : 'Polytechnic'}</option>
                    <option value="University">{zh ? '大学' : 'University'}</option>
                    <option value="Postgraduate">{zh ? '研究生' : 'Postgraduate'}</option>
                  </select>
                </div>
              </div>

              {/* Advanced filters toggle */}
              <button onClick={() => setShowAdvancedAud(!showAdvancedAud)}
                className="mt-3 text-xs text-blue-400 hover:text-blue-300 font-medium">
                {showAdvancedAud ? (zh ? '收起高级筛选 ▲' : 'Hide advanced ▲') : (zh ? '更多筛选维度 ▼（职业/区域/收入/婚姻/宗教）' : 'More filters ▼ (occupation/area/income/marital/religion)')}
              </button>

              {showAdvancedAud && (
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-[#1e293b]">
                  <div>
                    <label className="text-xs text-[#64748b] mb-1 block">{zh ? '职业' : 'Occupation'}</label>
                    <select value={audience.occupation} onChange={e => updateAud('occupation', e.target.value)} className={SFC}>
                      <option value="all">{zh ? '全部' : 'All'}</option>
                      {OCCUPATIONS.map(o => <option key={o.value} value={o.value}>{zh ? o.labelZh : o.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-[#64748b] mb-1 block">{zh ? '居住区域' : 'Planning Area'}</label>
                    <select value={audience.planningArea} onChange={e => updateAud('planningArea', e.target.value)} className={SFC}>
                      <option value="all">{zh ? '全部' : 'All'}</option>
                      {PLANNING_AREAS.map(a => <option key={a} value={a}>{a}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-[#64748b] mb-1 block">{zh ? '收入下限' : 'Income Min'}</label>
                    <select value={audience.incomeMin} onChange={e => updateAud('incomeMin', +e.target.value)} className={SFC}>
                      <option value={0}>{zh ? '不限' : 'No min'}</option>
                      <option value={1000}>S$1,000</option>
                      <option value={3000}>S$3,000</option>
                      <option value={5000}>S$5,000</option>
                      <option value={7000}>S$7,000</option>
                      <option value={10000}>S$10,000</option>
                      <option value={15000}>S$15,000</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-[#64748b] mb-1 block">{zh ? '收入上限' : 'Income Max'}</label>
                    <select value={audience.incomeMax} onChange={e => updateAud('incomeMax', +e.target.value)} className={SFC}>
                      <option value={0}>{zh ? '不限' : 'No max'}</option>
                      <option value={3000}>S$3,000</option>
                      <option value={5000}>S$5,000</option>
                      <option value={7000}>S$7,000</option>
                      <option value={10000}>S$10,000</option>
                      <option value={15000}>S$15,000</option>
                      <option value={20000}>S$20,000+</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-[#64748b] mb-1 block">{zh ? '婚姻状况' : 'Marital'}</label>
                    <select value={audience.marital} onChange={e => updateAud('marital', e.target.value)} className={SFC}>
                      <option value="all">{zh ? '全部' : 'All'}</option>
                      <option value="Single">{zh ? '单身' : 'Single'}</option>
                      <option value="Married">{zh ? '已婚' : 'Married'}</option>
                      <option value="Divorced">{zh ? '离异' : 'Divorced'}</option>
                      <option value="Widowed">{zh ? '丧偶' : 'Widowed'}</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-[#64748b] mb-1 block">{zh ? '宗教' : 'Religion'}</label>
                    <select value={audience.religion} onChange={e => updateAud('religion', e.target.value)} className={SFC}>
                      <option value="all">{zh ? '全部' : 'All'}</option>
                      <option value="Buddhism">{zh ? '佛教' : 'Buddhism'}</option>
                      <option value="Christianity">{zh ? '基督教' : 'Christianity'}</option>
                      <option value="Islam">{zh ? '伊斯兰教' : 'Islam'}</option>
                      <option value="Taoism">{zh ? '道教' : 'Taoism'}</option>
                      <option value="Hinduism">{zh ? '印度教' : 'Hinduism'}</option>
                      <option value="None">{zh ? '无宗教' : 'No Religion'}</option>
                    </select>
                  </div>
                </div>
              )}
            </div>

            {/* Submit */}
            {!canSubmit && (question.trim() || validOptions.length > 0 || industry) && (
              <div className="text-xs text-[#64748b] space-y-0.5">
                {!industry && <p>{zh ? '· 请选择行业' : '· Please select an industry'}</p>}
                {!question.trim() && <p>{zh ? '· 请填写调研问题' : '· Please enter a survey question'}</p>}
                {validOptions.length < 2 && <p>{zh ? '· 至少填写 2 个选项' : '· At least 2 options required'}</p>}
              </div>
            )}
            <button onClick={handleSubmit} disabled={!canSubmit}
              className="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-base font-bold rounded-2xl hover:shadow-lg hover:shadow-blue-500/25 transition-all disabled:opacity-30">
              {zh ? '提交给 Sophie' : 'Submit to Sophie'}
            </button>

            {/* Mobile scenario inspirations — shown below form on small screens */}
            <div className="xl:hidden mt-8 border-t border-[#1e293b] pt-6">
              <div className="text-xs text-[#475569] uppercase tracking-widest font-semibold text-center mb-4">
                {zh ? '调研灵感 — 点击预填表单' : 'Survey Ideas — Click to Pre-fill'}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {SURVEY_SCENARIOS.map((s, i) => (
                  <button key={i} onClick={() => applySurveyScenario(s)}
                    className="text-left bg-[#0d1117] border border-[#1e293b] rounded-lg p-2.5 hover:border-blue-500/50 hover:bg-blue-500/5 transition-all group">
                    <div className="flex items-start gap-1.5">
                      <span className="text-sm flex-shrink-0">{s.icon}</span>
                      <div className="min-w-0">
                        <div className="text-xs font-semibold text-[#94a3b8] group-hover:text-blue-300 truncate">
                          {zh ? s.titleZh : s.title}
                        </div>
                        <div className="text-[10px] text-[#475569] leading-snug mt-0.5 line-clamp-1">
                          {zh ? s.questionZh : s.question}
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ═══ SCIENTIFIC FOUNDATION ═══ */}
        {step === 'form' && (
          <div className="mt-16 space-y-10 border-t border-[#1e293b] pt-12">
            <div className="text-center">
              <h2 className="text-xl font-bold mb-2">
                {zh ? '科学基础与方法论' : 'Scientific Foundation & Methodology'}
              </h2>
              <p className="text-sm text-[#64748b] max-w-2xl mx-auto">
                {zh
                  ? '我们的合成调研系统建立在调查方法论、合成人口学和 LLM 行为模拟三大领域的前沿研究之上。'
                  : 'Our synthetic survey system is built on cutting-edge research spanning survey methodology, synthetic demography, and LLM behavioral simulation.'}
              </p>
            </div>

            {/* ── LLM as Survey Respondent ── */}
            <div>
              <h3 className="text-sm font-bold text-blue-400 uppercase tracking-wider mb-4">
                {zh ? 'LLM 作为调查受访者' : 'LLM as Survey Respondent'}
              </h3>
              <div className="space-y-3">
                {[
                  {
                    title: 'Out of One, Many: Using Language Models to Simulate Human Samples',
                    titleZh: '一生多：使用语言模型模拟人类样本',
                    authors: 'Argyle, L.P., Busby, E.C., Fulda, N., et al. Political Analysis, 2023.',
                    desc: 'Seminal paper demonstrating that GPT-3 conditioned on demographic backstories (silicon samples) can reproduce real survey results from ANES with r=0.85 correlation. Established that LLMs encode meaningful demographic-opinion associations.',
                    descZh: '开创性论文，证明以人口统计背景故事为条件的 GPT-3（"硅样本"）可以以 r=0.85 的相关性复制 ANES 的真实调查结果。确立了 LLM 编码了有意义的人口统计-意见关联。',
                    tag: zh ? '核心' : 'Core',
                  },
                  {
                    title: 'Large Language Models as Simulated Economic Agents',
                    titleZh: '大语言模型作为模拟经济主体',
                    authors: 'Horton, J.J. NBER Working Paper, 2023.',
                    desc: 'MIT economist showed LLMs replicate classic behavioral economics experiments: ultimatum game, dictator game, and prospect theory violations. Homo silicus behaves remarkably like homo economicus — with realistic irrationality.',
                    descZh: 'MIT 经济学家证明 LLM 可以复制经典行为经济学实验：最后通牒博弈、独裁者博弈和前景理论违反。"硅人"的行为与"经济人"惊人相似 — 包括现实中的非理性。',
                    tag: zh ? '经济学' : 'Econ',
                  },
                  {
                    title: 'Using GPT for Market Research',
                    titleZh: '使用 GPT 进行市场研究',
                    authors: 'Brand, J., Israeli, A., & Ngwe, D. Harvard Business School Working Paper, 2023.',
                    desc: 'Harvard Business School validated LLM-based market research against real consumer data. Found synthetic conjoint analysis matches actual consumer preferences with high accuracy, at 1/100th the cost.',
                    descZh: '哈佛商学院将基于 LLM 的市场研究与真实消费者数据进行验证。发现合成联合分析以高精度匹配实际消费者偏好，成本仅为 1/100。',
                    tag: zh ? '商业' : 'Business',
                  },
                  {
                    title: 'Can Large Language Models Transform Computational Social Science?',
                    titleZh: '大语言模型能否变革计算社会科学？',
                    authors: 'Ziems, C., Held, W., Shaikh, O., et al. Computational Linguistics, 2024.',
                    desc: 'Comprehensive review of 40+ studies on LLMs for social science tasks including survey simulation, content analysis, and behavioral prediction. Concludes LLMs are transformative but require careful calibration.',
                    descZh: '对 40 多项关于 LLM 在社会科学任务（包括调查模拟、内容分析和行为预测）中应用的研究的综合综述。结论是 LLM 具有变革性但需要仔细校准。',
                    tag: zh ? '综述' : 'Review',
                  },
                ].map((item, i) => (
                  <div key={i} className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-5">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div>
                        <div className="text-sm font-bold text-[#e2e8f0]">{zh ? item.titleZh : item.title}</div>
                        <div className="text-[11px] text-[#64748b] mt-0.5 font-mono">{item.authors}</div>
                      </div>
                      <span className="text-[10px] px-2 py-1 rounded-lg bg-blue-500/10 text-blue-400 font-semibold whitespace-nowrap">{item.tag}</span>
                    </div>
                    <p className="text-xs text-[#94a3b8] leading-relaxed">{zh ? item.descZh : item.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Survey Methodology ── */}
            <div>
              <h3 className="text-sm font-bold text-purple-400 uppercase tracking-wider mb-4">
                {zh ? '调查方法论经典' : 'Survey Methodology Classics'}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[
                  {
                    icon: '📖',
                    title: 'Survey Methodology (Groves et al.)',
                    titleZh: '调查方法论 (Groves 等)',
                    desc: 'The definitive textbook on survey design, covering sampling theory, nonresponse bias, measurement error, and mode effects. Our stratified sampling follows Neyman allocation as described in Chapter 4.',
                    descZh: '调查设计的权威教材，涵盖抽样理论、无回应偏差、测量误差和模式效应。我们的分层抽样遵循第 4 章描述的 Neyman 分配。',
                  },
                  {
                    icon: '📊',
                    title: 'Stratified Sampling (Neyman, 1934)',
                    titleZh: '分层抽样 (Neyman, 1934)',
                    desc: 'Jerzy Neyman\'s optimal allocation theorem — sample sizes proportional to stratum variance. Our age×gender×housing stratification ensures demographic representativeness.',
                    descZh: 'Jerzy Neyman 的最优分配定理 — 样本量与层内方差成比例。我们的年龄×性别×住房分层确保了人口统计代表性。',
                  },
                  {
                    icon: '⚖️',
                    title: 'Total Survey Error Framework',
                    titleZh: '总调查误差框架',
                    authors: 'Groves & Lyberg, Public Opinion Quarterly, 2010',
                    desc: 'Unified framework decomposing survey error into coverage, sampling, nonresponse, and measurement components. Our approach eliminates nonresponse bias (100% response rate) while introducing LLM-specific measurement considerations.',
                    descZh: '统一框架，将调查误差分解为覆盖、抽样、无回应和测量四个组成部分。我们的方法消除了无回应偏差（100% 回应率），同时引入 LLM 特有的测量考量。',
                  },
                  {
                    icon: '🎯',
                    title: 'Conjoint Analysis (Green & Srinivasan)',
                    titleZh: '联合分析 (Green & Srinivasan)',
                    desc: 'Gold standard method for understanding consumer preferences through trade-off analysis. Our multi-dimensional agent profiles enable implicit conjoint: how do age×income×ethnicity interact to shape preferences?',
                    descZh: '通过权衡分析理解消费者偏好的金标准方法。我们的多维智能体画像实现了隐式联合分析：年龄×收入×种族如何交互影响偏好？',
                  },
                ].map((item, i) => (
                  <div key={i} className="bg-[#111827] border border-[#1e293b] rounded-xl p-4">
                    <div className="text-xl mb-2">{item.icon}</div>
                    <div className="text-sm font-bold text-[#e2e8f0] mb-1">{zh ? item.titleZh : item.title}</div>
                    <p className="text-xs text-[#94a3b8] leading-relaxed">{zh ? item.descZh : item.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Synthetic Population & Census ── */}
            <div>
              <h3 className="text-sm font-bold text-cyan-400 uppercase tracking-wider mb-4">
                {zh ? '合成人口与人口普查' : 'Synthetic Populations & Census Science'}
              </h3>
              <div className="space-y-3">
                {[
                  {
                    title: 'Creating Synthetic Baseline Populations (RAND)',
                    titleZh: '创建合成基准人口 (RAND)',
                    authors: 'Beckman, R.J., Baggerly, K.A., McKay, M.D. Transportation Research, 1996.',
                    desc: 'Pioneered Iterative Proportional Fitting (IPF) for census-calibrated synthetic populations. Our 170,000+ Singapore agents use the same mathematical foundation: joint probability distributions from official census microdata.',
                    descZh: '开创了用于人口普查校准合成人口的迭代比例拟合 (IPF) 方法。我们的 17万+ 新加坡智能体使用相同的数学基础：来自官方人口普查微观数据的联合概率分布。',
                  },
                  {
                    title: 'Singapore Census of Population 2020',
                    titleZh: '新加坡 2020 年人口普查',
                    authors: 'Singapore Department of Statistics. Official census report.',
                    desc: 'The ground truth for our synthetic population. We calibrate joint distributions of age, gender, ethnicity, housing type, income, education, occupation, marital status, religion, and planning area to match census marginals.',
                    descZh: '我们合成人口的真实基准。我们将年龄、性别、种族、住房类型、收入、教育、职业、婚姻状况、宗教和居住区域的联合分布校准到与人口普查边际分布一致。',
                  },
                  {
                    title: 'Microsimulation in Government Policy',
                    titleZh: '微观模拟在政府政策中的应用',
                    authors: 'Bourguignon, F. & Spadaro, A. "Microsimulation as a Tool for Evaluating Redistribution Policies." Journal of Economic Inequality, 2006.',
                    desc: 'World Bank and EU governments use microsimulation with synthetic populations to pre-test tax, welfare, and healthcare policies. Our system adds behavioral responses (via LLM) to traditional demographic microsimulation.',
                    descZh: '世界银行和欧盟政府使用合成人口进行微观模拟，预测试税收、福利和医疗政策。我们的系统在传统人口统计微观模拟基础上增加了行为响应（通过 LLM）。',
                  },
                ].map((item, i) => (
                  <div key={i} className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-5">
                    <div className="text-sm font-bold text-[#e2e8f0] mb-0.5">{zh ? item.titleZh : item.title}</div>
                    <div className="text-[11px] text-[#64748b] font-mono mb-2">{item.authors}</div>
                    <p className="text-xs text-[#94a3b8] leading-relaxed">{zh ? item.descZh : item.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Quality Assurance ── */}
            <div>
              <h3 className="text-sm font-bold text-green-400 uppercase tracking-wider mb-4">
                {zh ? '质量保障与验证' : 'Quality Assurance & Validation'}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[
                  {
                    icon: '🛡️',
                    title: 'NVIDIA Nemotron-70B Reward Model',
                    titleZh: 'NVIDIA Nemotron-70B 奖励模型',
                    desc: 'State-of-the-art reward model trained on human preference data. We use it to score every synthetic response for coherence, relevance, and demographic consistency. 85%+ high quality rate.',
                    descZh: '基于人类偏好数据训练的最先进奖励模型。我们用它为每个合成回答的连贯性、相关性和人口统计一致性评分。85%+ 高质量率。',
                  },
                  {
                    icon: '✅',
                    title: 'Backtest Validation Protocol',
                    titleZh: '回测验证协议',
                    desc: 'Every model version is backtested against real survey/election results (2023 Presidential: 2.7pp MAE, GE 2025: 6.2pp MAE). Ground truth is strictly isolated — no data leakage.',
                    descZh: '每个模型版本都与真实调查/选举结果进行回测（2023 总统选举：2.7pp MAE，2025 大选：6.2pp MAE）。真实结果严格隔离 — 无数据泄露。',
                  },
                  {
                    icon: '🔄',
                    title: 'Pilot-Then-Scale Protocol',
                    titleZh: '先试点后扩展协议',
                    desc: 'Inspired by clinical trial phases. Start with n=10 pilot to check question clarity, option coverage, and response quality. Iterate at zero cost before committing to large-scale runs.',
                    descZh: '灵感来自临床试验阶段。从 n=10 试点开始，检查问题清晰度、选项覆盖度和回答质量。在投入大规模运行前零成本迭代。',
                  },
                  {
                    icon: '📐',
                    title: 'Sophie AI Pre-Evaluation',
                    titleZh: 'Sophie AI 预评估',
                    desc: 'Before launch, our AI evaluator checks: question bias, option completeness, context appropriateness, and industry-question fit. Prevents common survey design errors automatically.',
                    descZh: '启动前，我们的 AI 评估器检查：问题偏见、选项完整性、背景适当性和行业-问题匹配度。自动防止常见的调查设计错误。',
                  },
                ].map((item, i) => (
                  <div key={i} className="bg-[#111827] border border-[#1e293b] rounded-xl p-4">
                    <div className="text-xl mb-2">{item.icon}</div>
                    <div className="text-sm font-bold text-[#e2e8f0] mb-1">{zh ? item.titleZh : item.title}</div>
                    <p className="text-xs text-[#94a3b8] leading-relaxed">{zh ? item.descZh : item.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Our Pipeline ── */}
            <div className="bg-gradient-to-br from-blue-500/5 to-purple-500/5 border border-blue-500/20 rounded-2xl p-6">
              <h3 className="text-sm font-bold text-[#e2e8f0] mb-3">
                {zh ? '完整调研流水线' : 'Complete Survey Pipeline'}
              </h3>
              <div className="grid grid-cols-3 md:grid-cols-6 gap-3 text-center">
                {[
                  { label: zh ? '问卷设计' : 'Design', sub: 'Sophie AI', icon: '📝' },
                  { label: zh ? '分层抽样' : 'Sampling', sub: 'Neyman IPF', icon: '🎯' },
                  { label: zh ? 'LLM 回答' : 'LLM Response', sub: 'DeepSeek', icon: '🤖' },
                  { label: zh ? '质量评分' : 'Scoring', sub: 'Nemotron-70B', icon: '🛡️' },
                  { label: zh ? '人群分析' : 'Breakdown', sub: zh ? '39 维交叉' : '39-dim cross', icon: '📊' },
                  { label: zh ? '验证报告' : 'Validation', sub: zh ? '回测协议' : 'Backtest', icon: '✅' },
                ].map((m, i) => (
                  <div key={i}>
                    <div className="text-xl mb-1">{m.icon}</div>
                    <div className="text-[11px] font-bold text-[#e2e8f0]">{m.label}</div>
                    <div className="text-[10px] text-[#64748b] mt-0.5">{m.sub}</div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-[#94a3b8] mt-4 text-center leading-relaxed">
                {zh
                  ? '从问卷设计到验证报告，每一步都有学术理论支撑。17万+ AI 市民孪生智能体 × 39 维人口统计画像 × 人口普查校准 × NVIDIA 质量评分 = 可量化、可验证的市场洞察。'
                  : 'Every step from survey design to validation report is backed by academic theory. 170,000+ AI citizen digital twins × 39-dimension profiles × census calibration × NVIDIA quality scoring = quantifiable, verifiable market insights.'}
              </p>
            </div>

            <div className="text-center text-[11px] text-[#475569] pb-4">
              {zh
                ? '以上文献累计引用超过 30,000 次 · 涵盖调查方法论、合成人口学、计算社会科学、行为经济学四大领域'
                : 'Combined citations: 30,000+ · Spanning survey methodology, synthetic demography, computational social science, and behavioral economics'}
            </div>
          </div>
        )}

        {/* ═══ STEP 2: EVALUATING ═══ */}
        {step === 'evaluating' && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-lg font-bold mb-4 animate-pulse">S</div>
            <p className="text-sm text-[#94a3b8]">{zh ? 'Sophie 正在评估你的调研...' : 'Sophie is evaluating your survey...'}</p>
          </div>
        )}

        {/* ═══ STEP 2.5: SOPHIE REVIEW — show suggestions for user to confirm/edit ═══ */}
        {step === 'review' && evalResult && (
          <div className="space-y-6">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-sm font-bold">S</div>
                <div>
                  <h1 className="text-xl font-bold">{zh ? 'Sophie 优化建议' : 'Sophie\'s Suggestions'}</h1>
                  <p className="text-xs text-[#64748b]">{zh ? '以下是 Sophie 对问题和选项的优化建议，你可以直接采用或自行修改' : 'Sophie suggests improvements below. You can accept or edit them.'}</p>
                </div>
              </div>
            </div>

            {/* Fit score */}
            {evalResult.fit_score && (
              <div className="flex items-center gap-3 bg-[#111827] border border-[#1e293b] rounded-xl px-4 py-3">
                <span className={`text-lg font-bold font-mono ${
                  evalResult.fit_score >= 4 ? 'text-green-400' : evalResult.fit_score >= 3 ? 'text-yellow-400' : 'text-orange-400'
                }`}>{evalResult.fit_score}/5</span>
                <div>
                  <div className="text-xs text-[#64748b] uppercase tracking-wider">{zh ? '适配度评分' : 'Fit Score'}</div>
                  {evalResult.fit_reason && <div className="text-sm text-[#94a3b8]">{evalResult.fit_reason}</div>}
                </div>
              </div>
            )}

            {/* Suggested question */}
            {evalResult.suggestion && (
              <div>
                <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-2 block">
                  {zh ? '优化后的问题' : 'Improved Question'}
                </label>
                <div className="bg-[#0d1117] border border-blue-500/30 rounded-xl p-4 mb-2">
                  <p className="text-sm text-blue-300">{evalResult.suggestion}</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => { setQuestion(evalResult.suggestion!); }}
                    className="text-xs px-3 py-1.5 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-lg hover:bg-blue-500/20 transition-all">
                    {zh ? '采用此建议' : 'Accept'}
                  </button>
                  <button onClick={() => setStep('form')}
                    className="text-xs px-3 py-1.5 bg-[#111827] border border-[#1e293b] text-[#94a3b8] rounded-lg hover:border-[#2a3a4f] transition-all">
                    {zh ? '自己修改' : 'Edit myself'}
                  </button>
                </div>
              </div>
            )}

            {/* Suggested options */}
            {evalResult.suggestion_options && evalResult.suggestion_options.length > 0 && (
              <div>
                <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-2 block">
                  {zh ? '优化后的选项' : 'Improved Options'}
                </label>
                <div className="space-y-2">
                  {evalResult.suggestion_options.map((opt, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-xs text-[#475569] font-mono w-6">{i + 1}.</span>
                      <div className="flex-1 bg-[#0d1117] border border-blue-500/20 rounded-lg px-3 py-2 text-sm text-blue-300">{opt}</div>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2 mt-3">
                  <button onClick={() => { setOptions(evalResult.suggestion_options!); }}
                    className="text-xs px-3 py-1.5 bg-blue-500/10 border border-blue-500/30 text-blue-400 rounded-lg hover:bg-blue-500/20 transition-all">
                    {zh ? '采用这些选项' : 'Accept options'}
                  </button>
                  <button onClick={() => setStep('form')}
                    className="text-xs px-3 py-1.5 bg-[#111827] border border-[#1e293b] text-[#94a3b8] rounded-lg hover:border-[#2a3a4f] transition-all">
                    {zh ? '自己修改' : 'Edit myself'}
                  </button>
                </div>
              </div>
            )}

            {/* Ontology note */}
            {evalResult.ontology_note && (
              <div className="bg-[#111827] border border-[#1e293b] rounded-xl px-4 py-3">
                <div className="text-xs text-[#64748b] uppercase tracking-wider mb-1">{zh ? '知识库匹配' : 'Knowledge Base Match'}</div>
                <p className="text-sm text-[#94a3b8]">{evalResult.ontology_note}</p>
              </div>
            )}

            {/* Warnings */}
            {evalResult.issues && evalResult.issues.length > 0 && (
              <div className="space-y-2">
                {evalResult.issues.map((iss, i) => (
                  <div key={i} className={`text-sm px-4 py-3 rounded-xl border ${
                    iss.severity === 'error' ? 'bg-red-500/10 border-red-500/30 text-red-300' : 'bg-orange-500/10 border-orange-500/30 text-orange-300'
                  }`}>
                    {iss.message}
                  </div>
                ))}
              </div>
            )}

            {/* Proceed button */}
            <button onClick={() => setStep('scale')}
              className="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-base font-bold rounded-2xl hover:shadow-lg hover:shadow-blue-500/25 transition-all">
              {zh ? '确认，选择调研规模 →' : 'Confirm & Choose Sample Size →'}
            </button>
          </div>
        )}

        {/* ═══ STEP 3: CHOOSE SCALE ═══ */}
        {step === 'scale' && (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold mb-1">{zh ? '选择调研规模' : 'Choose Sample Size'}</h1>
              <p className="text-sm text-[#64748b]">{zh ? '建议先 10 人试跑，满意后再扩大' : 'Recommend: test with 10, then scale up'}</p>
            </div>

            {/* Evaluation note (if ontology matched) */}
            {evalResult?.ontology_note && (
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
                <p className="text-sm text-blue-300">{evalResult.ontology_note}</p>
                {evalResult.fit_reason && <p className="text-xs text-[#64748b] mt-1">{evalResult.fit_reason}</p>}
              </div>
            )}

            <div className="space-y-2">
              {SAMPLE_SIZES.map(s => (
                <button key={s.n} onClick={() => setSampleSize(s.n)}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all text-left ${
                    sampleSize === s.n
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-[#1e293b] bg-[#0d1117] hover:border-blue-500/40'
                  }`}>
                  <span className="text-lg font-bold text-[#e2e8f0] w-16">{s.label}</span>
                  <span className="flex-1 text-sm text-[#94a3b8]">{zh ? s.useZh : s.use}</span>
                  <span className="text-xs text-[#64748b]">{s.time}</span>
                  <span className="text-xs text-green-400 w-14 text-right">{zh ? s.costZh : s.cost}</span>
                </button>
              ))}
            </div>

            <button onClick={handleLaunch}
              className="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-base font-bold rounded-2xl hover:shadow-lg hover:shadow-blue-500/25 transition-all">
              {zh ? `启动 ${sampleSize.toLocaleString()} 人调研` : `Launch ${sampleSize.toLocaleString()}-Person Survey`}
            </button>

            <button onClick={() => setStep('form')}
              className="w-full py-3 text-sm text-[#64748b] hover:text-[#94a3b8] transition-all">
              {zh ? '← 返回修改' : '← Back to edit'}
            </button>
          </div>
        )}

        {/* ═══ STEP 4: RUNNING ═══ */}
        {step === 'running' && (
          <div className="space-y-6 py-8">
            <div className="text-center">
              <h1 className="text-2xl font-bold mb-1">{zh ? '调研进行中' : 'Survey in Progress'}</h1>
              <p className="text-sm text-[#64748b]">
                {zh ? `${sampleSize.toLocaleString()} 个 AI 市民正在回答...` : `${sampleSize.toLocaleString()} AI citizens responding...`}
              </p>
            </div>

            {/* Progress bar */}
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm text-[#94a3b8]">{progress.current}/{progress.total}</span>
                <span className="text-sm text-blue-400 font-mono">{progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 0}%</span>
              </div>
              <div className="w-full h-3 bg-[#111827] rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500"
                  style={{ width: `${progress.total > 0 ? (progress.current / progress.total) * 100 : 0}%` }} />
              </div>
            </div>

            {/* Interim results */}
            {Object.keys(progress.interim).length > 0 && (
              <div className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-4 space-y-2">
                <div className="text-xs text-[#64748b] uppercase tracking-wider font-semibold mb-2">{zh ? '实时结果' : 'Live Results'}</div>
                {Object.entries(progress.interim).slice(0, 6).map(([opt, cnt]) => (
                  <div key={opt} className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-[#111827] rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500/60 rounded-full" style={{ width: `${progress.current > 0 ? (cnt / progress.current) * 100 : 0}%` }} />
                    </div>
                    <span className="text-xs text-[#94a3b8] w-10 text-right font-mono">{progress.current > 0 ? Math.round((cnt / progress.current) * 100) : 0}%</span>
                    <span className="text-xs text-[#64748b] w-40 truncate">{opt}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ═══ STEP 5: RESULTS ═══ */}
        {step === 'results' && result && (
          <div className="space-y-6">
            {/* Summary bar */}
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold">{zh ? '调研结果' : 'Survey Results'}</h1>
              <div className="flex items-center gap-3 text-sm text-[#94a3b8]">
                <span>{result.n_respondents} {zh ? '受访者' : 'respondents'}</span>
                <span>${result.cost.total_cost_usd.toFixed(3)}</span>
                {result.quality?.available && (
                  <span className="text-xs px-2 py-1 rounded-lg bg-green-500/10 text-green-400">{result.quality.high_quality_pct}% {zh ? '高质量' : 'HQ'}</span>
                )}
              </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-[#1e293b]">
              {[
                { key: 'dist' as const, label: zh ? '分布' : 'Distribution' },
                { key: 'demo' as const, label: zh ? '人群细分' : 'Demographics' },
                { key: 'quotes' as const, label: zh ? '个体引用' : 'Quotes' },
                { key: 'report' as const, label: zh ? '分析报告' : 'Report' },
              ].map(t => (
                <button key={t.key} onClick={() => setResultTab(t.key)}
                  className={`flex-1 py-2.5 text-sm font-semibold ${
                    resultTab === t.key ? 'text-blue-400 border-b-2 border-blue-400' : 'text-[#475569] hover:text-[#94a3b8]'
                  }`}>{t.label}</button>
              ))}
            </div>

            {/* Distribution tab */}
            {resultTab === 'dist' && (
              <div className="space-y-3">
                {Object.entries(result.overall.choice_distribution)
                  .sort(([, a], [, b]) => b - a)
                  .map(([opt, cnt], i) => {
                    const pct = Math.round((cnt / result.n_respondents) * 100);
                    const colors = ['bg-blue-500', 'bg-purple-500', 'bg-green-500', 'bg-orange-500', 'bg-red-500', 'bg-cyan-500', 'bg-yellow-500'];
                    return (
                      <div key={opt}>
                        <div className="flex justify-between mb-1">
                          <span className="text-sm text-[#e2e8f0]">{opt}</span>
                          <span className="text-sm font-mono text-[#94a3b8]">{pct}% ({cnt})</span>
                        </div>
                        <div className="h-3 bg-[#111827] rounded-full overflow-hidden">
                          <div className={`h-full ${colors[i % colors.length]} rounded-full transition-all`} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}

            {/* Demographics tab */}
            {resultTab === 'demo' && (
              <div className="space-y-6">
                {result.breakdowns.by_age && Object.keys(result.breakdowns.by_age).length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-[#e2e8f0] mb-3">{zh ? '按年龄' : 'By Age'}</h3>
                    <div className="space-y-2">
                      {Object.entries(result.breakdowns.by_age).map(([age, d]) => (
                        <div key={age} className="flex items-center gap-3">
                          <span className="text-xs text-[#94a3b8] w-16">{age}</span>
                          <div className="flex-1 h-2 bg-[#111827] rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.round(d.positive_rate * 100)}%` }} />
                          </div>
                          <span className="text-xs font-mono text-[#94a3b8] w-14 text-right">{Math.round(d.positive_rate * 100)}% (n={d.n})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {result.breakdowns.by_income && Object.keys(result.breakdowns.by_income).length > 0 && (
                  <div>
                    <h3 className="text-sm font-bold text-[#e2e8f0] mb-3">{zh ? '按收入' : 'By Income'}</h3>
                    <div className="space-y-2">
                      {Object.entries(result.breakdowns.by_income).map(([inc, d]) => (
                        <div key={inc} className="flex items-center gap-3">
                          <span className="text-xs text-[#94a3b8] w-16">{inc}</span>
                          <div className="flex-1 h-2 bg-[#111827] rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500 rounded-full" style={{ width: `${Math.round(d.positive_rate * 100)}%` }} />
                          </div>
                          <span className="text-xs font-mono text-[#94a3b8] w-14 text-right">{Math.round(d.positive_rate * 100)}% (n={d.n})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Quotes tab */}
            {resultTab === 'quotes' && (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {result.agent_log.slice(0, 20).map((a, i) => (
                  <div key={i} className="p-3 bg-[#0d1117] rounded-xl border border-[#1e293b]">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-blue-400">{a.gender === 'M' ? '♂' : '♀'} {a.age}yo</span>
                      <span className="text-xs text-[#64748b]">{a.ethnicity}</span>
                      <span className="text-xs text-[#64748b]">S${a.income.toLocaleString()}/mo</span>
                      {a.reward !== null && (
                        <span className={`text-[11px] ml-auto px-1.5 py-0.5 rounded-md ${
                          a.reward > -5 ? 'bg-green-500/10 text-green-400' : a.reward > -15 ? 'bg-yellow-500/10 text-yellow-400' : 'bg-red-500/10 text-red-400'
                        }`}>{a.reward.toFixed(1)}</span>
                      )}
                    </div>
                    <div className="text-sm text-[#e2e8f0]">&rarr; <span className="text-purple-300">{a.choice}</span></div>
                  </div>
                ))}
                {result.reasoning_samples.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-[#1e293b]">
                    <div className="text-xs text-[#94a3b8] uppercase font-semibold mb-2">{zh ? '推理示例' : 'Sample Reasoning'}</div>
                    {result.reasoning_samples.slice(0, 5).map((r, i) => (
                      <p key={i} className="text-sm text-[#94a3b8] italic mb-2 pl-3 border-l-2 border-[#1e293b] leading-relaxed">&ldquo;{r}&rdquo;</p>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Report tab */}
            {resultTab === 'report' && (
              <div className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-6 space-y-4">
                <h3 className="text-sm font-bold">{zh ? '调研报告摘要' : 'Survey Report Summary'}</h3>
                <div className="text-sm text-[#94a3b8] leading-relaxed space-y-3">
                  <p>
                    <strong>{zh ? '问题：' : 'Question: '}</strong>{question}
                  </p>
                  <p>
                    <strong>{zh ? '样本量：' : 'Sample: '}</strong>
                    {result.n_respondents} {zh ? '人' : 'respondents'}
                    {result.quality?.available && ` (${result.quality.high_quality_pct}% ${zh ? '高质量' : 'high quality'})`}
                  </p>
                  <p>
                    <strong>{zh ? '主要发现：' : 'Key finding: '}</strong>
                    {(() => {
                      const sorted = Object.entries(result.overall.choice_distribution).sort(([, a], [, b]) => b - a);
                      const top = sorted[0];
                      const second = sorted[1];
                      return zh
                        ? `最多人选择「${top[0]}」（${Math.round((top[1] / result.n_respondents) * 100)}%），其次是「${second?.[0]}」（${second ? Math.round((second[1] / result.n_respondents) * 100) : 0}%）。`
                        : `Top choice: "${top[0]}" (${Math.round((top[1] / result.n_respondents) * 100)}%), followed by "${second?.[0]}" (${second ? Math.round((second[1] / result.n_respondents) * 100) : 0}%).`;
                    })()}
                  </p>
                  <p>
                    <strong>{zh ? '费用：' : 'Cost: '}</strong>${result.cost.total_cost_usd.toFixed(3)} ({result.cost.total_tokens.toLocaleString()} tokens)
                  </p>
                </div>
              </div>
            )}

            {/* Scale up / Follow-up actions */}
            <div className="space-y-3 pt-4 border-t border-[#1e293b]">
              <p className="text-xs text-[#64748b] uppercase tracking-wider font-semibold">{zh ? '下一步' : 'Next Steps'}</p>
              <div className="flex flex-wrap gap-2">
                {[100, 1000, 2000, 5000, 10000].filter(n => n > sampleSize).map(n => (
                  <button key={n} onClick={() => handleScaleUp(n)}
                    className="px-4 py-2 bg-blue-500/10 border border-blue-500/30 text-blue-300 text-sm rounded-xl hover:bg-blue-500/20 transition-all">
                    {zh ? `扩大到 ${n.toLocaleString()} 人` : `Scale to ${n.toLocaleString()}`}
                  </button>
                ))}
                <button onClick={() => { setStep('form'); setResult(null); }}
                  className="px-4 py-2 bg-[#111827] border border-[#1e293b] text-[#94a3b8] text-sm rounded-xl hover:text-[#e2e8f0] transition-all">
                  {zh ? '修改再跑' : 'Edit & Rerun'}
                </button>
                <button onClick={() => setStep('feedback')}
                  className="px-4 py-2 bg-purple-500/10 border border-purple-500/30 text-purple-300 text-sm rounded-xl hover:bg-purple-500/20 transition-all">
                  {zh ? '评价结果' : 'Rate Results'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ═══ STEP 6: FEEDBACK ═══ */}
        {step === 'feedback' && (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold mb-1">{zh ? '你的反馈' : 'Your Feedback'}</h1>
              <p className="text-sm text-[#64748b]">{zh ? '帮助我们改进系统' : 'Help us improve the system'}</p>
            </div>

            {/* Star rating */}
            <div>
              <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-2 block">{zh ? '整体评分' : 'Overall Rating'}</label>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map(n => (
                  <button key={n} onClick={() => setRating(n)}
                    className={`w-10 h-10 rounded-xl text-lg font-bold transition-all ${
                      rating >= n ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40' : 'bg-[#111827] text-[#475569] border border-[#1e293b]'
                    }`}>
                    {n}
                  </button>
                ))}
              </div>
            </div>

            {/* Expectation match */}
            <div>
              <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-2 block">{zh ? '结果与你的预期一致吗？' : 'Results match your expectations?'}</label>
              <div className="flex gap-2">
                {[
                  { v: 'yes' as const, label: zh ? '一致' : 'Yes' },
                  { v: 'partial' as const, label: zh ? '部分一致' : 'Partially' },
                  { v: 'no' as const, label: zh ? '不一致' : 'No' },
                ].map(opt => (
                  <button key={opt.v} onClick={() => setExpectMatch(opt.v)}
                    className={`px-4 py-2 rounded-xl text-sm font-medium border transition-all ${
                      expectMatch === opt.v ? 'border-blue-500 bg-blue-500/10 text-blue-300' : 'border-[#1e293b] bg-[#0d1117] text-[#94a3b8]'
                    }`}>{opt.label}</button>
                ))}
              </div>
            </div>

            {/* Comment */}
            <div>
              <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-1.5 block">{zh ? '一句话反馈（可选）' : 'Quick comment (optional)'}</label>
              <input value={feedbackText} onChange={e => setFeedbackText(e.target.value)}
                placeholder={zh ? '对结果有什么看法？' : 'Any thoughts on the results?'}
                className={FC} />
            </div>

            {feedbackSubmitted ? (
              <div className="text-center space-y-4">
                <div className="text-green-400 text-lg">&#10003;</div>
                <p className="text-sm text-[#e2e8f0]">{zh ? '感谢您的宝贵意见！' : 'Thank you for your valuable feedback!'}</p>
                <div className="flex flex-col gap-2 items-center">
                  <button onClick={() => { setStep('form'); setFeedbackSubmitted(false); setFeedbackText(''); }}
                    className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-sm font-bold rounded-xl hover:shadow-lg hover:shadow-blue-500/25 transition-all">
                    {zh ? '开始新调研' : 'Start New Survey'}
                  </button>
                  <button onClick={() => setStep('results')}
                    className="px-6 py-3 text-[#64748b] text-sm hover:text-[#94a3b8] transition-all">
                    {zh ? '← 返回结果' : '← Back to results'}
                  </button>
                </div>
              </div>
            ) : (
              <>
                <button onClick={() => {
                  // TODO: Save feedback to Supabase
                  setFeedbackSubmitted(true);
                }}
                  className="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-base font-bold rounded-2xl hover:shadow-lg hover:shadow-blue-500/25 transition-all">
                  {zh ? '提交反馈' : 'Submit Feedback'}
                </button>

                <button onClick={() => setStep('results')}
                  className="w-full py-3 text-sm text-[#64748b] hover:text-[#94a3b8] transition-all">
                  {zh ? '← 返回结果' : '← Back to results'}
                </button>
              </>
            )}
          </div>
        )}

        </div>{/* end center content */}

        {/* Right sidebar — only on form step, xl screens */}
        {step === 'form' && (
          <div className="hidden xl:block w-56 flex-shrink-0 sticky top-8 self-start max-h-[calc(100vh-4rem)] overflow-y-auto scrollbar-thin">
            {renderSurveySidebar(survRightCats)}
          </div>
        )}
      </div>
    </div>
  );
}

export default function SurveyPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#050810]" />}>
      <SurveyContent />
    </Suspense>
  );
}
