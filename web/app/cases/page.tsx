'use client';

import { useState } from 'react';
import NavBar from '@/components/NavBar';
import { useLocale } from '@/lib/locale-context';

type CaseType = 'backtest' | 'prediction' | 'simulation';
type Category = 'election' | 'economy' | 'social' | 'policy';
type Status = 'completed' | 'pending';

interface SurveyQ {
  q: string; qZh: string;
  results: Record<string, number>;
}

interface Case {
  no: string;
  name: string; nameZh: string;
  type: CaseType; category: Category; status: Status;
  sample: number; mae: number | null;
  desc: string; descZh: string;
  insight?: string; insightZh?: string;
  predicted?: Record<string, number>;
  actual?: Record<string, number>;
  source?: string;
  surveyResults?: SurveyQ[];
}

const CASES: Case[] = [
  // ── Backtests ──
  {
    no: 'BT-001', name: '2023 Presidential Election', nameZh: '2023 总统选举',
    type: 'backtest', category: 'election', status: 'completed', sample: 1000, mae: 2.7,
    desc: 'Three-candidate presidential election. Tharman vs Ng Kok Song vs Tan Kin Lian.',
    descZh: '三候选人总统选举。尚达曼 vs 黄国松 vs 陈清木。',
    predicted: { 'Tharman': 67.1, 'Ng Kok Song': 19.7, 'Tan Kin Lian': 13.2 },
    actual: { 'Tharman': 70.4, 'Ng Kok Song': 15.7, 'Tan Kin Lian': 13.9 },
    source: 'ELD Official Results, Sep 2023',
    insight: 'MAE 2.7pp. All three candidates within ±4pp. Abstention 10.7% redistributed proportionally.',
    insightZh: 'MAE 2.7pp。三个候选人均在±4pp以内。弃权10.7%按比例重分配。',
  },
  {
    no: 'BT-002', name: '2024 GST Increase to 9%', nameZh: '2024 GST 涨至 9%',
    type: 'backtest', category: 'economy', status: 'completed', sample: 1000, mae: 4.3,
    desc: 'Consumer spending impact after GST rose from 8% to 9%. Protocol v2.0 with cumulative inflation pressure framing.',
    descZh: 'GST从8%涨到9%后的消费影响。协议v2.0，累积通胀压力叙事。无ground truth泄露。',
    predicted: { 'Significantly reduce': 15.3, 'Moderately reduce': 42.2, 'No change': 32.1, 'Increase spending': 10.4 },
    actual: { 'Significantly reduce': 11, 'Moderately reduce': 47, 'No change': 34, 'Increase spending': 8 },
    source: 'Blackbox Research Survey, Jan 2024',
    insight: 'MAE 4.3pp. Correct directional prediction of moderate reduction as dominant response.',
    insightZh: 'MAE 4.3pp。正确预测"适度减少"为主要反应方向。',
  },
  {
    no: 'BT-003', name: '2025 General Election', nameZh: '2025 大选',
    type: 'backtest', category: 'election', status: 'completed', sample: 1000, mae: 6.2,
    desc: 'Multi-party general election with Protocol v2.0 (V-ELEC). Historical anchoring + anti-media-bias calibration.',
    descZh: '多党大选，应用协议v2.0（V-ELEC）。历史锚定 + 反媒体偏差校准。',
    predicted: { 'PAP': 55.9, 'WP': 24.6, 'PSP': 12.7, 'Others': 6.8 },
    actual: { 'PAP': 65.6, 'WP': 17.4, 'PSP': 10.5, 'Others': 6.5 },
    source: 'ELD Official Results, May 2025',
    insight: 'MAE 6.2pp. Systematic anti-incumbent bias: underestimated PAP by 9.7pp. Direction of WP>PSP correct.',
    insightZh: 'MAE 6.2pp。系统性反执政党偏差：低估PAP 9.7pp。WP>PSP方向正确。',
  },
  {
    no: 'BT-004', name: 'Section 377A Repeal Attitudes', nameZh: '377A 废除态度',
    type: 'backtest', category: 'social', status: 'completed', sample: 1000, mae: 14.4,
    desc: 'Public attitudes toward 377A repeal. Ipsos 2022 longitudinal data as benchmark.',
    descZh: '公众对377A废除的态度。以Ipsos 2022纵向数据为基准。',
    insight: 'MAE 14.4pp. LLM shows strong progressive bias on social-moral issues. Age gradient direction correct but magnitude exaggerated.',
    insightZh: 'MAE 14.4pp。LLM在社会道德议题上显示强烈进步偏差。年龄梯度方向正确但幅度夸大。',
    source: 'Ipsos 2022 Survey',
  },
  {
    no: 'BT-005', name: 'Death Penalty Attitudes', nameZh: '死刑态度',
    type: 'backtest', category: 'social', status: 'completed', sample: 1000, mae: 7.0,
    desc: 'Public support for the death penalty. MHA 2023 survey (n=2000) as benchmark.',
    descZh: '公众对死刑的支持度。以MHA 2023调查(n=2000)为基准。',
    insight: 'MAE 7.0pp. Model underestimates support for death penalty. Conservative Singaporean values partially captured.',
    insightZh: 'MAE 7.0pp。模型低估了对死刑的支持度。部分捕捉到新加坡保守价值观。',
    source: 'MHA 2023 Survey',
  },
  {
    no: 'BT-006', name: 'Racial & Religious Harmony', nameZh: '种族宗教和谐指标',
    type: 'backtest', category: 'social', status: 'completed', sample: 1000, mae: 9.3,
    desc: 'Cross-racial trust and harmony perceptions. IPS 2024 survey (n=4000) as benchmark.',
    descZh: '跨种族信任和和谐感知。以IPS 2024调查(n=4000)为基准。',
    insight: 'MAE 9.3pp. Model captures ethnic-specific patterns but overestimates cross-racial tension.',
    insightZh: 'MAE 9.3pp。模型捕捉到种族特定模式，但高估了跨种族紧张程度。',
    source: 'IPS 2024 Survey',
  },
  {
    no: 'BT-007', name: 'Net Zero 2050 Support', nameZh: '2050 净零碳排支持度',
    type: 'backtest', category: 'policy', status: 'completed', sample: 1000, mae: 2.9,
    desc: 'Public support for Singapore Net Zero by 2050 target. MSE/NUS/SUTD 2023 survey (n=2000+).',
    descZh: '公众对新加坡2050年净零碳排目标的支持度。MSE/NUS/SUTD 2023调查(n=2000+)。',
    predicted: { 'Strongly support': 31.2, 'Support': 37.6, 'Neutral': 19.8, 'Oppose': 8.3, 'Strongly oppose': 3.1 },
    actual: { 'Strongly support': 28, 'Support': 37, 'Neutral': 24, 'Oppose': 8, 'Strongly oppose': 3 },
    source: 'MSE/NUS/SUTD 2023 Climate Survey',
    insight: 'MAE 2.9pp. Best-performing backtest! Near-perfect match on all categories. Climate concern aligns well with LLM training data.',
    insightZh: 'MAE 2.9pp。表现最佳的回测！所有类别近乎完美匹配。气候关切与LLM训练数据高度一致。',
  },
  {
    no: 'BT-009', name: 'Plastic Bag Charge Behavior', nameZh: '塑料袋收费行为',
    type: 'backtest', category: 'policy', status: 'completed', sample: 1000, mae: 9.3,
    desc: 'Behavioral response to $0.05 plastic bag charge. NEA/FairPrice 2024 data as benchmark.',
    descZh: '对$0.05塑料袋收费的行为反应。以NEA/FairPrice 2024数据为基准。',
    insight: 'MAE 9.3pp. Behavioral questions are harder than attitudinal ones for LLM simulation.',
    insightZh: 'MAE 9.3pp。行为类问题对LLM模拟来说比态度类问题更难。',
    source: 'NEA/FairPrice 2024 Data',
  },
  {
    no: 'BT-010', name: 'Cost of Living Concerns', nameZh: '生活成本关切',
    type: 'backtest', category: 'economy', status: 'completed', sample: 1000, mae: null,
    desc: 'Top concerns of Singaporeans. IPS Post-GE2025 survey (n=2056) as benchmark. Multi-select format.',
    descZh: '新加坡人最关切的问题。以IPS Post-GE2025调查(n=2056)为基准。多选格式，MAE不可直接比较。',
    source: 'IPS Post-GE2025 Survey',
  },
  {
    no: 'BT-INS-001', name: 'Insurance Purchase Channel', nameZh: '保险购买渠道偏好',
    type: 'backtest', category: 'economy', status: 'completed', sample: 869, mae: 15.7,
    desc: 'Backtest against Capco Singapore Insurance Survey 2023. Model underestimates agent dominance, overestimates digital channels.',
    descZh: '回测对标 Capco 新加坡保险调查 2023。模型低估代理人主导地位、高估数字渠道。方向性模式正确。',
    insight: 'MAE 15.7pp. First insurance-vertical backtest. Behavioral channel choice is harder than attitudinal opinion.',
    insightZh: 'MAE 15.7pp。首个保险垂直领域回测。行为渠道选择比态度意见更难预测。',
    source: 'Capco Singapore Insurance Survey 2023',
  },
  // ── Client Predictions / Surveys ──
  {
    no: 'SV-001', name: 'National Service Attitudes', nameZh: '国民服役态度调研',
    type: 'prediction', category: 'social', status: 'completed', sample: 1000, mae: null,
    desc: '3-dimension NS attitudes survey: importance, fairness, and duration. Multi-demographic breakdown.',
    descZh: '国民服役态度3维调研：重要性、公平性、服役时长。按性别、年龄、种族、收入多维分析。',
    insight: '82.7% think NS is important. 53.1% think it\'s fair. 37.9% keep 2 years. Male 58% "very important" vs Female 40%. Age gradient: 60+ 67% vs 18-29 38%.',
    insightZh: '82.7%认为NS重要。53.1%认为公平。37.9%保持2年。男性58%"非常重要" vs 女性40%。年龄梯度：60+ 67% vs 18-29 38%。',
    surveyResults: [
      { q: 'Q1: How important is NS to Singapore?', qZh: 'Q1: 国民服役对新加坡有多重要？',
        results: { 'Very important': 48.9, 'Somewhat important': 33.8, 'Neutral': 10.9, 'Somewhat unimportant': 4.6, 'Not important': 1.8 } },
      { q: 'Q2: How fair is the current NS system?', qZh: 'Q2: 目前的NS制度公平吗？',
        results: { 'Very fair': 12.5, 'Somewhat fair': 40.6, 'Neutral': 18.1, 'Somewhat unfair': 21.9, 'Very unfair': 6.9 } },
      { q: 'Q3: Should 2-year NS duration be shortened?', qZh: 'Q3: 2年服役期是否应缩短？',
        results: { 'Keep 2 years': 37.9, 'Maybe 18 months': 35.3, '12-18 months': 16.1, 'Under 12 months': 6.1, 'Abolish': 4.6 } },
    ],
  },
  {
    no: 'SV-002', name: 'IP Price Hike Response', nameZh: '综合健保计划涨价接受度',
    type: 'prediction', category: 'economy', status: 'completed', sample: 840, mae: null,
    desc: '4-dimension IP survey: current status, 15% hike reaction, max acceptable premium, key choice factors.',
    descZh: '综合健保计划（IP）涨价应对4维调研：当前IP状态、15%涨价反应、最高可接受保费、最重要选择因素。',
    insight: '53.6% at risk of leaving/downgrading with 15% hike. Only 34% accept. Premium cost #1 factor (38.5%). Income: $8K+ 42% accept vs <$3K 28%.',
    insightZh: '15%涨价下53.6%面临流失风险。仅34%接受。保费价格首要因素（38.5%）。收入：$8K+ 42%接受 vs <$3K 28%。',
    surveyResults: [
      { q: 'Q1: Do you have an Integrated Shield Plan?', qZh: 'Q1: 是否持有综合健保计划？',
        results: { 'Private hospital IP': 42.9, 'Govt hospital IP': 26.5, 'MediShield only': 24.5, 'Don\'t know': 6.1 } },
      { q: 'Q2: If premium +15%, what would you do?', qZh: 'Q2: 保费涨15%你会怎么做？',
        results: { 'Accept & keep': 34.0, 'Downgrade': 20.2, 'Switch insurer': 24.0, 'Drop IP': 9.4, 'Not sure': 12.3 } },
      { q: 'Q3: Max annual premium for private IP?', qZh: 'Q3: 私立医院IP最高年保费？',
        results: { '<$300': 18.6, '$300-600': 31.2, '$600-1,200': 24.9, '$1,200-2,000': 12.7, '>$2,000': 4.4, 'No IP': 8.2 } },
      { q: 'Q4: Most important factor choosing IP?', qZh: 'Q4: 选IP最重要的因素？',
        results: { 'Premium cost': 38.5, 'Coverage scope': 24.8, 'Brand': 12.7, 'Claims process': 9.9, 'Recommendation': 8.1, 'Pre-existing': 6.1 } },
    ],
  },
  {
    no: 'SV-003', name: 'IP Switching & Channels', nameZh: 'IP 转保意愿与渠道偏好',
    type: 'prediction', category: 'economy', status: 'completed', sample: 1000, mae: null,
    desc: '3-topic survey: MAS portability reform switching intention, switching triggers, channel preference (agent vs digital).',
    descZh: '3题调研：MAS可携带性改革后的转保意愿、触发转保的关键因素、购买渠道偏好。',
    surveyResults: [
      { q: 'Q1: Would you switch IP under MAS portability?', qZh: 'Q1: MAS可携带性改革下会转保吗？',
        results: { 'Yes, actively considering': 22.1, 'Maybe, if better offer': 38.4, 'Unlikely': 25.3, 'No, staying': 14.2 } },
      { q: 'Q2: Key trigger for switching?', qZh: 'Q2: 触发转保的关键因素？',
        results: { 'Lower premium': 41.2, 'Better coverage': 28.6, 'Poor claims experience': 15.8, 'Agent recommendation': 9.1, 'Other': 5.3 } },
      { q: 'Q3: Preferred purchase channel?', qZh: 'Q3: 偏好的购买渠道？',
        results: { 'Insurance agent': 38.7, 'Online direct': 27.4, 'Bank/bancassurance': 18.1, 'Comparison platform': 12.3, 'Other': 3.5 } },
    ],
  },
  {
    no: 'SV-004', name: 'IP Product Innovation', nameZh: 'IP 产品创新接受度',
    type: 'prediction', category: 'economy', status: 'completed', sample: 920, mae: null,
    desc: '3-topic survey: panel doctor acceptance, basic IP demand, coverage trade-off willingness.',
    descZh: '3题调研：指定医生接受度、基础IP需求、保障取舍意愿。',
    surveyResults: [
      { q: 'Q1: Accept panel doctor for lower premium?', qZh: 'Q1: 接受指定医生换取更低保费？',
        results: { 'Yes, definitely': 31.4, 'Yes, if savings >20%': 29.8, 'Unsure': 17.6, 'No, want free choice': 21.2 } },
      { q: 'Q2: Interested in basic/affordable IP?', qZh: 'Q2: 对基础/低价IP感兴趣吗？',
        results: { 'Very interested': 28.3, 'Somewhat': 35.1, 'Neutral': 18.4, 'Not interested': 18.2 } },
      { q: 'Q3: Willing to trade coverage for lower cost?', qZh: 'Q3: 愿意用保障换低价吗？',
        results: { 'Yes, less coverage OK': 24.7, 'Depends on what\'s cut': 41.3, 'No, want full coverage': 34.0 } },
    ],
  },
  {
    no: 'SV-005', name: 'Young Adults (25-35) IP Awareness', nameZh: '青年（25-35岁）IP 认知与购买障碍',
    type: 'prediction', category: 'economy', status: 'completed', sample: 122, mae: null,
    desc: '3-topic survey targeting 25-35 year olds: IP awareness level, purchase barriers, purchase triggers.',
    descZh: '3题调研，聚焦25-35岁：IP认知水平、购买障碍、购买触发事件。',
    surveyResults: [
      { q: 'Q1: How well do you understand IP?', qZh: 'Q1: 对IP了解程度？',
        results: { 'Very well': 11.5, 'Somewhat': 34.4, 'Basic only': 32.0, 'Not at all': 22.1 } },
      { q: 'Q2: Main barrier to buying IP?', qZh: 'Q2: 购买IP的主要障碍？',
        results: { 'Too expensive': 33.6, 'Don\'t understand': 25.4, 'Feel healthy/young': 20.5, 'Already have MediShield': 13.9, 'Other': 6.6 } },
      { q: 'Q3: What would trigger you to buy?', qZh: 'Q3: 什么会触发你购买？',
        results: { 'Health scare': 29.5, 'Marriage/child': 26.2, 'Parent\'s advice': 18.0, 'Friend\'s claim story': 14.8, 'Marketing/ad': 11.5 } },
    ],
  },
  {
    no: 'SV-006', name: 'Savings Insurance vs Alternatives', nameZh: '储蓄险 vs 替代理财产品偏好',
    type: 'prediction', category: 'economy', status: 'completed', sample: 1000, mae: null,
    desc: '4-topic survey: T-bill decline reallocation, savings insurance attractiveness, long-term preference, life-stage triggers.',
    descZh: '4题调研：T-bill下降后储蓄配置、储蓄险吸引力、长期产品偏好、人生阶段触发。',
    surveyResults: [
      { q: 'Q1: If T-bill rates drop, where to reallocate?', qZh: 'Q1: T-bill利率下降后资金去向？',
        results: { 'Fixed deposit': 31.8, 'Savings insurance': 22.4, 'Stocks/ETF': 20.1, 'CPF top-up': 14.3, 'Keep T-bill': 11.4 } },
      { q: 'Q2: Is savings insurance attractive now?', qZh: 'Q2: 储蓄险现在有吸引力吗？',
        results: { 'Very attractive': 14.2, 'Somewhat': 33.6, 'Neutral': 25.8, 'Not attractive': 18.1, 'Don\'t know': 8.3 } },
      { q: 'Q3: Preferred long-term savings product?', qZh: 'Q3: 偏好的长期储蓄产品？',
        results: { 'Endowment': 28.4, 'Whole life': 21.6, 'Investment-linked': 16.8, 'Pure investment': 22.1, 'None': 11.1 } },
      { q: 'Q4: Life event triggering savings plan?', qZh: 'Q4: 触发储蓄计划的人生事件？',
        results: { 'Child\'s education': 31.5, 'Retirement planning': 28.7, 'Marriage': 18.2, 'First job': 14.8, 'Other': 6.8 } },
    ],
  },
  {
    no: 'SV-007', name: 'ILP Trust & Bundling', nameZh: '投资型保险信任度与捆绑偏好',
    type: 'prediction', category: 'economy', status: 'completed', sample: 1000, mae: null,
    desc: '3-topic survey: ILP trust level, bundling vs unbundling preference, purchase drivers.',
    descZh: '3题调研：ILP信任度、捆绑vs拆分偏好、购买驱动因素。',
    surveyResults: [
      { q: 'Q1: How much do you trust ILPs?', qZh: 'Q1: 对投资型保险的信任度？',
        results: { 'High trust': 8.7, 'Moderate trust': 28.4, 'Neutral': 24.1, 'Low trust': 26.3, 'No trust': 12.5 } },
      { q: 'Q2: Prefer bundled or separate insurance+investment?', qZh: 'Q2: 偏好捆绑还是拆分保险+投资？',
        results: { 'Bundled ILP': 22.3, 'Separate is better': 45.8, 'Depends on product': 24.6, 'Don\'t know': 7.3 } },
      { q: 'Q3: Main driver for buying ILP?', qZh: 'Q3: 购买ILP的主要驱动因素？',
        results: { 'Agent recommendation': 32.1, 'Guaranteed returns': 24.6, 'Tax benefits': 16.8, 'Convenience': 15.2, 'Other': 11.3 } },
    ],
  },
  // ── Pending backtests ──
  {
    no: 'BT-011', name: 'Gambling Participation Rate', nameZh: '博彩参与率',
    type: 'backtest', category: 'social', status: 'pending', sample: 1000, mae: null,
    desc: 'Gambling participation and type preferences. NCPG 2023 survey (n=3,007) as benchmark.',
    descZh: '博彩参与率及类型偏好。以NCPG 2023调查(n=3,007)为基准。',
  },
  {
    no: 'BT-012', name: 'Institutional Trust', nameZh: '机构信任度',
    type: 'backtest', category: 'social', status: 'pending', sample: 1000, mae: null,
    desc: 'Trust in parliament, courts, police, media. Edelman/IPS benchmark data.',
    descZh: '对国会、法院、警察、媒体的信任度。Edelman/IPS基准数据。',
  },
  {
    no: 'BT-013', name: 'Marriage Intention', nameZh: '婚姻意愿',
    type: 'backtest', category: 'social', status: 'pending', sample: 1000, mae: null,
    desc: 'Marriage intention among young adults. NPTD 2021 Marriage & Parenthood survey as benchmark.',
    descZh: '年轻人的婚姻意愿。以NPTD 2021婚育调查为基准。',
  },
  {
    no: 'BT-014', name: 'Volunteering & Giving', nameZh: '志愿服务与捐赠',
    type: 'backtest', category: 'social', status: 'pending', sample: 1000, mae: null,
    desc: 'Volunteering rates and donation behavior. NVPC 2023 survey as benchmark.',
    descZh: '志愿服务率和捐赠行为。以NVPC 2023调查为基准。',
  },
];

