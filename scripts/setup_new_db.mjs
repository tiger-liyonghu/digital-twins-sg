#!/usr/bin/env node
/**
 * Setup new Supabase database schema via Management API
 * Uses supabase db execute approach
 */
import { readFileSync } from 'fs';
import { execSync } from 'child_process';

const PROJECT_REF = 'rndfpyuuredtqncegygi';
const SQL_FILE = new URL('../supabase/migrations_new/00001_full_schema.sql', import.meta.url);

const sql = readFileSync(SQL_FILE, 'utf-8');

// Split SQL by semicolons, filter empty
const statements = sql
  .split(/;\s*\n/)
  .map(s => s.trim())
  .filter(s => s.length > 0 && !s.startsWith('--'));

console.log(`Total statements: ${statements.length}`);

// Execute via supabase CLI linked project
// We need to use the Management API endpoint
const SUPABASE_ACCESS_TOKEN = process.env.SUPABASE_ACCESS_TOKEN;

if (!SUPABASE_ACCESS_TOKEN) {
  console.log('No access token found. Trying supabase db push approach...');

  // Alternative: write a temp migration and push
  try {
    const result = execSync(
      `cd "${new URL('..', import.meta.url).pathname}" && supabase db push --linked --project-ref ${PROJECT_REF}`,
      { encoding: 'utf-8', timeout: 30000 }
    );
    console.log(result);
  } catch (e) {
    console.error('db push failed:', e.message);
    console.log('\nTrying Management API...');

    // Use Management API
    const resp = await fetch(`https://api.supabase.com/v1/projects/${PROJECT_REF}/database/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${SUPABASE_ACCESS_TOKEN || ''}`,
      },
      body: JSON.stringify({ query: sql }),
    });

    if (resp.ok) {
      console.log('Schema created successfully!');
    } else {
      console.error('API Error:', await resp.text());
    }
  }
  process.exit(0);
}

// Use Management API directly
const resp = await fetch(`https://api.supabase.com/v1/projects/${PROJECT_REF}/database/query`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${SUPABASE_ACCESS_TOKEN}`,
  },
  body: JSON.stringify({ query: sql }),
});

if (resp.ok) {
  const data = await resp.json();
  console.log('Schema created successfully!', data);
} else {
  console.error('Error:', resp.status, await resp.text());
}
