export type Locale = 'en' | 'zh';

export const translations = {
  en: {
    // Home
    title: 'Singapore Digital Twin',
    subtitle: 'Singapore Population Simulation Platform',
    desc: '170,000+ synthetic agents · LLM-powered survey simulation · Real-time demographic analysis',
    openCanvas: 'Open Canvas',
    audiencePanel: 'Audience Panel',
    audiencePanelDesc: 'Filter by age, gender, income, housing type. See real-time eligible count from 20K+ synthetic agents.',
    surveyQuery: 'Survey Query',
    surveyQueryDesc: '6 pre-built insurance scenarios (BT-011~014, SV-003~004) or design your own with custom context.',
    instantResults: 'Instant Results',
    instantResultsDesc: 'Distribution charts, demographic breakdowns, individual agent quotes with quality scoring.',
    poweredBy: 'Powered by DeepSeek LLM · NVIDIA Reward Model · Stratified Census Sampling',

    // Canvas
    beta: 'BETA',
    presets: 'PRESETS',
    addGroup: '+ Add Group',
    runSimulation: 'Run Simulation',
    running: 'Running...',
    nodes: 'Nodes',
    edges: 'Edges',
    agents: 'Agents',

    // Audience Node
    audiencePanelTitle: 'Audience Panel',
    defineTarget: 'Define your target group',
    ageMin: 'Age Min',
    ageMax: 'Age Max',
    gender: 'Gender',
    all: 'All',
    male: 'Male',
    female: 'Female',
    housingType: 'Housing Type',
    incomeMin: 'Income Min',
    incomeMax: 'Income Max',
    sampleSize: 'Sample Size',
    eligible: 'Eligible',
    avgAge: 'Avg age',

    // Query Node
    surveyQueryTitle: 'Survey Query',
    defineQuestion: 'Define question & scenario',
    quickLoadPreset: 'Quick Load Preset',
    question: 'Question',
    questionPlaceholder: 'Enter your survey question...',
    options: 'Options',
    add: '+ Add',
    contextInjection: 'Context Injection',
    contextPlaceholder: 'Background context for agents (do NOT include ground truth)...',
    chars: 'chars',

    // Result Node
    results: 'Results',
    respondents: 'respondents',
    waitingForSimulation: 'Waiting for simulation...',
    errorOccurred: 'Error occurred',
    connectNodes: 'Connect an Audience and Query node, then click Run',
    distribution: 'Distribution',
    byAge: 'By Age',
    quotes: 'Quotes',
    population: 'Population',
    eligibleLabel: 'Eligible',
    sampled: 'Sampled',
    positiveRateByAge: 'Positive Rate by Age Group',
    byIncome: 'By Income',
    sampleReasoning: 'Sample Reasoning',
    highQuality: 'high quality',
    queued: 'Queued...',
    surveyingAgents: 'Surveying agents...',
    count: 'Count',
    positiveRate: 'Positive Rate',
    tokens: 'Tokens',
    cost: 'Cost',

    // Housing options
    hdb12: 'HDB 1-2 Room',
    hdb3: 'HDB 3 Room',
    hdb4: 'HDB 4 Room',
    hdb5: 'HDB 5 Room / Exec',
    condo: 'Condo',
    landed: 'Landed',
  },

  zh: {
    // Home
    title: '新加坡数字孪生',
    subtitle: '新加坡人口模拟平台',
    desc: '17万+ 合成智能体 · LLM 驱动调研模拟 · 实时人口统计分析',
    openCanvas: '打开画布',
    audiencePanel: '受众面板',
    audiencePanelDesc: '按年龄、性别、收入、住房类型筛选，实时显示 2 万+ 合成 agent 中符合条件的数量。',
    surveyQuery: '调研问卷',
    surveyQueryDesc: '6 个预置保险场景（BT-011~014, SV-003~004），也可自定义问题和上下文。',
    instantResults: '即时结果',
    instantResultsDesc: '分布图表、人口细分、个体 agent 回答引用及质量评分。',
    poweredBy: '基于 DeepSeek LLM · NVIDIA 奖励模型 · 分层人口普查抽样',

    // Canvas
    beta: '测试版',
    presets: '预设场景',
    addGroup: '+ 新增组',
    runSimulation: '运行模拟',
    running: '运行中...',
    nodes: '节点',
    edges: '连线',
    agents: '智能体',

    // Audience Node
    audiencePanelTitle: '受众面板',
    defineTarget: '定义目标人群',
    ageMin: '最小年龄',
    ageMax: '最大年龄',
    gender: '性别',
    all: '全部',
    male: '男',
    female: '女',
    housingType: '住房类型',
    incomeMin: '最低收入',
    incomeMax: '最高收入',
    sampleSize: '样本量',
    eligible: '符合条件',
    avgAge: '平均年龄',

    // Query Node
    surveyQueryTitle: '调研查询',
    defineQuestion: '设定问题与场景',
    quickLoadPreset: '快速加载预设',
    question: '问题',
    questionPlaceholder: '输入调研问题...',
    options: '选项',
    add: '+ 添加',
    contextInjection: '上下文注入',
    contextPlaceholder: '为 agent 提供背景信息（不要包含 ground truth）...',
    chars: '字符',

    // Result Node
    results: '结果',
    respondents: '受访者',
    waitingForSimulation: '等待模拟运行...',
    errorOccurred: '发生错误',
    connectNodes: '连接受众和查询节点，然后点击运行',
    distribution: '分布',
    byAge: '按年龄',
    quotes: '个体引用',
    population: '总人口',
    eligibleLabel: '符合条件',
    sampled: '已抽样',
    positiveRateByAge: '各年龄段正面率',
    byIncome: '按收入',
    sampleReasoning: '推理示例',
    highQuality: '高质量',
    queued: '排队中...',
    surveyingAgents: '正在调研 agent...',
    count: '数量',
    positiveRate: '正面率',
    tokens: 'Tokens',
    cost: '费用',

    // Housing options
    hdb12: '组屋 1-2房',
    hdb3: '组屋 3房',
    hdb4: '组屋 4房',
    hdb5: '组屋 5房/行政',
    condo: '公寓',
    landed: '有地住宅',
  },
} as const;

export type TranslationKey = keyof typeof translations.en;

export function t(locale: Locale, key: TranslationKey): string {
  return translations[locale][key] || translations.en[key] || key;
}