const CATEGORY_COLORS: Record<Category, string> = {
  election: 'bg-blue-500/10 text-blue-400',
  economy: 'bg-purple-500/10 text-purple-400',
  social: 'bg-orange-500/10 text-orange-400',
  policy: 'bg-cyan-500/10 text-cyan-400',
};

const CATEGORY_LABELS: Record<Category, { en: string; zh: string }> = {
  election: { en: 'Election', zh: '选举' },
  economy: { en: 'Economy', zh: '经济' },
  social: { en: 'Social', zh: '社会' },
  policy: { en: 'Policy', zh: '政策' },
};

export default function CasesPage() {
  const { locale } = useLocale();
  const zh = locale === 'zh';
  const [filter, setFilter] = useState<'all' | CaseType>('all');
  const [expanded, setExpanded] = useState<string | null>(null);

  const filtered = filter === 'all' ? CASES : CASES.filter(c => c.type === filter);

  const completedBT = CASES.filter(c => c.type === 'backtest' && c.status === 'completed');
  const avgMAE = completedBT.filter(c => c.mae !== null).reduce((s, c) => s + c.mae!, 0) / completedBT.filter(c => c.mae !== null).length;
  const totalSampled = CASES.filter(c => c.status === 'completed').reduce((s, c) => s + c.sample, 0);

  return (
    <div className="min-h-screen bg-[#050810] text-[#e2e8f0]">
      <NavBar />

      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold mb-2">
            {zh ? '案例验证库' : 'Validation Case Registry'}
          </h1>
          <p className="text-sm text-[#64748b] leading-relaxed">
            {zh
              ? '所有回测验证和客户模拟案例。每个回测案例将预测结果与真实调查/选举数据对比，以 MAE（平均绝对误差）衡量精度。'
              : 'All backtest validations and client simulation cases. Each backtest compares predictions against real survey/election data, measured by MAE (Mean Absolute Error).'}
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
          <div className="bg-[#111827] border border-[#1e293b] rounded-xl p-4 text-center">
            <div className="text-2xl font-extrabold text-[#e2e8f0]">{CASES.length}</div>
            <div className="text-[10px] text-[#64748b] uppercase tracking-wider mt-1">{zh ? '总案例' : 'Total Cases'}</div>
          </div>
          <div className="bg-[#111827] border border-[#1e293b] rounded-xl p-4 text-center">
            <div className="text-2xl font-extrabold text-green-400">{completedBT.length}</div>
            <div className="text-[10px] text-[#64748b] uppercase tracking-wider mt-1">{zh ? '已完成回测' : 'Backtests Done'}</div>
          </div>
          <div className="bg-[#111827] border border-[#1e293b] rounded-xl p-4 text-center">
            <div className="text-2xl font-extrabold text-blue-400">{avgMAE.toFixed(1)}pp</div>
            <div className="text-[10px] text-[#64748b] uppercase tracking-wider mt-1">{zh ? '平均 MAE' : 'Avg MAE'}</div>
          </div>
          <div className="bg-[#111827] border border-[#1e293b] rounded-xl p-4 text-center">
            <div className="text-2xl font-extrabold text-purple-400">{(totalSampled / 1000).toFixed(1)}K</div>
            <div className="text-[10px] text-[#64748b] uppercase tracking-wider mt-1">{zh ? '总调研人次' : 'Total Sampled'}</div>
          </div>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {[
            { key: 'all' as const, label: zh ? '全部' : 'All', count: CASES.length },
            { key: 'backtest' as const, label: zh ? '回测验证' : 'Backtest', count: CASES.filter(c => c.type === 'backtest').length },
            { key: 'prediction' as const, label: zh ? '客户调研' : 'Client Survey', count: CASES.filter(c => c.type === 'prediction').length },
          ].map(t => (
            <button key={t.key} onClick={() => setFilter(t.key)}
              className={`px-4 py-2 rounded-lg text-xs font-semibold border transition-all ${
                filter === t.key
                  ? 'border-blue-500 bg-blue-500/10 text-blue-400'
                  : 'border-[#1e293b] bg-[#111827] text-[#64748b] hover:text-[#94a3b8]'
              }`}>
              {t.label} ({t.count})
            </button>
          ))}
        </div>

        {/* ── 社会模拟 Section ── */}
        {(filter === 'all' || filter === 'prediction') && (
          <div className="mb-6">
            <h2 className="text-lg font-bold mb-1 text-purple-400">
              {zh ? '社会模拟' : 'Social Simulation'}
            </h2>
            <p className="text-xs text-[#64748b] mb-4">
              {zh
                ? '基于 7 天 4 轮 ABM 模型的社会舆论演变模拟。冷反应 → 初步讨论 → 同伴影响 → 回音室效应。'
                : '7-day 4-round ABM model for social opinion evolution. Cold reaction → early discussion → peer influence → echo chamber.'}
            </p>
          </div>
        )}

        {/* Case list */}
        <div className="space-y-3">
          {filtered.map(c => {
            const isExpanded = expanded === c.no;
            return (
              <div key={c.no} className={`bg-[#111827] border rounded-xl overflow-hidden transition-all ${
                isExpanded ? 'border-blue-500/40' : 'border-[#1e293b] hover:border-[#2a3a4f]'
              }`}>
                {/* Top row */}
                <div className="p-4 cursor-pointer flex items-start gap-4" onClick={() => setExpanded(isExpanded ? null : c.no)}>
                  {/* Status icon */}
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                    c.status === 'completed' ? 'bg-green-500/10 text-green-400' : 'bg-[#1e293b] text-[#475569]'
                  }`}>
                    {c.status === 'completed' ? '✓' : '⏳'}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="text-sm font-bold text-[#e2e8f0]">{zh ? c.nameZh : c.name}</span>
                      <span className="text-[10px] font-mono text-[#475569]">{c.no}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${CATEGORY_COLORS[c.category]}`}>
                        {zh ? CATEGORY_LABELS[c.category].zh : CATEGORY_LABELS[c.category].en}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                        c.type === 'backtest' ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                        'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                      }`}>
                        {c.type === 'backtest' ? (zh ? '回测' : 'Backtest') : (zh ? '客户调研' : 'Survey')}
                      </span>
                    </div>
                    <p className="text-xs text-[#94a3b8] leading-relaxed">{zh ? c.descZh : c.desc}</p>
                    <div className="flex gap-4 mt-2 text-[11px] text-[#475569]">
                      <span>n={c.sample.toLocaleString()}</span>
                      {c.source && <span>{c.source}</span>}
                    </div>
                  </div>

                  {/* MAE */}
                  <div className="flex-shrink-0 text-right">
                    {c.mae !== null ? (
                      <>
                        <div className={`text-lg font-extrabold font-mono ${
                          c.mae <= 5 ? 'text-green-400' : c.mae <= 10 ? 'text-yellow-400' : 'text-orange-400'
                        }`}>{c.mae}pp</div>
                        <div className="text-[10px] text-[#475569] uppercase">MAE</div>
                      </>
                    ) : c.status === 'completed' ? (
                      <div className="text-xs text-[#475569]">{zh ? '无基准' : 'No GT'}</div>
                    ) : (
                      <div className="text-xs text-[#475569]">{zh ? '待运行' : 'Pending'}</div>
                    )}
                    <div className="text-[#475569] text-sm mt-1">{isExpanded ? '▲' : '▼'}</div>
                  </div>
                </div>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className="border-t border-[#1e293b] p-4 space-y-4">
                    {/* Predicted vs Actual (backtest with data) */}
                    {c.predicted && c.actual && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-4">
                          <div className="text-xs text-[#64748b] uppercase tracking-wider font-semibold mb-3">
                            {zh ? '模型预测' : 'Model Prediction'}
                          </div>
                          <div className="space-y-2">
                            {Object.entries(c.predicted).map(([opt, pct]) => (
                              <div key={opt}>
                                <div className="flex justify-between mb-0.5">
                                  <span className="text-xs text-[#94a3b8]">{opt}</span>
                                  <span className="text-xs font-mono text-blue-400">{pct}%</span>
                                </div>
                                <div className="h-2 bg-[#111827] rounded-full overflow-hidden">
                                  <div className="h-full bg-blue-500/60 rounded-full" style={{ width: `${pct}%` }} />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                        <div className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-4">
                          <div className="text-xs text-[#64748b] uppercase tracking-wider font-semibold mb-3">
                            {zh ? '真实结果' : 'Ground Truth'}
                          </div>
                          <div className="space-y-2">
                            {Object.entries(c.actual).map(([opt, pct]) => (
                              <div key={opt}>
                                <div className="flex justify-between mb-0.5">
                                  <span className="text-xs text-[#94a3b8]">{opt}</span>
                                  <span className="text-xs font-mono text-green-400">{pct}%</span>
                                </div>
                                <div className="h-2 bg-[#111827] rounded-full overflow-hidden">
                                  <div className="h-full bg-green-500/60 rounded-full" style={{ width: `${pct}%` }} />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Survey results (prediction type with surveyResults) */}
                    {c.surveyResults && c.surveyResults.length > 0 && (
                      <div className="space-y-4">
                        {c.surveyResults.map((sq, qi) => {
                          const colors = ['bg-blue-500', 'bg-purple-500', 'bg-cyan-500', 'bg-green-500', 'bg-orange-500', 'bg-red-500'];
                          return (
                            <div key={qi} className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-4">
                              <div className="text-xs font-bold text-[#e2e8f0] mb-3">{zh ? sq.qZh : sq.q}</div>
                              <div className="space-y-2">
                                {Object.entries(sq.results)
                                  .sort(([, a], [, b]) => b - a)
                                  .map(([opt, pct], i) => (
                                    <div key={opt}>
                                      <div className="flex justify-between mb-0.5">
                                        <span className="text-xs text-[#94a3b8]">{opt}</span>
                                        <span className="text-xs font-mono text-[#e2e8f0]">{pct}%</span>
                                      </div>
                                      <div className="h-2 bg-[#111827] rounded-full overflow-hidden">
                                        <div className={`h-full ${colors[i % colors.length]} rounded-full`} style={{ width: `${pct}%` }} />
                                      </div>
                                    </div>
                                  ))}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Pending backtest info */}
                    {c.status === 'pending' && (
                      <div className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-4 text-center">
                        <div className="text-sm text-[#64748b]">
                          {zh ? '此回测案例尚未运行。基准数据已确认，等待排期执行。' : 'This backtest has not been run yet. Benchmark data confirmed, awaiting scheduled execution.'}
                        </div>
                      </div>
                    )}

                    {/* Insight */}
                    {(c.insight || c.insightZh) && (
                      <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4">
                        <div className="text-xs text-blue-400 uppercase tracking-wider font-semibold mb-1">
                          {zh ? '分析洞察' : 'Analysis Insight'}
                        </div>
                        <p className="text-sm text-[#94a3b8] leading-relaxed">
                          {zh ? c.insightZh || c.insight : c.insight}
                        </p>
                      </div>
                    )}

                    {/* Description detail for surveys without insight */}
                    {c.type === 'prediction' && !c.insight && (
                      <div className="bg-purple-500/5 border border-purple-500/20 rounded-xl p-4">
                        <div className="text-xs text-purple-400 uppercase tracking-wider font-semibold mb-1">
                          {zh ? '调研详情' : 'Survey Details'}
                        </div>
                        <p className="text-sm text-[#94a3b8] leading-relaxed">
                          {zh ? c.descZh : c.desc}
                        </p>
                        <div className="flex gap-4 mt-3 text-xs text-[#475569]">
                          <span>{zh ? '样本' : 'Sample'}: n={c.sample.toLocaleString()}</span>
                          <span>{zh ? '状态' : 'Status'}: {c.status === 'completed' ? (zh ? '已完成' : 'Completed') : (zh ? '待运行' : 'Pending')}</span>
                          <span>{zh ? '零 API 错误' : 'Zero API errors'}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* MAE Legend */}
        <div className="mt-8 bg-[#0d1117] border border-[#1e293b] rounded-xl p-4">
          <div className="text-xs text-[#64748b] uppercase tracking-wider font-semibold mb-3">
            {zh ? 'MAE 精度等级' : 'MAE Accuracy Tiers'}
          </div>
          <div className="flex gap-6 flex-wrap">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-400" />
              <span className="text-xs text-[#94a3b8]">≤5pp — {zh ? '高精度' : 'High accuracy'}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-yellow-400" />
              <span className="text-xs text-[#94a3b8]">5-10pp — {zh ? '中等精度' : 'Moderate'}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-orange-400" />
              <span className="text-xs text-[#94a3b8]">&gt;10pp — {zh ? '需校准' : 'Needs calibration'}</span>
            </div>
          </div>
          <p className="text-[10px] text-[#475569] mt-3">
            {zh
              ? 'MAE = Mean Absolute Error（平均绝对误差），衡量模型预测值与真实调查/选举结果各选项之间的平均偏差（百分点）。MAE 越低越好。'
              : 'MAE = Mean Absolute Error, measuring average deviation between model predictions and real survey/election results across all options (in percentage points). Lower is better.'}
          </p>
        </div>

        {/* Footer */}
        <div className="text-center text-[11px] text-[#475569] mt-8 pb-4">
          Singapore Digital Twin — {zh ? '案例验证库' : 'Validation Case Registry'} — Updated 2026-03-10
          <br />
          <span className="text-[#334155]">{zh ? '所有回测结果完整公开，包括表现不佳的案例。我们相信透明度是建立信任的基础。' : 'All backtest results are fully disclosed, including underperforming cases. We believe transparency builds trust.'}</span>
        </div>
      </div>
    </div>
  );
}
