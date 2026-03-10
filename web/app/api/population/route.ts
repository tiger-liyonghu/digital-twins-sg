import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export const dynamic = 'force-dynamic';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
);

// Count by a single column
async function countBy(column: string): Promise<Record<string, number>> {
  const counts: Record<string, number> = {};
  let offset = 0;
  const limit = 1000;

  while (true) {
    const { data, error } = await supabase
      .from('agents')
      .select(column)
      .range(offset, offset + limit - 1);
    if (error || !data || data.length === 0) break;
    for (const row of data) {
      const r = row as unknown as Record<string, unknown>;
      const val = String(r[column] ?? 'null');
      counts[val] = (counts[val] || 0) + 1;
    }
    if (data.length < limit) break;
    offset += limit;
  }
  return counts;
}

// Count by two columns (joint distribution)
async function countByTwo(col1: string, col2: string): Promise<Record<string, Record<string, number>>> {
  const counts: Record<string, Record<string, number>> = {};
  let offset = 0;
  const limit = 1000;

  while (true) {
    const { data, error } = await supabase
      .from('agents')
      .select(`${col1},${col2}`)
      .range(offset, offset + limit - 1);
    if (error || !data || data.length === 0) break;
    for (const row of data) {
      const r = row as unknown as Record<string, unknown>;
      const v1 = String(r[col1] ?? 'null');
      const v2 = String(r[col2] ?? 'null');
      if (!counts[v1]) counts[v1] = {};
      counts[v1][v2] = (counts[v1][v2] || 0) + 1;
    }
    if (data.length < limit) break;
    offset += limit;
  }
  return counts;
}

// Compute summary stats
async function computeStats(): Promise<{ median_age: number; median_income: number; total: number }> {
  // Get all ages
  const ages: number[] = [];
  const incomes: number[] = [];
  let offset = 0;
  const limit = 1000;

  while (true) {
    const { data, error } = await supabase
      .from('agents')
      .select('age,monthly_income')
      .range(offset, offset + limit - 1);
    if (error || !data || data.length === 0) break;
    for (const row of data) {
      const r = row as unknown as Record<string, unknown>;
      if (r.age != null) ages.push(r.age as number);
      if (r.monthly_income != null && (r.monthly_income as number) > 0) incomes.push(r.monthly_income as number);
    }
    if (data.length < limit) break;
    offset += limit;
  }

  ages.sort((a, b) => a - b);
  incomes.sort((a, b) => a - b);

  return {
    median_age: ages[Math.floor(ages.length / 2)] || 0,
    median_income: incomes[Math.floor(incomes.length / 2)] || 0,
    total: ages.length,
  };
}

export async function GET() {
  try {
    // Run all queries in parallel
    const [
      genderDist,
      ethnicityDist,
      educationDist,
      housingDist,
      incomeBandDist,
      maritalDist,
      ageGroupDist,
      planningAreaDist,
      religionDist,
      socialMediaDist,
      // Joint distributions
      ethnicityEducation,
      genderIncome,
      housingIncome,
      stats,
    ] = await Promise.all([
      countBy('gender'),
      countBy('ethnicity'),
      countBy('education_level'),
      countBy('housing_type'),
      countBy('income_band'),
      countBy('marital_status'),
      countBy('age_group'),
      countBy('planning_area'),
      countBy('religion'),
      countBy('social_media_usage'),
      countByTwo('ethnicity', 'education_level'),
      countByTwo('gender', 'income_band'),
      countByTwo('housing_type', 'income_band'),
      computeStats(),
    ]);

    return NextResponse.json({
      total: stats.total,
      median_age: stats.median_age,
      median_income: stats.median_income,
      marginals: {
        gender: genderDist,
        ethnicity: ethnicityDist,
        education_level: educationDist,
        housing_type: housingDist,
        income_band: incomeBandDist,
        marital_status: maritalDist,
        age_group: ageGroupDist,
        planning_area: planningAreaDist,
        religion: religionDist,
        social_media_usage: socialMediaDist,
      },
      joints: {
        ethnicity_education: ethnicityEducation,
        gender_income: genderIncome,
        housing_income: housingIncome,
      },
    });
  } catch (err) {
    console.error('Population API error:', err);
    return NextResponse.json({ error: 'Failed to fetch population data' }, { status: 500 });
  }
}
