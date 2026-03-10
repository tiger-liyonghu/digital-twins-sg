import type { Node } from '@xyflow/react';

// Audience node data
export interface AudienceData {
  label: string;
  ageMin: number;
  ageMax: number;
  gender: string;
  housing: string;
  incomeMin: number;
  incomeMax: number;
  marital: string;
  education: string;
  sampleSize: number;
  // live stats from /api/eligible
  eligibleCount?: number;
  totalPopulation?: number;
  summary?: {
    age_mean?: number;
    income_median?: number;
    gender_dist?: Record<string, number>;
    ethnicity_dist?: Record<string, number>;
  };
}

// Query node data
export interface QueryData {
  label: string;
  question: string;
  options: string[];
  context: string;
  // preset scenario
  presetId?: string;
}

// Result node data
export interface ResultData {
  label: string;
  jobId?: string;
  status?: 'idle' | 'queued' | 'sampling' | 'running' | 'done' | 'error';
  progress?: number;
  total?: number;
  result?: import('./api').SurveyResult;
  error?: string;
}

// Node type aliases (for documentation; use generic Node in practice)
export type AudienceNodeType = Node<AudienceData & Record<string, unknown>, 'audience'>;
export type QueryNodeType = Node<QueryData & Record<string, unknown>, 'query'>;
export type ResultNodeType = Node<ResultData & Record<string, unknown>, 'result'>;

// Insurance backtest presets
export interface ScenarioPreset {
  id: string;
  name: string;
  tag: string;
  question: string;
  options: string[];
  context: string;
  audienceDefaults?: Partial<AudienceData>;
}

