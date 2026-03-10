'use client';

import Link from 'next/link';
import NavBar from '@/components/NavBar';
import { useLocale } from '@/lib/locale-context';

const STRENGTHS = [
  {
    icon: '👥', title: '172,173 Census-Calibrated Agents', titleZh: '172,173 个人口普查校准智能体',
    desc: 'Age × income × housing × ethnicity × education × occupation × religion × planning area — IPF + Bayesian Network joint distribution matching, not randomly generated.',
    descZh: '年龄×收入×住房×种族×教育×职业×宗教×居住区域 — IPF+贝叶斯网络联合分布拟合，不是随机生成。',
  },
  {
    icon: '⚡', title: '5 Minutes, Not 4 Weeks', titleZh: '5 分钟，不是 4 周',
    desc: '1,000-person survey in 3-5 minutes. Traditional research: 2-4 weeks, $50K+.',
    descZh: '1,000 人调研 3-5 分钟。传统调研：2-4 周，$50K 以上。',
  },
  {
    icon: '🎯', title: '39-Dimension Targeting', titleZh: '39 维人群定向',
    desc: 'Low-income elderly Malay in Bedok? HDB 3-room young couples? Professional women aged 30-40? Filter across 39 demographic dimensions.',
    descZh: '勿洛区低收入马来老人？HDB 3房年轻夫妇？30-40 岁职业女性？39 个人口维度自由筛选。',
  },
  {
    icon: '🛡️', title: 'AI Quality Control', titleZh: 'AI 质量保障',
    desc: 'NVIDIA Nemotron-70B scores every response. Low-quality answers auto-flagged. 85%+ high quality rate.',
    descZh: 'NVIDIA Nemotron-70B 逐条评分，低质量回答自动标记，85%+ 高质量率。',
  },
];

const SCENARIOS = [
  {
    icon: '🏛️', title: 'Policy Preview', titleZh: '政策预演',
    example: 'If GST rises to 10%, how will residents react?',
    exampleZh: 'GST 涨到 10%，居民怎么反应？',
  },
  {
    icon: '🗳️', title: 'Election Polling', titleZh: '选举民调',
    example: 'Predict party support rates for the next election',
    exampleZh: '预测下次大选各党支持率',
  },
  {
    icon: '💰', title: 'Product Pricing', titleZh: '产品定价',
    example: 'Insurance premium +$300/yr — will customers cancel?',
    exampleZh: '保险涨价 $300/年，客户会退保吗？',
  },
  {
    icon: '🏷️', title: 'Brand Perception', titleZh: '品牌感知',
    example: 'New brand acceptance across ethnic groups',
    exampleZh: '新品牌在不同种族群体中的接受度',
  },
  {
    icon: '🎖️', title: 'Social Issues', titleZh: '社会议题',
    example: 'National Service satisfaction and reform attitudes',
    exampleZh: '国民服役制度满意度与改革态度',
  },
  {
    icon: '🏥', title: 'Healthcare', titleZh: '医疗健康',
    example: 'Telehealth adoption barriers among elderly',
    exampleZh: '远程医疗在老年群体中的接受障碍',
  },
];

const BACKTESTS = [
  { name: '2023 Presidential', nameZh: '2023 总统选举', mae: '2.7pp', color: 'text-green-400' },
  { name: 'Net Zero 2050', nameZh: '净零碳排 2050', mae: '2.9pp', color: 'text-green-400' },
  { name: 'GST 9% Impact', nameZh: 'GST 涨至 9%', mae: '4.3pp', color: 'text-green-400' },
  { name: 'GE 2025', nameZh: '2025 大选', mae: '6.2pp', color: 'text-yellow-400' },
  { name: 'Death Penalty', nameZh: '死刑态度', mae: '7.0pp', color: 'text-yellow-400' },
  { name: 'Racial Harmony', nameZh: '种族和谐', mae: '9.3pp', color: 'text-orange-400' },
  { name: 'Plastic Bag', nameZh: '塑料袋收费', mae: '9.3pp', color: 'text-orange-400' },
  { name: '377A Repeal', nameZh: '377A 废除', mae: '14.4pp', color: 'text-red-400' },
  { name: 'Insurance Channel', nameZh: '保险渠道', mae: '15.7pp', color: 'text-red-400' },
];

