// ============================================================
// SINGAPORE PARAMETER REGISTRY — Single Source of Truth
// All time-sensitive policy/demographic parameters live here.
// When government updates a value, change it HERE ONLY.
// ============================================================
// Version:       2026-03 (March 2026)
// Last verified:  2026-03-07
// Next review:    2026-04-07 (monthly cycle)
// Sources:        CPF Board, DOS, HDB, MOM (see inline references)
// ============================================================

const SG_PARAMS = {

  _meta: {
    version: '2026-03',
    last_verified: '2026-03-07',
    next_review: '2026-04-07',
    maintainer: 'Expert Advisory Board — monthly learning cycle'
  },

  // ──────────────────────────────────────────────────────────
  // CPF — Central Provident Fund
  // Source: https://www.cpf.gov.sg/employer/employer-obligations/how-much-cpf-contributions-to-pay
  // Updated: Jan 2026 rates
  // ──────────────────────────────────────────────────────────
  cpf: {
    wage_ceiling: 8000,           // OW ceiling $/month (was 6800 pre-2025)
    additional_wage_ceiling: 102000, // AW ceiling $/year (2026)

    // Employee + Employer combined rates
    rates: [
      { label: '≤55',    age_min: 0,  age_max: 55, oa: 0.23,  sa: 0.06,  ma: 0.08,  total: 0.37  },
      { label: '55-60',  age_min: 55, age_max: 60, oa: 0.17,  sa: 0.055, ma: 0.115, total: 0.34  },
      { label: '60-65',  age_min: 60, age_max: 65, oa: 0.10,  sa: 0.045, ma: 0.105, total: 0.25  },
      { label: '65-70',  age_min: 65, age_max: 70, oa: 0.065, sa: 0.03,  ma: 0.08,  total: 0.175 },
      { label: '>70',    age_min: 70, age_max: 999,oa: 0.05,  sa: 0.02,  ma: 0.06,  total: 0.13  },
    ],

    // PR graduated rates (fraction of citizen rate)
    pr_graduation: [
      { years: '0-2', fraction: 0.60 },
      { years: '2-3', fraction: 0.80 },
      { years: '3+',  fraction: 1.00 },
    ],

    // Retirement sums (2025 values)
    full_retirement_sum: 213000,
    basic_retirement_sum: 106500,
  },

  // ──────────────────────────────────────────────────────────
  // POPULATION — Demographics
  // Source: https://www.population.gov.sg/files/media-centre/publications/Population_in_Brief_2025.pdf
  // ──────────────────────────────────────────────────────────
  population: {
    total: 6110000,               // June 2025 (was 5800000)
    citizens: 3640000,
    prs: 560000,
    non_residents: 1910000,
    synthetic_agents: 172000,     // 148K NVIDIA + 24K children
    scale_factor: 35.5,           // 6.11M / 172K

    ethnicity: { chinese: 0.739, malay: 0.135, indian: 0.090, others: 0.035 },
    gender: { male: 0.486, female: 0.514 },

    residency: {
      citizen: 0.599, pr: 0.088, ep: 0.032, sp: 0.033,
      wp: 0.162, fdw: 0.042, dp: 0.022, stp: 0.022
    },

    median_income: 5775,          // MOM 2025 monthly median
  },

  // ──────────────────────────────────────────────────────────
  // HDB — Housing & Development Board
  // Source: https://www.hdb.gov.sg/residential/buying-a-flat
  // ──────────────────────────────────────────────────────────
  hdb: {
    // Ethnic Integration Policy (EIP) quotas
    // IMPORTANT: block limit ≥ neighborhood limit (block is smaller unit, less strict)
    eip: {
      chinese:      { block: 0.87, neighborhood: 0.84 },  // was swapped: 84/87
      malay:        { block: 0.22, neighborhood: 0.25 },
      indian_others:{ block: 0.10, neighborhood: 0.13 },
    },

    // Housing type distribution (Census)
    distribution: { hdb: 0.772, condo: 0.179, landed: 0.047 },

    // New classification (2024+)
    flat_types: ['Standard', 'Plus', 'Prime'],  // replaces mature/non-mature
  },

  // ──────────────────────────────────────────────────────────
  // HOUSEHOLD
  // Source: GHS 2025
  // ──────────────────────────────────────────────────────────
  household: {
    mean_size: 3.06,
    size_distribution: {1:0.153, 2:0.188, 3:0.180, 4:0.223, 5:0.155, 6:0.065, 7:0.026, 8:0.010},
  },

  // ──────────────────────────────────────────────────────────
  // NATIONAL SERVICE
  // ──────────────────────────────────────────────────────────
  ns: {
    enlistment_age: 18,
    ord_age: 20,
    reservist_end_age: 40,
    statuses: ['NOT_APPLICABLE', 'PRE_ENLISTMENT', 'SERVING_NSF', 'ACTIVE_NSMEN', 'COMPLETED', 'EXEMPT'],
  },

  // ──────────────────────────────────────────────────────────
  // INCOME MODEL
  // Source: MOM Labour Force Report 2025
  // ──────────────────────────────────────────────────────────
  income: {
    education_multipliers: {
      No_Formal: 0.5, Primary: 0.6, Secondary: 0.7, Post_Secondary: 0.85,
      Polytechnic: 1.0, University: 1.4, Postgraduate: 1.8
    },
    age_multipliers: {
      'lt25': 0.5, '25-35': 0.85, '35-45': 1.0, '45-55': 1.05,
      '55-63': 0.90, '63-70': 0.50, 'gt70': 0.0
    },
  },

  // ──────────────────────────────────────────────────────────
  // MEDIA CHANNELS — by age tier
  // Source: Hashmeta Social Media Landscape 2025
  // ──────────────────────────────────────────────────────────
  media: {
    young:  ['tiktok', 'instagram', 'xiaohongshu', 'youtube', 'telegram'],
    middle: ['facebook', 'whatsapp', 'straits_times', 'cna', 'linkedin'],
    senior: ['straits_times', 'tv', 'whatsapp', 'facebook', 'radio', 'print'],
  },

  // ──────────────────────────────────────────────────────────
  // LLM / COST
  // ──────────────────────────────────────────────────────────
  llm: {
    providers: {
      deepseek: {
        base_url: 'https://api.deepseek.com/v1',
        model: 'deepseek-chat',
        price_per_1k_tokens: 0.0007,
        cache_hit_price_per_1m: 0.07,
        cache_miss_price_per_1m: 0.56,
        semaphore: 30,
        tcp_limit: 40,
      },
      sealion: {
        base_url: 'https://api.sea-lion.ai/v1',
        model: 'aisingapore/Gemma-SEA-LION-v4-27B-IT',
        price_per_1k_tokens: 0.0,        // free trial tier
        semaphore: 5,                      // 10 req/min rate limit
        tcp_limit: 10,
        note: 'AISG SEA-LION — best for Singapore/SEA context, Singlish',
      },
    },
    active_provider: 'deepseek',           // switch to 'sealion' to test
    temperature: 0.7,
    max_tokens: 300,
    retry_attempts: 3,
    timeout_ms: 30000,
  },

  // ──────────────────────────────────────────────────────────
  // GE2025 BACKTEST BENCHMARKS
  // ──────────────────────────────────────────────────────────
  backtest: {
    // ge2025: pending — to be designed and run separately
    presidential_2023: { predicted_tharman: 0.671, actual_tharman: 0.704, deviation_pp: 3.3, mae_pp: 2.7, n: 1000, method: 'VS+RP', status: 'completed' },
    gst_2024: { predicted_cut: 0.73, actual_cut: 0.60, deviation_pp: 13, mae_pp: 13, n: 100, status: 'completed' },
  },

  // ──────────────────────────────────────────────────────────
  // HELPER: get CPF rate for a given age
  // ──────────────────────────────────────────────────────────
  getCpfRate(age) {
    const bracket = this.cpf.rates.find(r => age >= r.age_min && age < r.age_max);
    return bracket || this.cpf.rates[this.cpf.rates.length - 1];
  },

  getCpfContribution(income, age) {
    const rate = this.getCpfRate(age);
    return Math.round(Math.min(income, this.cpf.wage_ceiling) * rate.total);
  },
};

// Make globally available
if (typeof window !== 'undefined') window.SG_PARAMS = SG_PARAMS;
