// Sophie conversation phases
export type Phase =
  | 'welcome'
  | 'scenario_select'
  | 'industry_select'
  | 'pain_point'
  | 'objective'
  | 'audience'
  | 'question'
  | 'sample_size'
  | 'confirm'
  | 'test_run'
  | 'test_analysis'
  | 'full_run'
  | 'results'
  | 'qa'
  | 'export'
  | 'archived';

// Message with optional interactive widget
export interface SophieMessage {
  id: string;
  role: 'sophie' | 'client' | 'system';
  content: string;
  timestamp: string;
  phase: Phase;
  widget?: Widget;
  quickReplies?: string[];
}

export type Widget =
  | { type: 'scenario_cards' }
  | { type: 'industry_cards' }
  | { type: 'pain_point_input' }
  | { type: 'objective_input' }
  | { type: 'audience_config' }
  | { type: 'question_editor' }
  | { type: 'sample_size_selector' }
  | { type: 'confirm_summary' }
  | { type: 'progress'; jobId: string; isTest: boolean }
  | { type: 'results' }
  | { type: 'downloads' };

// Industry (loaded from DB via sophie-ontology.ts)
export interface IndustryOption {
  id: string;
  name: string;
  name_zh: string;
  icon: string;
  is_other: boolean;
}

export interface SessionState {
  sessionId: string;
  phase: Phase;
  scenario?: ScenarioConfig;
  industry?: IndustryOption;
  painPoint?: string;
  objective?: string;
  audience: AudienceConfig;
  question?: string;
  options: string[];
  context: string;
  sampleSize: number;
  testJobId?: string;
  testResult?: import('./api').SurveyResult;
  fullJobId?: string;
  fullResult?: import('./api').SurveyResult;
}

export interface ScenarioConfig {
  id: string;
  name: string;
  nameZh: string;
  tagline: string;
  taglineZh: string;
  description: string;
  descriptionZh: string;
  examples: string;
  examplesZh: string;
  icon: string;
  defaultQuestion: string;
  defaultOptions: string[];
  defaultContext: string;
  defaultAudience: Partial<AudienceConfig>;
}

export interface AudienceConfig {
  ageMin: number;
  ageMax: number;
  gender: string;
  housing: string;
  incomeMin: number;
  incomeMax: number;
  ethnicity: string;
  marital: string;
  education: string;
  lifePhase: string;
}

