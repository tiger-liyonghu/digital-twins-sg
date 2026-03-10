'use client';

import { useState, useEffect } from 'react';
import NavBar from '@/components/NavBar';
import { useLocale } from '@/lib/locale-context';

// ═══════════════════════════════════════════════════════════════
// GHS 2025 / Census 2020 BENCHMARKS — ALL-AGE EQUIVALENT
//
// IMPORTANT: GHS reports education for 25+ and marital for 15+.
// Our synthetic population includes ALL ages (0-100), so we must
// convert benchmarks to all-age equivalents using age marginals.
//
// Age structure: 0-14 = 11.4%, 15+ = 88.6%, 25+ = 78.6%
// Children 0-14: 100% Single, education by age-deterministic CPT
// Youth 15-24: mixed education (secondary/poly/university)
//
// Sources: Population Trends 2025, GHS 2025, MOM 2025
// ═══════════════════════════════════════════════════════════════
const BENCHMARKS = {
  gender: { M: 0.486, F: 0.514 },
  ethnicity: { Chinese: 0.739, Malay: 0.135, Indian: 0.090, Others: 0.035 },
  housing_agg: { HDB: 0.772, Condo: 0.179, Landed: 0.047 },
  housing_detail: {
    // GHS 2025: HDB_1_2 7.3%, HDB_3 16.6%, HDB_4 31.2%, HDB_5_EC 22.1%
    HDB_1_2: 0.073, HDB_3: 0.166, HDB_4: 0.312,
    HDB_5_EC: 0.221, Condo: 0.179, Landed: 0.047,
  },
  // All-age education benchmark:
  // P(edu) = P(edu|age<25)*P(age<25) + P(edu|25+, GHS)*P(25+)
  // Children contribute deterministically: 0-4→NoFormal, 5-9→Primary,
  // 10-14→Secondary, 15-19→mixed, 20-24→mostly Uni/Poly
  // DB merges University+Postgraduate into 'University'
  education: {
    No_Formal: 0.114, Primary: 0.138, Secondary: 0.170,
    Post_Secondary: 0.196, Polytechnic: 0.107,
    University: 0.276,
  },
  income_band: {
    '0': 0.302, '1-1999': 0.080, '2000-3499': 0.126,
    '3500-4999': 0.151, '5000-6999': 0.149,
    '7000-9999': 0.103, '10000-14999': 0.056, '15000+': 0.032,
  },
  // All-age marital: GHS is 15+ (Single 30.4%, Married 58.9%)
  // All-age = GHS * 0.886, plus 0-14 are 100% Single
  marital: {
    Single: 0.383, Married: 0.522, Widowed: 0.043, Divorced: 0.051,
  },
  point_estimates: {
    median_age: 43.2,
    median_income: 5000,
    degree_plus_25: 0.38,
    married_30_34: 0.60,
  },
};

const SOURCES = [
  { name: 'Population Trends 2025', nameZh: '人口趋势 2025', org: 'SingStat', dims: 'Age, Gender, Ethnicity, Planning Area' },
  { name: 'General Household Survey 2025', nameZh: '住户综合调查 2025', org: 'SingStat', dims: 'Education, Housing, Income, Marital Status' },
  { name: 'MOM Labour Force Survey 2025', nameZh: 'MOM 劳动力调查 2025', org: 'MOM', dims: 'Income, Occupation, PMET Share' },
  { name: 'Key Household Income Trends 2025', nameZh: '住户收入趋势 2025', org: 'SingStat', dims: 'Income × Housing × Household Size' },
  { name: 'HDB Key Statistics 2024/2025', nameZh: 'HDB 关键统计 2024/2025', org: 'HDB', dims: 'Housing Type Distribution' },
];

// ═══════════════════════════════════════════════════════════════
// MATH: SRMSE, Chi-square, KL Divergence, Total Variation
// ═══════════════════════════════════════════════════════════════
function computeSRMSE(observed: Record<string, number>, benchmark: Record<string, number>): number {
  const total = Object.values(observed).reduce((s, v) => s + v, 0);
  if (total === 0) return 1;
  const keys = Object.keys(benchmark);
  let sumSqDev = 0;
  let meanTarget = 0;
  for (const k of keys) meanTarget += (benchmark[k] || 0);
  meanTarget /= keys.length;
  if (meanTarget === 0) return 1;

  for (const k of keys) {
    const obs = (observed[k] || 0) / total;
    const exp = benchmark[k] || 0;
    sumSqDev += (obs - exp) ** 2;
  }
  const rmse = Math.sqrt(sumSqDev / keys.length);
  return rmse / meanTarget;
}

