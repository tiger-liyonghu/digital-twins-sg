export interface ScenarioPrefill {
  industry: string;
  question: string;
  questionZh: string;
  options: string[];
  optionsZh: string[];
  context?: string;
  contextZh?: string;
}

export const SCENARIO_PREFILLS: ScenarioPrefill[] = [
  {
    industry: 'government',
    question: 'The government proposes raising GST from 9% to 10% to fund increased healthcare spending. How would you respond?',
    questionZh: '政府提议将 GST 从 9% 提高到 10%，用于增加医疗支出。你怎么看？',
    options: ['Strongly support', 'Somewhat support', 'Neutral', 'Somewhat oppose', 'Strongly oppose', 'No opinion'],
    optionsZh: ['强烈支持', '比较支持', '中立', '比较反对', '强烈反对', '没有意见'],
    context: 'Singapore GST was raised from 8% to 9% in January 2024. Government revenue from GST: ~S$16 billion/year. Healthcare spending is projected to triple by 2030.',
    contextZh: '新加坡 GST 于 2024 年 1 月从 8% 上调至 9%。GST 年收入约 160 亿新元。医疗支出预计到 2030 年翻三倍。',
  },
  {
    industry: 'government',
    question: 'If a general election were held today, which party would you vote for?',
    questionZh: '如果今天举行大选，你会投票给哪个政党？',
    options: ['PAP', 'WP', 'PSP', 'SDP', 'Other opposition', 'Undecided'],
    optionsZh: ['人民行动党', '工人党', '前进党', '新加坡民主党', '其他反对党', '未决定'],
    context: 'GE2025 results: PAP 65.57%, WP 12.04%, PSP 7.09%. PAP won 79 of 97 seats. Voter turnout: 93.56%. Singapore uses GRC and SMC constituencies.',
    contextZh: 'GE2025 结果：PAP 65.57%，WP 12.04%，PSP 7.09%。PAP 赢得 97 席中的 79 席。投票率 93.56%。',
  },
  {
    industry: 'finance',
    question: 'Your health insurance premium increases by $300/year (from $800 to $1,100). What would you do?',
    questionZh: '你的医疗保险保费每年增加 $300（从 $800 涨到 $1,100）。你会怎么做？',
    options: ['Keep current plan', 'Downgrade coverage', 'Switch insurer', 'Cancel insurance', 'Undecided'],
    optionsZh: ['保留现有计划', '降低保障等级', '更换保险公司', '取消保险', '未决定'],
    context: 'Singapore has mandatory MediShield Life (basic) plus optional Integrated Shield Plans (IP). Average IP premium for 30-year-old: ~S$600-900/year. Claims ratio industry average: 85%.',
    contextZh: '新加坡有强制 MediShield Life（基础）加可选综合健保计划（IP）。30 岁 IP 平均保费约 S$600-900/年。行业平均赔付率 85%。',
  },
  {
    industry: 'retail',
    question: 'A new local skincare brand launches at $25-40 price point. How likely are you to try it?',
    questionZh: '一个新的本地护肤品牌以 $25-40 的价格推出。你有多大可能尝试？',
    options: ['Very likely', 'Somewhat likely', 'Neutral', 'Unlikely', 'Very unlikely'],
    optionsZh: ['非常可能', '比较可能', '中立', '不太可能', '非常不可能'],
  },
  {
    industry: 'government',
    question: 'Should the duration of National Service be reduced from 2 years to 1.5 years?',
    questionZh: '国民服役期限是否应该从 2 年缩短到 1.5 年？',
    options: ['Strongly agree', 'Somewhat agree', 'Neutral', 'Somewhat disagree', 'Strongly disagree', 'Not applicable'],
    optionsZh: ['非常同意', '比较同意', '中立', '比较不同意', '非常不同意', '不适用'],
    context: 'All male Singapore citizens and PRs serve 2-year National Service. ~20,000 enlistees per year. SAF active personnel: ~72,000. Recent public debate on NS duration and relevance.',
    contextZh: '所有新加坡男性公民和 PR 服 2 年国民服役。每年约 2 万人入伍。SAF 现役约 7.2 万人。近期有关于 NS 时长和必要性的公众讨论。',
  },
  {
    industry: 'healthcare',
    question: 'What is the biggest barrier preventing you from using telehealth (online doctor consultations)?',
    questionZh: '阻止你使用远程医疗（在线问诊）的最大障碍是什么？',
    options: ['Prefer face-to-face', 'Don\'t trust online diagnosis', 'Technology too difficult', 'Privacy concerns', 'Not aware of services', 'Cost concerns', 'No barriers — I use it'],
    optionsZh: ['更喜欢面对面', '不信任在线诊断', '技术太难', '隐私担忧', '不知道有这项服务', '费用顾虑', '没有障碍 — 我在用'],
    context: 'Telehealth adoption in Singapore grew 5x post-COVID. MOH licenses telehealth providers under Healthcare Services Act. 16% of residents are aged 65+. 4 official languages.',
    contextZh: '新加坡远程医疗采用率在疫情后增长 5 倍。MOH 根据医疗服务法许可远程医疗供应商。16% 居民 65 岁以上。4 种官方语言。',
  },
];