// Predefined scenarios
export const SCENARIOS: ScenarioConfig[] = [
  {
    id: 'policy_simulation',
    name: 'Policy Simulation',
    nameZh: '政策预演',
    tagline: 'Hear Your Nation Before You Announce',
    taglineZh: '政策发布前，先听听民声',
    description: 'Run any draft policy through tens of thousands of AI citizens. See approval ratings by demographic, detect controversy hotspots, and understand emotional responses — before a single word goes public.',
    descriptionZh: '将任何政策草案送入数万名 AI 市民中测试。按人口统计查看支持率、发现争议热点、理解情绪反应——在公开发布之前。',
    examples: 'CPF withdrawal age reform, HDB allocation rule changes, carbon tax adjustments, healthcare subsidy restructuring',
    examplesZh: 'CPF提取年龄改革、HDB分配规则调整、碳税调整、医疗补贴重组',
    icon: '🏛️',
    defaultQuestion: 'The government proposes raising the CPF withdrawal age from 55 to 60, with enhanced interest rates on savings. How would you respond?',
    defaultOptions: [
      'Strongly support — it encourages better retirement planning',
      'Somewhat support — if the enhanced interest rates are attractive enough',
      'Neutral — I need more details before deciding',
      'Somewhat oppose — I want access to my money earlier',
      'Strongly oppose — the government should not restrict my savings further',
      'No opinion / Does not affect me',
    ],
    defaultContext: `You are a resident of Singapore. The Central Provident Fund (CPF) is a mandatory savings scheme.\n- CPF contribution: 20% employee + 17% employer for those under 55\n- Current withdrawal age: 55 (partial), with retirement sum set aside\n- CPF interest rates: OA 2.5%, SA 4%, MA 4%, RA 4%\n- Average CPF balance at 55: ~S$250,000\n- Life expectancy in Singapore: ~84 years\n- Median monthly household income: ~S$10,000`,
    defaultAudience: { ageMin: 21, ageMax: 75 },
  },
  {
    id: 'product_pricing',
    name: 'Product & Pricing Test',
    nameZh: '产品与定价测试',
    tagline: 'Test on 10,000 Consumers, Not 100',
    taglineZh: '用一万人测试，而非一百人',
    description: 'Simulate how different income groups, age brackets, and cultural segments react to your new product concept, pricing tiers, or promotional strategy. Get directional signals in hours, not weeks.',
    descriptionZh: '模拟不同收入群体、年龄段和文化群体对新产品概念、定价层级或促销策略的反应。在数小时内获得方向性信号，而非数周。',
    examples: 'Insurance product pricing sensitivity, F&B new product acceptance, subscription vs one-time purchase preference, retail promotion A/B testing',
    examplesZh: '保险产品定价敏感度、餐饮新品接受度、订阅制 vs 一次性购买偏好、零售促销 A/B 测试',
    icon: '🧪',
    defaultQuestion: 'A new meal subscription service offers unlimited lunch deliveries for S$199/month (vs ~S$12/meal normally). How likely are you to subscribe?',
    defaultOptions: [
      'Very likely — great value, I eat out daily anyway',
      'Somewhat likely — I\'d try it for a month',
      'Neutral — depends on restaurant quality and variety',
      'Unlikely — I prefer cooking or choosing different restaurants',
      'Very unlikely — too expensive for my budget',
      'Not applicable — I don\'t eat lunch regularly',
    ],
    defaultContext: `You are a resident of Singapore. The food delivery and dining landscape:\n- Average lunch cost: S$8-15 at hawker/food court, S$12-25 at restaurants\n- Major delivery platforms: Grab Food, foodpanda, Deliveroo\n- Delivery fees typically S$2-5 per order\n- Average working professional eats out 3-5 times per week for lunch\n- Subscription meal services are a growing trend in Singapore\n- Monthly food expenditure for average household: ~S$1,200`,
    defaultAudience: { ageMin: 21, ageMax: 64 },
  },
  {
    id: 'audience_intelligence',
    name: 'Audience Intelligence',
    nameZh: '受众洞察',
    tagline: 'See the People Surveys Can\'t Reach',
    taglineZh: '看见问卷触达不到的人群',
    description: 'Have real conversations with AI citizens who represent Singapore\'s hardest-to-reach segments. Understand not just what people choose, but why — through dialogue, not checkboxes.',
    descriptionZh: '与代表新加坡最难触达群体的 AI 市民进行真实对话。不仅了解人们的选择，更理解原因——通过对话，而非勾选框。',
    examples: 'Why elderly Malay residents refuse telehealth, what low-income mothers worry about for childcare, how immigrant families perceive public schools',
    examplesZh: '马来老年居民为何拒绝远程医疗、低收入母亲选择托儿所时的真正顾虑、新移民家庭如何看待公立学校',
    icon: '🔍',
    defaultQuestion: 'What is the biggest challenge you face when accessing healthcare services in Singapore?',
    defaultOptions: [
      'Long waiting times at public hospitals and polyclinics',
      'Cost — even with subsidies, out-of-pocket expenses are high',
      'Language barriers — hard to communicate with healthcare staff',
      'Inconvenient locations — clinics are far from where I live',
      'Lack of awareness — I don\'t know what services I\'m entitled to',
      'Cultural or religious considerations not well accommodated',
      'Digital barriers — online booking and telehealth are difficult for me',
      'No major challenges — healthcare access works well for me',
    ],
    defaultContext: `You are a resident of Singapore. Singapore's healthcare system:\n- Public healthcare: restructured hospitals, polyclinics, community hospitals\n- Subsidized rates for citizens (up to 80% at polyclinics)\n- CHAS (Community Health Assist Scheme) for lower/middle income\n- Pioneer/Merdeka Generation benefits for seniors\n- Telehealth adoption growing post-COVID but varies significantly by age and ethnicity\n- ~30% of residents are non-citizens (PRs and work pass holders)\n- 4 official languages: English, Mandarin, Malay, Tamil\n- Significant elderly population (16% aged 65+)`,
    defaultAudience: { ageMin: 18, ageMax: 80 },
  },
];

export const SAMPLE_SIZE_OPTIONS = [20, 1000, 2000, 5000, 20000, 50000, 172000];

export function makeId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}
