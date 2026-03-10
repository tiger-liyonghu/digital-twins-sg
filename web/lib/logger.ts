import { supabase } from './supabase';

// Log a conversation message
export async function logConversation(
  sessionId: string,
  role: 'sophie' | 'client' | 'system',
  content: string,
  phase: string,
  metadata?: Record<string, unknown>
) {
  try {
    await supabase.from('dt_conversations').insert({
      session_id: sessionId,
      role,
      content,
      phase,
      metadata: metadata || {},
    });
  } catch (e) {
    console.error('Failed to log conversation:', e);
  }
}

// Log an error/incident
export async function logError(
  sessionId: string,
  category: 'api_error' | 'quality' | 'distribution' | 'prompt' | 'client_feedback' | 'performance' | 'validation',
  severity: 'critical' | 'warning' | 'info',
  detail: Record<string, unknown>,
  jobId?: string,
  agentId?: string,
  resolution?: string
) {
  try {
    await supabase.from('dt_error_logs').insert({
      session_id: sessionId,
      job_id: jobId,
      agent_id: agentId,
      category,
      severity,
      detail,
      resolution,
    });
  } catch (e) {
    console.error('Failed to log error:', e);
  }
}

// Log quality incident
export async function logQualityIncident(
  jobId: string,
  agentId: string,
  issueType: string,
  promptUsed: string,
  rawResponse: string,
  rewardScore: number | null,
  wasExcluded: boolean
) {
  try {
    await supabase.from('dt_quality_incidents').insert({
      job_id: jobId,
      agent_id: agentId,
      issue_type: issueType,
      prompt_used: promptUsed,
      raw_response: rawResponse,
      reward_score: rewardScore,
      was_excluded: wasExcluded,
    });
  } catch (e) {
    console.error('Failed to log quality incident:', e);
  }
}

// Create a new session
export async function createSession(scenarioId?: string): Promise<string> {
  const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  try {
    await supabase.from('dt_sessions').insert({
      id,
      scenario_id: scenarioId,
      status: 'active',
      title: `Research Session — ${new Date().toLocaleDateString()}`,
    });
  } catch (e) {
    console.error('Failed to create session:', e);
  }
  return id;
}

// Update session
export async function updateSession(
  sessionId: string,
  updates: Record<string, unknown>
) {
  try {
    await supabase.from('dt_sessions').update({
      ...updates,
      updated_at: new Date().toISOString(),
    }).eq('id', sessionId);
  } catch (e) {
    console.error('Failed to update session:', e);
  }
}

// Save survey job
export async function saveSurveyJob(
  sessionId: string,
  jobId: string,
  jobType: 'test_run' | 'full_run',
  params: Record<string, unknown>
) {
  try {
    await supabase.from('dt_survey_jobs').insert({
      id: jobId,
      session_id: sessionId,
      job_type: jobType,
      params,
      status: 'queued',
    });
  } catch (e) {
    console.error('Failed to save survey job:', e);
  }
}

// Update survey job status
export async function updateSurveyJob(
  jobId: string,
  updates: Record<string, unknown>
) {
  try {
    await supabase.from('dt_survey_jobs').update(updates).eq('id', jobId);
  } catch (e) {
    console.error('Failed to update survey job:', e);
  }
}

// Save survey results
export async function saveSurveyResults(
  jobId: string,
  sessionId: string,
  resultData: Record<string, unknown>,
  analysis?: string
) {
  try {
    await supabase.from('dt_survey_results').insert({
      job_id: jobId,
      session_id: sessionId,
      result_data: resultData,
      analysis,
    });
  } catch (e) {
    console.error('Failed to save survey results:', e);
  }
}

// Save a report/file reference
export async function saveFile(
  sessionId: string,
  fileType: string,
  fileName: string,
  storagePath: string,
  fileSize: number
) {
  try {
    await supabase.from('dt_client_files').insert({
      session_id: sessionId,
      file_type: fileType,
      file_name: fileName,
      storage_path: storagePath,
      file_size: fileSize,
    });
  } catch (e) {
    console.error('Failed to save file record:', e);
  }
}

// Log system learning
export async function logSystemLearning(
  sourceIncidentIds: string[],
  learningType: string,
  description: string,
  beforeState: string,
  afterState: string
) {
  try {
    await supabase.from('dt_system_learnings').insert({
      source_incident_ids: sourceIncidentIds,
      learning_type: learningType,
      description,
      before_state: beforeState,
      after_state: afterState,
    });
  } catch (e) {
    console.error('Failed to log system learning:', e);
  }
}