function computeChiSquare(observed: Record<string, number>, benchmark: Record<string, number>): { chi2: number; df: number; pValue: string } {
  const total = Object.values(observed).reduce((s, v) => s + v, 0);
  const keys = Object.keys(benchmark);
  let chi2 = 0;
  for (const k of keys) {
    const obs = observed[k] || 0;
    const exp = (benchmark[k] || 0) * total;
    if (exp > 0) chi2 += (obs - exp) ** 2 / exp;
  }
  const df = keys.length - 1;
  // Approximate p-value using Wilson-Hilferty for large chi2
  if (df <= 0) return { chi2, df, pValue: 'N/A' };
  const z = Math.pow(chi2 / df, 1 / 3) - (1 - 2 / (9 * df));
  const denom = Math.sqrt(2 / (9 * df));
  const zScore = z / denom;
  // For large N, chi2 is always "significant" — focus on effect size
  return { chi2: Math.round(chi2), df, pValue: zScore > 3.3 ? '<0.001' : zScore > 2.6 ? '<0.01' : zScore > 2 ? '<0.05' : '>0.05' };
}

function computeKL(observed: Record<string, number>, benchmark: Record<string, number>): number {
  const total = Object.values(observed).reduce((s, v) => s + v, 0);
  if (total === 0) return Infinity;
  const keys = Object.keys(benchmark);
  let kl = 0;
  for (const k of keys) {
    const p = Math.max((observed[k] || 0) / total, 1e-10);
    const q = Math.max(benchmark[k] || 0, 1e-10);
    kl += p * Math.log(p / q);
  }
  return kl;
}

function computeTV(observed: Record<string, number>, benchmark: Record<string, number>): number {
  const total = Object.values(observed).reduce((s, v) => s + v, 0);
  if (total === 0) return 1;
  const keys = Object.keys(benchmark);
  let tv = 0;
  for (const k of keys) {
    tv += Math.abs((observed[k] || 0) / total - (benchmark[k] || 0));
  }
  return tv / 2;
}