export const INDUSTRIES = [
  { value: 'government', label: 'Government & Policy', labelZh: '政府与政策' },
  { value: 'finance', label: 'Finance & Insurance', labelZh: '金融与保险' },
  { value: 'healthcare', label: 'Healthcare', labelZh: '医疗健康' },
  { value: 'retail', label: 'Retail & Consumer', labelZh: '零售与消费' },
  { value: 'realestate', label: 'Real Estate', labelZh: '房地产' },
  { value: 'other', label: 'Other', labelZh: '其他' },
];

export const PLANNING_AREAS = [
  'Bedok', 'Tampines', 'Jurong West', 'Sengkang', 'Woodlands', 'Hougang', 'Yishun',
  'Choa Chu Kang', 'Punggol', 'Bukit Merah', 'Bukit Batok', 'Toa Payoh', 'Ang Mo Kio',
  'Queenstown', 'Clementi', 'Kallang', 'Pasir Ris', 'Bishan', 'Geylang', 'Serangoon',
  'Bukit Panjang', 'Sembawang', 'Marine Parade', 'Bukit Timah', 'Novena', 'Central Area', 'Tanglin',
];

export const OCCUPATIONS = [
  { value: 'Senior Official or Manager', label: 'Manager', labelZh: '管理人员' },
  { value: 'Professional', label: 'Professional', labelZh: '专业人员' },
  { value: 'Associate Professional or Technician', label: 'Assoc. Professional', labelZh: '副专业人员' },
  { value: 'Clerical Worker', label: 'Clerical', labelZh: '文员' },
  { value: 'Service or Sales Worker', label: 'Service & Sales', labelZh: '服务与销售' },
  { value: 'Production Craftsman or Related Worker', label: 'Production', labelZh: '生产工人' },
  { value: 'Plant or Machine Operator or Assembler', label: 'Machine Operator', labelZh: '机器操作员' },
  { value: 'Cleaner, Labourer or Related Worker', label: 'Cleaner & Labourer', labelZh: '清洁与劳工' },
  { value: 'Agricultural or Fishery Worker', label: 'Agriculture', labelZh: '农渔业' },
];

export const SAMPLE_SIZES = [
  { n: 10, label: '10', labelZh: '10', use: 'Quick check', useZh: '快速验证', time: '<30s', cost: 'Free', costZh: '免费' },
  { n: 100, label: '100', labelZh: '100', use: 'See trends', useZh: '看初步趋势', time: '~1 min', cost: '$0.03', costZh: '$0.03' },
  { n: 1000, label: '1,000', labelZh: '1,000', use: 'Standard', useZh: '标准调研', time: '~3 min', cost: '$0.30', costZh: '$0.30' },
  { n: 2000, label: '2,000', labelZh: '2,000', use: 'Deep analysis', useZh: '深度分析', time: '~6 min', cost: '$0.60', costZh: '$0.60' },
  { n: 5000, label: '5,000', labelZh: '5,000', use: 'Segment reliable', useZh: '细分可靠', time: '~15 min', cost: '$1.50', costZh: '$1.50' },
  { n: 10000, label: '10,000', labelZh: '10,000', use: 'Full coverage', useZh: '全面覆盖', time: '~30 min', cost: '$3.00', costZh: '$3.00' },
];