export default function HomePage() {
  const { locale } = useLocale();
  const zh = locale === 'zh';

  return (
    <div className="min-h-screen bg-[#050810] text-[#e2e8f0]">
      <NavBar />

      {/* Hero */}
      <div className="max-w-4xl mx-auto px-6 pt-16 pb-12 text-center">
        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-2xl font-bold mx-auto mb-6">S</div>
        <h1 className="text-4xl font-extrabold mb-4 bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent leading-tight">
          {zh ? <>新加坡数字孪生<br />172,173 个 AI 市民孪生智能体，5 分钟出结果</> : <>Singapore Digital Twin<br />172,173 AI Citizen Digital Twins, Results in 5 Min</>}
        </h1>
        <p className="text-lg text-[#94a3b8] max-w-2xl mx-auto mb-10">
          {zh
            ? '基于新加坡人口普查数据构建的全岛数字孪生。172,173 个 AI 市民孪生智能体，每人拥有完整人口统计画像，覆盖年龄、收入、住房、种族、教育等 39 个维度。9 项历史回测验证，中位 MAE 7.0pp。'
            : 'A city-scale digital twin built on Singapore census data. 172,173 AI citizen digital twins, each with a full demographic profile across 39 dimensions. Validated against 9 historical events, median MAE 7.0pp.'}
        </p>

        <div className="flex gap-4 justify-center mb-16">
          <Link href="/simulate" className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-base font-bold rounded-2xl hover:shadow-lg hover:shadow-blue-500/25 transition-all">
            {zh ? '社会模拟' : 'Social Simulation'}
            <span className="block text-xs font-normal opacity-80 mt-0.5">{zh ? '7 天 4 轮舆论演进模型' : '7-day 4-round opinion model'}</span>
          </Link>
          <Link href="/survey" className="px-8 py-4 bg-[#111827] border border-[#1e293b] text-[#e2e8f0] text-base font-bold rounded-2xl hover:border-blue-500/40 transition-all">
            {zh ? '市场调研' : 'Market Survey'}
            <span className="block text-xs font-normal text-[#64748b] mt-0.5">{zh ? '问卷 → 5 分钟出结果' : 'Questionnaire → Results in 5 min'}</span>
          </Link>
        </div>
      </div>

      {/* Strengths */}
      <div className="max-w-4xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-2 gap-4">
          {STRENGTHS.map((s, i) => (
            <div key={i} className="bg-[#111827] border border-[#1e293b] rounded-2xl p-6">
              <div className="text-2xl mb-3">{s.icon}</div>
              <h3 className="text-sm font-bold text-[#e2e8f0] mb-2">{zh ? s.titleZh : s.title}</h3>
              <p className="text-xs text-[#94a3b8] leading-relaxed">{zh ? s.descZh : s.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Scenarios */}
      <div className="max-w-4xl mx-auto px-6 pb-16">
        <h2 className="text-xl font-bold text-center mb-2">{zh ? '我们擅长的调研方向' : 'What We Do Best'}</h2>
        <p className="text-sm text-[#64748b] text-center mb-8">{zh ? '点击直接预填问卷，快速开始' : 'Click to pre-fill and start instantly'}</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {SCENARIOS.map((s, i) => (
            <Link key={i} href={`/survey?scenario=${i}`} className="bg-[#0d1117] border border-[#1e293b] rounded-2xl p-5 hover:border-blue-500/60 hover:bg-blue-500/5 transition-all group">
              <div className="text-2xl mb-2">{s.icon}</div>
              <div className="text-sm font-bold text-[#e2e8f0] group-hover:text-blue-300 mb-1">{zh ? s.titleZh : s.title}</div>
              <p className="text-xs text-[#64748b] leading-relaxed">{zh ? s.exampleZh : s.example}</p>
            </Link>
          ))}
        </div>
      </div>

      {/* Backtest strip */}
      <div className="border-t border-[#1e293b] bg-[#0a0e1a]/50">
        <div className="max-w-5xl mx-auto px-6 py-10">
          <h3 className="text-sm font-bold text-center text-[#94a3b8] mb-2 uppercase tracking-wider">{zh ? '9 项历史验证 — 全部公开' : '9 Backtests — Full Transparency'}</h3>
          <p className="text-[11px] text-[#475569] text-center mb-6">
            {zh
              ? '中位 MAE 7.0pp | 政策态度类 ≤5pp | 行为类/社会道德类偏差较大 — 系统提供方向性信号，不是精确预测'
              : 'Median MAE 7.0pp | Policy attitudes ≤5pp | Behavioral/social-moral topics show higher bias — directional signals, not precise predictions'}
          </p>
          <div className="flex justify-center gap-6 flex-wrap">
            {BACKTESTS.map((bt) => (
              <div key={bt.name} className="text-center min-w-[70px]">
                <div className={`text-base font-bold font-mono ${bt.color}`}>{bt.mae}</div>
                <div className="text-[10px] text-[#64748b] mt-0.5 leading-tight">{zh ? bt.nameZh : bt.name}</div>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-[#475569] text-center mt-5">
            MAE = Mean Absolute Error vs. real survey/election results.{' '}
            <span className="text-green-400/60">■</span> ≤5pp{' '}
            <span className="text-yellow-400/60">■</span> 5-10pp{' '}
            <span className="text-orange-400/60">■</span> 10-15pp{' '}
            <span className="text-red-400/60">■</span> &gt;15pp
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-[#1e293b] py-6 text-center text-[10px] text-[#475569]">
        <span>Powered by DeepSeek LLM · NVIDIA Nemotron-70B Reward Model · Census 2020 + GHS 2025 Calibrated Population · Supabase Cloud</span>
        <br />
        <span className="text-[#334155]">172,173 agents · 39 demographic dimensions · VS+RP simulation protocol · 9 validated backtests</span>
      </div>
    </div>
  );
}