function srmseGrade(srmse: number): { label: string; labelZh: string; color: string } {
  if (srmse < 0.05) return { label: 'Excellent', labelZh: '优秀', color: 'text-green-400' };
  if (srmse < 0.10) return { label: 'Good', labelZh: '良好', color: 'text-green-400' };
  if (srmse < 0.20) return { label: 'Acceptable', labelZh: '可接受', color: 'text-yellow-400' };
  return { label: 'Poor', labelZh: '不佳', color: 'text-red-400' };
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════
interface PopData {
  total: number;
  median_age: number;
  median_income: number;
  marginals: Record<string, Record<string, number>>;
  joints: Record<string, Record<string, Record<string, number>>>;
}

export default function DataPage() {
  const { locale } = useLocale();
  const zh = locale === 'zh';

  const [data, setData] = useState<PopData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'marginal' | 'joint' | 'metrics' | 'method'>('marginal');

  useEffect(() => {
    fetch('/data/population-stats.json')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => { setError('Failed to load'); setLoading(false); });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050810] text-[#e2e8f0]">
        <NavBar />
        <div className="flex items-center justify-center py-32">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full border-2 border-blue-500 border-t-transparent animate-spin mx-auto mb-4" />
            <p className="text-sm text-[#64748b]">{zh ? '正在从 Supabase 加载 172,173 个 agent 分布数据...' : 'Loading distribution data for 172,173 agents from Supabase...'}</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-[#050810] text-[#e2e8f0]">
        <NavBar />
        <div className="max-w-3xl mx-auto px-6 py-20 text-center">
          <p className="text-red-400">{error || 'No data'}</p>
        </div>
      </div>
    );
  }

  const total = data.total;

  // Aggregate housing for benchmark comparison
  const housingObs = data.marginals.housing_type || {};
  const housingAgg: Record<string, number> = {
    HDB: (housingObs['HDB_1_2'] || 0) + (housingObs['HDB_3'] || 0) + (housingObs['HDB_4'] || 0) + (housingObs['HDB_5_EC'] || 0),
    Condo: housingObs['Condo'] || 0,
    Landed: housingObs['Landed'] || 0,
  };

  // Compute all metrics
  const dimensions: {
    key: string; label: string; labelZh: string;
    observed: Record<string, number>;
    benchmark: Record<string, number>;
    labelMap?: Record<string, string>;
  }[] = [
    { key: 'gender', label: 'Gender', labelZh: '性别', observed: data.marginals.gender, benchmark: BENCHMARKS.gender },
    { key: 'ethnicity', label: 'Ethnicity', labelZh: '种族', observed: data.marginals.ethnicity, benchmark: BENCHMARKS.ethnicity },
    { key: 'housing_agg', label: 'Housing (Aggregate)', labelZh: '住房类型（汇总）', observed: housingAgg, benchmark: BENCHMARKS.housing_agg },
    { key: 'housing_detail', label: 'Housing (Detail)', labelZh: '住房类型（细分）', observed: data.marginals.housing_type, benchmark: BENCHMARKS.housing_detail },
    { key: 'education', label: 'Education', labelZh: '教育程度', observed: data.marginals.education_level, benchmark: BENCHMARKS.education,
      labelMap: { No_Formal: zh ? '无学历' : 'No Formal', Primary: zh ? '小学' : 'Primary', Secondary: zh ? '中学' : 'Secondary', Post_Secondary: zh ? '大专' : 'Post Sec', Polytechnic: zh ? '理工' : 'Poly', University: zh ? '大学+研究生' : 'Uni+PG' },
    },
    { key: 'income', label: 'Income Band', labelZh: '收入档次', observed: data.marginals.income_band, benchmark: BENCHMARKS.income_band },
    { key: 'marital', label: 'Marital Status', labelZh: '婚姻状况', observed: data.marginals.marital_status, benchmark: BENCHMARKS.marital },
  ];

  const metricRows = dimensions.map(d => {
    const srmse = computeSRMSE(d.observed, d.benchmark);
    const chi = computeChiSquare(d.observed, d.benchmark);
    const kl = computeKL(d.observed, d.benchmark);
    const tv = computeTV(d.observed, d.benchmark);
    const grade = srmseGrade(srmse);
    return { ...d, srmse, chi2: chi.chi2, df: chi.df, pValue: chi.pValue, kl, tv, grade };
  });

  // Point estimate deviations
  const pointEstimates = [
    {
      label: zh ? '中位年龄' : 'Median Age',
      actual: data.median_age,
      target: BENCHMARKS.point_estimates.median_age,
      unit: zh ? '岁' : 'yrs',
    },
    {
      label: zh ? '中位收入（就业者）' : 'Median Income (employed)',
      actual: data.median_income,
      target: BENCHMARKS.point_estimates.median_income,
      unit: 'S$',
    },
  ];

  return (
    <div className="min-h-screen bg-[#050810] text-[#e2e8f0]">
      <NavBar />

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold mb-2">
            {zh ? '人口数据质量 — 数学验证' : 'Population Data Quality — Mathematical Validation'}
          </h1>
          <p className="text-sm text-[#64748b] max-w-3xl">
            {zh
              ? `172,173 个 AI 市民孪生智能体的人口统计分布，与 GHS 2025 / Census 2020 基准对标。每个维度计算 SRMSE、χ² 检验、KL 散度和全变差距离。`
              : `Demographic distributions of 172,173 AI citizen digital twins, benchmarked against GHS 2025 / Census 2020. Each dimension is evaluated with SRMSE, χ² test, KL divergence, and Total Variation distance.`}
          </p>
          <div className="flex flex-wrap gap-3 sm:gap-4 mt-4">
            <div className="bg-[#111827] border border-[#1e293b] rounded-xl px-4 py-2">
              <div className="text-xs text-[#64748b]">{zh ? '智能体总数' : 'Total Agents'}</div>
              <div className="text-lg font-bold font-mono text-blue-400">{total.toLocaleString()}</div>
            </div>
            {pointEstimates.map((pe, i) => {
              const dev = ((pe.actual - pe.target) / pe.target * 100).toFixed(1);
              const devNum = Math.abs(pe.actual - pe.target) / pe.target;
              return (
                <div key={i} className="bg-[#111827] border border-[#1e293b] rounded-xl px-4 py-2">
                  <div className="text-xs text-[#64748b]">{pe.label}</div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-lg font-bold font-mono text-[#e2e8f0]">{pe.unit === 'S$' ? `S$${pe.actual.toLocaleString()}` : pe.actual}</span>
                    <span className="text-xs text-[#64748b]">vs {pe.unit === 'S$' ? `S$${pe.target.toLocaleString()}` : pe.target}</span>
                    <span className={`text-xs font-mono ${devNum < 0.05 ? 'text-green-400' : devNum < 0.10 ? 'text-yellow-400' : 'text-orange-400'}`}>
                      ({dev}%)
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Tabs */}
        <div className="flex overflow-x-auto border-b border-[#1e293b] mb-6">
          {[
            { key: 'marginal' as const, label: zh ? '边缘分布' : 'Marginal Distributions' },
            { key: 'joint' as const, label: zh ? '联合分布' : 'Joint Distributions' },
            { key: 'metrics' as const, label: zh ? '统计检验' : 'Statistical Tests' },
            { key: 'method' as const, label: zh ? '方法论' : 'Methodology' },
          ].map(t => (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
              className={`px-5 py-2.5 text-sm font-semibold transition-all ${
                activeTab === t.key ? 'text-blue-400 border-b-2 border-blue-400' : 'text-[#475569] hover:text-[#94a3b8]'
              }`}>{t.label}</button>
          ))}
        </div>

        {/* ═══ MARGINAL DISTRIBUTIONS ═══ */}
        {activeTab === 'marginal' && (
          <div className="space-y-8">
            {metricRows.map(dim => {
              const obsTotal = Object.values(dim.observed).reduce((s, v) => s + v, 0);
              const sortedKeys = Object.keys(dim.benchmark).sort(
                (a, b) => (dim.benchmark[b] || 0) - (dim.benchmark[a] || 0)
              );

              return (
                <div key={dim.key} className="bg-[#111827] border border-[#1e293b] rounded-2xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-base font-bold">{zh ? dim.labelZh : dim.label}</h3>
                      <span className="text-xs text-[#64748b]">n = {obsTotal.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="text-[10px] text-[#64748b] uppercase">SRMSE</div>
                        <div className={`text-sm font-bold font-mono ${dim.grade.color}`}>
                          {dim.srmse.toFixed(4)}
                        </div>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-lg font-semibold ${
                        dim.grade.color.replace('text-', 'bg-').replace('400', '500/10')
                      } ${dim.grade.color}`}>
                        {zh ? dim.grade.labelZh : dim.grade.label}
                      </span>
                    </div>
                  </div>

                  {/* Bar comparison */}
                  <div className="space-y-2 overflow-x-auto">
                    {sortedKeys.map(k => {
                      const obsPct = obsTotal > 0 ? (dim.observed[k] || 0) / obsTotal : 0;
                      const expPct = dim.benchmark[k] || 0;
                      const maxPct = Math.max(obsPct, expPct, 0.01);
                      const deviation = expPct > 0 ? ((obsPct - expPct) / expPct * 100) : 0;
                      const displayLabel = dim.labelMap?.[k] || k;

                      return (
                        <div key={k} className="grid grid-cols-[120px_1fr_80px_80px_60px] items-center gap-2 min-w-[600px]">
                          <div className="text-xs text-[#94a3b8] truncate">{displayLabel}</div>
                          <div className="relative h-5">
                            {/* Benchmark bar (outline) */}
                            <div className="absolute inset-y-0 left-0 border border-dashed border-[#475569] rounded-sm"
                              style={{ width: `${(expPct / maxPct) * 100}%` }} />
                            {/* Observed bar (filled) */}
                            <div className={`absolute inset-y-0 left-0 rounded-sm ${
                              Math.abs(deviation) < 5 ? 'bg-green-500/40' : Math.abs(deviation) < 15 ? 'bg-yellow-500/40' : 'bg-orange-500/40'
                            }`} style={{ width: `${(obsPct / maxPct) * 100}%` }} />
                          </div>
                          <div className="text-xs font-mono text-right text-[#e2e8f0]">{(obsPct * 100).toFixed(1)}%</div>
                          <div className="text-xs font-mono text-right text-[#64748b]">{(expPct * 100).toFixed(1)}%</div>
                          <div className={`text-xs font-mono text-right ${
                            Math.abs(deviation) < 5 ? 'text-green-400' : Math.abs(deviation) < 15 ? 'text-yellow-400' : 'text-orange-400'
                          }`}>
                            {deviation > 0 ? '+' : ''}{deviation.toFixed(1)}%
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Legend */}
                  <div className="flex gap-4 mt-3 text-[10px] text-[#475569]">
                    <span className="flex items-center gap-1">
                      <span className="w-3 h-2 rounded-sm bg-green-500/40 inline-block" /> {zh ? '合成人口' : 'Synthetic'}
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-3 h-2 rounded-sm border border-dashed border-[#475569] inline-block" /> {zh ? 'GHS 2025 基准' : 'GHS 2025 Benchmark'}
                    </span>
                    <span className="ml-auto">
                      {zh ? '偏差' : 'Deviation'}: <span className="text-green-400">&lt;5%</span> / <span className="text-yellow-400">5-15%</span> / <span className="text-orange-400">&gt;15%</span>
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ═══ JOINT DISTRIBUTIONS ═══ */}
        {activeTab === 'joint' && (
          <div className="space-y-8">
            {/* Ethnicity × Education */}
            <div className="bg-[#111827] border border-[#1e293b] rounded-2xl p-6">
              <h3 className="text-base font-bold mb-1">{zh ? '种族 × 教育程度' : 'Ethnicity × Education'}</h3>
              <p className="text-xs text-[#64748b] mb-4">
                {zh ? 'P(education | ethnicity) — 条件分布，行内归一化' : 'P(education | ethnicity) — Conditional distribution, row-normalized'}
              </p>
              <JointTable
                data={data.joints.ethnicity_education}
                rowOrder={['Chinese', 'Malay', 'Indian', 'Others']}
                colOrder={['No_Formal', 'Primary', 'Secondary', 'Post_Secondary', 'Polytechnic', 'University', 'Postgraduate']}
                colLabels={zh
                  ? { No_Formal: '无学历', Primary: '小学', Secondary: '中学', Post_Secondary: '大专', Polytechnic: '理工', University: '大学', Postgraduate: '研究生' }
                  : undefined}
              />
            </div>

            {/* Housing × Income */}
            <div className="bg-[#111827] border border-[#1e293b] rounded-2xl p-6">
              <h3 className="text-base font-bold mb-1">{zh ? '住房类型 × 收入档次' : 'Housing Type × Income Band'}</h3>
              <p className="text-xs text-[#64748b] mb-4">
                {zh ? 'P(income | housing) — 住房与收入的联合分布' : 'P(income | housing) — Joint distribution of housing and income'}
              </p>
              <JointTable
                data={data.joints.housing_income}
                rowOrder={['HDB_1_2', 'HDB_3', 'HDB_4', 'HDB_5_EC', 'Condo', 'Landed']}
                colOrder={['0', '1-1999', '2000-3499', '3500-4999', '5000-6999', '7000-9999', '10000-14999', '15000+']}
                rowLabels={{ HDB_1_2: 'HDB 1-2R', HDB_3: 'HDB 3R', HDB_4: 'HDB 4R', HDB_5_EC: 'HDB 5R/EC' }}
              />
            </div>

            {/* Gender × Income */}
            <div className="bg-[#111827] border border-[#1e293b] rounded-2xl p-6">
              <h3 className="text-base font-bold mb-1">{zh ? '性别 × 收入档次' : 'Gender × Income Band'}</h3>
              <p className="text-xs text-[#64748b] mb-4">
                {zh ? 'P(income | gender) — 性别收入差异' : 'P(income | gender) — Gender income gap analysis'}
              </p>
              <JointTable
                data={data.joints.gender_income}
                rowOrder={['M', 'F']}
                colOrder={['0', '1-1999', '2000-3499', '3500-4999', '5000-6999', '7000-9999', '10000-14999', '15000+']}
                rowLabels={{ M: zh ? '男' : 'Male', F: zh ? '女' : 'Female' }}
              />
            </div>
          </div>
        )}

        {/* ═══ STATISTICAL TESTS ═══ */}
        {activeTab === 'metrics' && (
          <div className="space-y-6">
            {/* Summary table */}
            <div className="bg-[#111827] border border-[#1e293b] rounded-2xl p-6">
              <h3 className="text-base font-bold mb-4">
                {zh ? '全维度统计检验汇总' : 'Statistical Test Summary — All Dimensions'}
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-[#64748b] border-b border-[#1e293b]">
                      <th className="text-left py-2 pr-4">{zh ? '维度' : 'Dimension'}</th>
                      <th className="text-right py-2 px-2">SRMSE</th>
                      <th className="text-right py-2 px-2">{zh ? '评级' : 'Grade'}</th>
                      <th className="text-right py-2 px-2">χ²</th>
                      <th className="text-right py-2 px-2">df</th>
                      <th className="text-right py-2 px-2">p-value</th>
                      <th className="text-right py-2 px-2">KL(P‖Q)</th>
                      <th className="text-right py-2 px-2">TV</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metricRows.map(m => (
                      <tr key={m.key} className="border-b border-[#1e293b]/50">
                        <td className="py-2.5 pr-4 font-medium text-[#e2e8f0]">{zh ? m.labelZh : m.label}</td>
                        <td className={`py-2.5 px-2 text-right font-mono ${m.grade.color}`}>{m.srmse.toFixed(4)}</td>
                        <td className={`py-2.5 px-2 text-right font-semibold ${m.grade.color}`}>{zh ? m.grade.labelZh : m.grade.label}</td>
                        <td className="py-2.5 px-2 text-right font-mono text-[#94a3b8]">{m.chi2.toLocaleString()}</td>
                        <td className="py-2.5 px-2 text-right font-mono text-[#64748b]">{m.df}</td>
                        <td className="py-2.5 px-2 text-right font-mono text-[#94a3b8]">{m.pValue}</td>
                        <td className="py-2.5 px-2 text-right font-mono text-[#94a3b8]">{m.kl.toFixed(5)}</td>
                        <td className="py-2.5 px-2 text-right font-mono text-[#94a3b8]">{m.tv.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Metric explanations */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                {
                  name: 'SRMSE',
                  full: 'Standardized Root Mean Squared Error',
                  formula: '√(Σ(pᵢ − qᵢ)² / k) / q̄',
                  desc: zh
                    ? '衡量合成分布与基准分布之间的标准化偏差。< 0.05 优秀，< 0.10 良好，< 0.20 可接受。'
                    : 'Normalized deviation between synthetic and benchmark distributions. <0.05 excellent, <0.10 good, <0.20 acceptable.',
                  ref: 'Voas & Williamson (2001)',
                },
                {
                  name: 'χ² Test',
                  full: 'Pearson Chi-Square Goodness of Fit',
                  formula: 'Σ (Oᵢ − Eᵢ)² / Eᵢ',
                  desc: zh
                    ? '检验合成分布是否来自基准分布。注意：大样本（N=172K）下几乎总是"显著"，因此关注效应量（SRMSE）比 p 值更有意义。'
                    : 'Tests if synthetic matches benchmark. Note: with N=172K, almost always "significant" — effect size (SRMSE) matters more than p-value.',
                  ref: 'Pearson (1900)',
                },
                {
                  name: 'KL Divergence',
                  full: 'Kullback-Leibler Divergence',
                  formula: 'Σ pᵢ · log(pᵢ / qᵢ)',
                  desc: zh
                    ? '信息论度量：合成分布 P 相对于基准分布 Q 的信息损失（bits）。KL = 0 表示完全匹配。'
                    : 'Information-theoretic measure: information loss of synthetic P relative to benchmark Q (bits). KL=0 means perfect match.',
                  ref: 'Kullback & Leibler (1951)',
                },
                {
                  name: 'TV Distance',
                  full: 'Total Variation Distance',
                  formula: '½ Σ |pᵢ − qᵢ|',
                  desc: zh
                    ? '两个分布之间最大可能的事件概率差异。范围 [0,1]，0 为完全匹配，1 为完全不相交。'
                    : 'Maximum possible difference in event probability between two distributions. Range [0,1], 0=perfect match, 1=disjoint.',
                  ref: 'Tsybakov (2009)',
                },
              ].map((m, i) => (
                <div key={i} className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-4">
                  <div className="text-sm font-bold text-blue-400 mb-1">{m.name}</div>
                  <div className="text-[10px] text-[#64748b] mb-2">{m.full}</div>
                  <div className="font-mono text-xs text-[#94a3b8] bg-[#111827] rounded px-2 py-1 mb-2 inline-block">{m.formula}</div>
                  <p className="text-xs text-[#94a3b8] leading-relaxed">{m.desc}</p>
                  <div className="text-[10px] text-[#475569] mt-2">{m.ref}</div>
                </div>
              ))}
            </div>

            {/* SRMSE threshold reference */}
            <div className="bg-[#111827] border border-[#1e293b] rounded-2xl p-5">
              <h3 className="text-sm font-bold mb-3">
                {zh ? 'SRMSE 评级标准 (Voas & Williamson, 2001)' : 'SRMSE Grading Scale (Voas & Williamson, 2001)'}
              </h3>
              <div className="flex flex-wrap gap-3 sm:gap-6">
                {[
                  { range: '< 0.05', grade: zh ? '优秀' : 'Excellent', color: 'text-green-400', bg: 'bg-green-500/10' },
                  { range: '0.05 – 0.10', grade: zh ? '良好' : 'Good', color: 'text-green-400', bg: 'bg-green-500/10' },
                  { range: '0.10 – 0.20', grade: zh ? '可接受' : 'Acceptable', color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
                  { range: '> 0.20', grade: zh ? '不佳' : 'Poor', color: 'text-red-400', bg: 'bg-red-500/10' },
                ].map((s, i) => (
                  <div key={i} className={`${s.bg} rounded-lg px-4 py-2 text-center flex-1`}>
                    <div className={`text-sm font-bold font-mono ${s.color}`}>{s.range}</div>
                    <div className={`text-xs ${s.color}`}>{s.grade}</div>
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-[#475569] mt-3">
                {zh
                  ? '参考标准来自 Voas & Williamson (2001) "Evaluating Goodness-of-Fit Measures for Synthetic Microdata"，被广泛用于合成人口验证。'
                  : 'Reference: Voas & Williamson (2001) "Evaluating Goodness-of-Fit Measures for Synthetic Microdata", widely used in synthetic population validation.'}
              </p>
            </div>
          </div>
        )}

        {/* ═══ METHODOLOGY ═══ */}
        {activeTab === 'method' && (
          <div className="space-y-6">
            {/* Synthesis pipeline */}
            <div className="bg-[#111827] border border-[#1e293b] rounded-2xl p-6">
              <h3 className="text-base font-bold mb-4">{zh ? '合成人口生成流水线' : 'Synthesis Pipeline'}</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 text-center mb-6">
                {[
                  { step: '1', label: zh ? '边缘分布' : 'Marginals', desc: zh ? 'GHS 2025 数据' : 'GHS 2025 data', icon: '📊' },
                  { step: '2', label: zh ? 'CPT 构建' : 'CPT Build', desc: zh ? '条件概率表' : 'Conditional prob tables', icon: '🔢' },
                  { step: '3', label: 'IPF', desc: zh ? '迭代比例拟合' : 'Iterative Proportional Fitting', icon: '⚙️' },
                  { step: '4', label: zh ? '贝叶斯网络' : 'Bayes Net', desc: zh ? '联合分布采样' : 'Joint distribution sampling', icon: '🧮' },
                  { step: '5', label: zh ? '质量门控' : 'Quality Gate', desc: 'SRMSE < 0.20', icon: '🛡️' },
                ].map((s, i) => (
                  <div key={i} className="flex flex-col items-center">
                    <div className="text-2xl mb-2">{s.icon}</div>
                    <div className="text-xs font-bold text-[#e2e8f0]">{s.label}</div>
                    <div className="text-[10px] text-[#64748b] mt-0.5">{s.desc}</div>
                    {i < 4 && <div className="text-[#475569] mt-1">→</div>}
                  </div>
                ))}
              </div>

              <div className="space-y-3">
                <div className="bg-[#0d1117] rounded-xl p-4">
                  <div className="text-xs font-bold text-blue-400 mb-1">{zh ? '步骤 1-2：边缘分布 + 条件概率表' : 'Step 1-2: Marginals + CPT'}</div>
                  <p className="text-xs text-[#94a3b8]">
                    {zh
                      ? '从 GHS 2025 提取 21 个年龄组、4 个种族、7 个教育层次、8 个收入档的边缘分布。构建 P(education|age)、P(income|education,age)、P(housing|income)、P(marital|age,gender) 等条件概率表。'
                      : 'Extract marginal distributions: 21 age groups, 4 ethnicities, 7 education levels, 8 income bands from GHS 2025. Build CPTs: P(education|age), P(income|education,age), P(housing|income), P(marital|age,gender).'}
                  </p>
                </div>
                <div className="bg-[#0d1117] rounded-xl p-4">
                  <div className="text-xs font-bold text-blue-400 mb-1">{zh ? '步骤 3：迭代比例拟合 (IPF)' : 'Step 3: Iterative Proportional Fitting (IPF)'}</div>
                  <p className="text-xs text-[#94a3b8]">
                    {zh
                      ? 'Deming-Stephan 算法：给定多维度边缘约束，迭代调整联合分布直到所有边缘同时满足。保证数学收敛（Csiszár, 1975）。我们使用 6 维 IPF：age × gender × ethnicity × education × housing × planning_area。'
                      : 'Deming-Stephan algorithm: given multi-dimensional marginal constraints, iteratively adjust joint distribution until all marginals satisfied. Guaranteed convergence (Csiszár, 1975). We use 6-dimensional IPF: age × gender × ethnicity × education × housing × planning_area.'}
                  </p>
                </div>
                <div className="bg-[#0d1117] rounded-xl p-4">
                  <div className="text-xs font-bold text-blue-400 mb-1">{zh ? '步骤 4：贝叶斯网络采样' : 'Step 4: Bayesian Network Sampling'}</div>
                  <p className="text-xs text-[#94a3b8]">
                    {zh
                      ? 'IPF 输出作为先验，用贝叶斯网络的 DAG 结构（age → education → income → housing 等因果链）逐维采样。高斯 Copula 处理连续变量间的非线性相关。'
                      : 'IPF output serves as prior. Bayesian network DAG structure (age → education → income → housing causal chain) samples dimension by dimension. Gaussian Copula handles non-linear correlations between continuous variables.'}
                  </p>
                </div>
                <div className="bg-[#0d1117] rounded-xl p-4">
                  <div className="text-xs font-bold text-blue-400 mb-1">{zh ? '步骤 5：质量门控' : 'Step 5: Quality Gate'}</div>
                  <p className="text-xs text-[#94a3b8]">
                    {zh
                      ? '硬门控（必须通过）：性别、种族、年龄、家庭规模分布 SRMSE < 0.10。软门控（允许警告）：教育、住房、收入、性格 SRMSE < 0.20。隐私检查：k-匿名性 ≥ 5。如果任何硬门控失败，自动重新合成。'
                      : 'Hard gates (must pass): gender, ethnicity, age, household size SRMSE < 0.10. Soft gates (warning): education, housing, income, personality SRMSE < 0.20. Privacy: k-anonymity ≥ 5. Auto re-synthesize on hard gate failure.'}
                  </p>
                </div>
              </div>
            </div>

            {/* Data sources */}
            <div className="bg-[#111827] border border-[#1e293b] rounded-2xl p-6">
              <h3 className="text-base font-bold mb-4">{zh ? '数据来源' : 'Data Sources'}</h3>
              <div className="space-y-2">
                {SOURCES.map((s, i) => (
                  <div key={i} className="flex items-center gap-3 bg-[#0d1117] rounded-xl px-4 py-3">
                    <span className="text-xs font-bold text-blue-400 bg-blue-500/10 rounded-lg px-2 py-1">{s.org}</span>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-[#e2e8f0]">{zh ? s.nameZh : s.name}</div>
                      <div className="text-[10px] text-[#64748b]">{zh ? '覆盖维度' : 'Dimensions'}: {s.dims}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 39 dimensions */}
            <div className="bg-[#111827] border border-[#1e293b] rounded-2xl p-6">
              <h3 className="text-base font-bold mb-3">{zh ? '39 维人口统计画像' : '39-Dimension Demographic Profile'}</h3>
              <p className="text-xs text-[#64748b] mb-4">
                {zh ? '每个 AI 市民孪生智能体拥有以下完整画像：' : 'Each AI citizen digital twin has a complete profile across:'}
              </p>
              <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
                {[
                  'Age', 'Age Group', 'Gender', 'Ethnicity', 'Residency', 'Planning Area',
                  'Education', 'Occupation', 'Industry', 'Monthly Income', 'Income Band',
                  'Housing Type', 'Health Status', 'Marital Status', 'Household ID', 'Num Children',
                  'Big Five: O', 'Big Five: C', 'Big Five: E', 'Big Five: A', 'Big Five: N',
                  'Risk Appetite', 'Political Leaning', 'Social Trust', 'Religious Devotion',
                  'Life Phase', 'Is Alive', 'Media Diet', 'Social Media', 'Dialect Group',
                  'Data Source', 'Religion',
                ].map((dim, i) => (
                  <div key={i} className="text-xs text-[#94a3b8] bg-[#0d1117] rounded-lg px-3 py-1.5 text-center border border-[#1e293b]">
                    {dim}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-12 border-t border-[#1e293b] py-6 text-center">
          <p className="text-[10px] text-[#475569]">
            {zh
              ? `数据来源：GHS 2025 / Census 2020 / MOM 2025 | 合成方法：IPF + 贝叶斯网络 + 高斯 Copula | 验证标准：Voas & Williamson (2001) SRMSE | ${total.toLocaleString()} 个智能体 × 39 维`
              : `Sources: GHS 2025 / Census 2020 / MOM 2025 | Method: IPF + Bayesian Network + Gaussian Copula | Validation: Voas & Williamson (2001) SRMSE | ${total.toLocaleString()} agents × 39 dimensions`}
          </p>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// Joint distribution heatmap table
// ═══════════════════════════════════════════════════════════════
function JointTable({ data, rowOrder, colOrder, rowLabels, colLabels }: {
  data: Record<string, Record<string, number>>;
  rowOrder: string[];
  colOrder: string[];
  rowLabels?: Record<string, string>;
  colLabels?: Record<string, string>;
}) {
  // Compute row totals for normalization
  const rowTotals: Record<string, number> = {};
  for (const r of rowOrder) {
    rowTotals[r] = 0;
    for (const c of colOrder) {
      rowTotals[r] += data[r]?.[c] || 0;
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-[#64748b] border-b border-[#1e293b]">
            <th className="text-left py-2 pr-2" />
            {colOrder.map(c => (
              <th key={c} className="text-right py-2 px-1.5 font-medium whitespace-nowrap">
                {colLabels?.[c] || c}
              </th>
            ))}
            <th className="text-right py-2 px-1.5 text-[#475569]">n</th>
          </tr>
        </thead>
        <tbody>
          {rowOrder.filter(r => rowTotals[r] > 0).map(r => (
            <tr key={r} className="border-b border-[#1e293b]/30">
              <td className="py-2 pr-2 font-medium text-[#94a3b8] whitespace-nowrap">{rowLabels?.[r] || r}</td>
              {colOrder.map(c => {
                const count = data[r]?.[c] || 0;
                const pct = rowTotals[r] > 0 ? count / rowTotals[r] : 0;
                // Heat color intensity based on percentage
                const intensity = Math.min(pct * 3, 1); // max at ~33%
                return (
                  <td key={c} className="py-2 px-1.5 text-right font-mono"
                    style={{
                      backgroundColor: `rgba(59, 130, 246, ${intensity * 0.3})`,
                      color: pct > 0.25 ? '#93c5fd' : pct > 0.10 ? '#94a3b8' : '#475569',
                    }}>
                    {(pct * 100).toFixed(1)}%
                  </td>
                );
              })}
              <td className="py-2 px-1.5 text-right font-mono text-[#475569]">
                {rowTotals[r].toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