export const SCENARIO_PRESETS: ScenarioPreset[] = [
  {
    id: 'BT-011',
    name: 'Protection Adequacy',
    tag: 'INSURANCE',
    question: 'Do you think your current life insurance coverage is sufficient to protect your family financially if something happens to you?',
    options: [
      'Very insufficient — I have little or no coverage',
      'Somewhat insufficient — I have some coverage but not enough',
      'About right — I think my coverage is adequate',
      'More than enough — I\'m well covered',
      'Don\'t know / Haven\'t thought about it',
    ],
    context: `You are a resident of Singapore. Singapore has a multi-layer healthcare financing system:
- MediShield Life: mandatory basic health insurance for all citizens and PRs
- CPF (Central Provident Fund): mandatory savings including MediSave for healthcare
- Dependants' Protection Scheme (DPS): auto-enrolled term life, max S$70,000
- Optional: private life insurance, critical illness coverage, Integrated Shield Plans

Average household income in Singapore is approximately S$10,000-12,000/month.
Housing costs (HDB mortgage) typically S$1,000-2,500/month.
Education costs for children range from minimal (public) to S$20,000+/year (international).
Healthcare costs are rising at 5-8% annually.`,
    audienceDefaults: { ageMin: 21, ageMax: 64, sampleSize: 50 },
  },
  {
    id: 'BT-012',
    name: 'IP Price Hike Response',
    tag: 'INSURANCE',
    question: 'Your Integrated Shield Plan (IP) premium has increased by 15-25% this year. What will you most likely do?',
    options: [
      'Keep my current plan and pay the higher premium',
      'Downgrade to a lower ward class (e.g., Class A → B1)',
      'Remove or reduce my IP rider to lower the cost',
      'Switch to a different insurer with lower premiums',
      'Drop my IP entirely and rely only on MediShield Life',
      'I don\'t have an IP / Not applicable',
    ],
    context: `You are a resident of Singapore. Integrated Shield Plans (IP) are private health insurance plans that top up the basic MediShield Life coverage.
- MediShield Life covers basic public hospital bills (mandatory for all citizens/PRs)
- IPs provide higher coverage: private hospitals, single rooms, specialist care
- Ward classes: A (single room), B1 (4-bed), B2 (6-bed)
- IP premiums are paid via MediSave (CPF healthcare account)
- In 2025, almost all private insurers raised IP premiums by 15-25%
- MOH announced new IP rider requirements effective April 2026, expected to lower new rider premiums by ~30%
- Healthcare cost inflation in Singapore runs at 5-8% annually`,
    audienceDefaults: { ageMin: 25, ageMax: 70, sampleSize: 50 },
  },
  {
    id: 'BT-013',
    name: 'Purchase Barriers',
    tag: 'INSURANCE',
    question: 'What is the main reason you have not purchased (more) life or health insurance?',
    options: [
      'Too expensive / Can\'t afford the premiums',
      'I don\'t understand insurance products well enough',
      'I think my existing coverage (CPF, MediShield Life) is sufficient',
      'I don\'t trust insurance companies or agents',
      'The products available don\'t match my needs',
      'I\'m young and healthy — I don\'t need it yet',
      'I already have adequate private insurance coverage',
      'Other reasons',
    ],
    context: `You are a resident of Singapore. Singapore has several compulsory insurance/savings schemes:
- MediShield Life: basic health insurance (mandatory)
- CareShield Life: long-term care insurance (mandatory for those born 1980+)
- Dependants' Protection Scheme: basic term life (auto-enrolled)
- CPF: mandatory savings (20% employee + 17% employer contribution)

Private insurance is optional and includes: term life, whole life, endowment, investment-linked plans, critical illness, personal accident, and Integrated Shield Plans.
Insurance products can be purchased from tied agents, financial advisers (FA), banks, or online platforms.
Common private insurers include NTUC Income, Great Eastern, AIA, Prudential, Singlife, Manulife, FWD.`,
    audienceDefaults: { ageMin: 21, ageMax: 64, sampleSize: 50 },
  },
  {
    id: 'BT-014',
    name: 'Brand Preference',
    tag: 'INSURANCE',
    question: 'If you were to purchase a new insurance policy today, which insurer would you most likely consider?',
    options: [
      'NTUC Income (Income Insurance)',
      'Great Eastern',
      'AIA',
      'Prudential',
      'Singlife',
      'Manulife',
      'FWD',
      'Other / No preference',
    ],
    context: `You are a resident of Singapore considering purchasing insurance. Major insurers in Singapore include:
- NTUC Income (Income Insurance): Originated as a co-operative, known for affordable positioning
- Great Eastern: Largest insurer in Singapore, subsidiary of OCBC bank
- AIA: Pan-Asian insurer with premium positioning and health focus
- Prudential: UK-headquartered, strong in investment-linked products
- Singlife: Merger of Singlife and Aviva Singapore, digital-first approach
- Manulife: Canadian insurer focused on retirement and investment
- FWD: Pan-Asian digital disruptor

Distribution channels: Financial Advisers represent ~43% of sales, tied agents ~32%, bancassurance ~14%, direct/online ~10% and growing.`,
    audienceDefaults: { ageMin: 21, ageMax: 64, sampleSize: 50 },
  },
  {
    id: 'SV-003',
    name: 'MediShield +20%',
    tag: 'POLICY',
    question: 'The government announces that MediShield Life premiums will increase by 20% over the next 2 years due to rising healthcare costs. Additional subsidies will be provided for lower-income individuals. How would this affect your insurance decisions?',
    options: [
      'No change — I\'ll absorb the increase, it\'s still affordable',
      'I\'ll review and possibly downgrade my IP to offset the cost',
      'I\'ll cut back on other private insurance to compensate',
      'I\'ll increase my MediSave contributions to cover it',
      'I\'m worried — this is becoming unaffordable',
      'I support the increase if it means better coverage',
    ],
    context: `You are a resident of Singapore. MediShield Life is the mandatory basic health insurance for all citizens and PRs.
- Current premiums range from ~S$130/year (age 21-30) to ~S$2,400/year (age 81-85)
- Premiums are paid from MediSave (CPF healthcare savings)
- Government provides premium subsidies of up to 60% for lower/middle-income seniors
- MediShield Life coverage limit was raised to S$200,000/policy year in April 2025
- The government committed S$4.1B to support the latest MediShield Life review
- Healthcare costs in Singapore have been rising at 5-8% annually
- Many residents also have Integrated Shield Plans (IP) that top up MediShield Life`,
    audienceDefaults: { ageMin: 21, ageMax: 75, sampleSize: 50 },
  },
  {
    id: 'SV-004',
    name: 'Platform Worker Insurance',
    tag: 'POLICY',
    question: 'The government is considering requiring platform companies (Grab, Deliveroo, etc.) to provide basic insurance coverage for their workers. As a Singapore resident, what is your view?',
    options: [
      'Strongly support — platform workers deserve protection',
      'Support — but concerned about higher service fees being passed to consumers',
      'Neutral — I don\'t have a strong opinion',
      'Oppose — it\'s the worker\'s personal responsibility',
      'Oppose — it will hurt the gig economy and reduce flexible work options',
    ],
    context: `You are a resident of Singapore. The gig/platform economy is growing:
- Platform workers (Grab drivers, Deliveroo riders, etc.) are classified as independent contractors
- They do not receive employer CPF contributions or group insurance benefits
- Their income is irregular and often lower than full-time employment
- They must arrange their own insurance coverage independently
- Basic government schemes (MediShield Life, CareShield Life) still apply to citizens/PRs
- The government has been studying options for platform worker protections
- Similar debates are happening globally (EU, UK, Australia have various approaches)`,
    audienceDefaults: { ageMin: 21, ageMax: 64, sampleSize: 50 },
  },
];
