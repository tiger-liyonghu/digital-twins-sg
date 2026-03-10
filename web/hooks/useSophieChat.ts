'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import type { Phase, SophieMessage, SessionState, ScenarioConfig, AudienceConfig, IndustryOption } from '@/lib/sophie-types';
import { makeId } from '@/lib/sophie-types';
import { submitSurvey, getJobStatus } from '@/lib/api';
import {
  logConversation,
  logError,
  createSession,
  updateSession,
  saveSurveyJob,
  updateSurveyJob,
  saveSurveyResults,
} from '@/lib/logger';

function sophieMsg(content: string, phase: Phase, widget?: SophieMessage['widget'], quickReplies?: string[]): SophieMessage {
  return { id: makeId(), role: 'sophie', content, timestamp: new Date().toISOString(), phase, widget, quickReplies };
}

function clientMsg(content: string, phase: Phase): SophieMessage {
  return { id: makeId(), role: 'client', content, timestamp: new Date().toISOString(), phase };
}

export function useSophieChat(zh: boolean, locale: string) {
  const [messages, setMessages] = useState<SophieMessage[]>([]);
  const [completedWidgets, setCompletedWidgets] = useState<Set<string>>(new Set());
  const [session, setSession] = useState<SessionState>({
    sessionId: '',
    phase: 'welcome',
    audience: { ageMin: 21, ageMax: 64, gender: 'all', housing: 'all', incomeMin: 0, incomeMax: 0, ethnicity: 'all', marital: 'all', education: 'all', lifePhase: 'all' },
    options: [],
    context: '',
    sampleSize: 2000,
  });
  const [inputText, setInputText] = useState('');
  const [isPolling, setIsPolling] = useState(false);
  const [isSophieThinking, setIsSophieThinking] = useState(false);
  const [pollProgress, setPollProgress] = useState({ progress: 0, total: 0, interim: {} as Record<string, number> });
  const [discoveryConv, setDiscoveryConv] = useState<{ role: 'sophie' | 'client'; content: string }[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval>>();
  const initialized = useRef(false);

  const completeWidget = useCallback((msgId: string) => {
    setCompletedWidgets((prev) => new Set(prev).add(msgId));
  }, []);

  const addMessage = useCallback((msg: SophieMessage) => {
    setMessages((prev) => [...prev, msg]);
    logConversation(session.sessionId, msg.role, msg.content, msg.phase);
  }, [session.sessionId]);

  const updatePhase = useCallback((phase: Phase) => {
    setSession((s) => ({ ...s, phase }));
    updateSession(session.sessionId, { metadata: { phase } });
  }, [session.sessionId]);

  // Initialize
  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    (async () => {
      const sid = await createSession();
      setSession((s) => ({ ...s, sessionId: sid }));

      const welcome = sophieMsg(
        zh
          ? '你好，我是 Sophie。你想调研什么方向？'
          : "Hi, I'm Sophie. What area would you like to research?",
        'welcome',
        { type: 'scenario_cards' }
      );
      setMessages([welcome]);
      logConversation(sid, 'sophie', welcome.content, 'welcome');
    })();
  }, [zh]);

  // ─── Step 1: Scenario selected ──
  const handleScenarioSelect = useCallback((scenario: ScenarioConfig, msgId: string) => {
    completeWidget(msgId);
    addMessage(clientMsg(zh ? scenario.nameZh : scenario.name, 'scenario_select'));
    setSession((s) => ({ ...s, scenario }));
    updatePhase('industry_select');
    addMessage(sophieMsg(
      zh ? '你是哪个行业的？' : 'Which industry are you in?',
      'industry_select',
      { type: 'industry_cards' }
    ));
  }, [zh, addMessage, updatePhase, completeWidget]);

  // ─── Step 2: Industry selected ──
  const handleIndustrySelect = useCallback(async (industry: IndustryOption, msgId: string) => {
    completeWidget(msgId);
    addMessage(clientMsg(zh ? industry.name_zh : industry.name, 'industry_select'));
    setSession((s) => ({ ...s, industry }));
    updatePhase('pain_point');
    setIsSophieThinking(true);

    try {
      const res = await fetch('/api/sophie', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'probe',
          scenarioId: session.scenario?.id || '',
          scenarioName: zh ? (session.scenario?.nameZh || '') : (session.scenario?.name || ''),
          industryId: industry.id,
          conversation: [],
          locale,
        }),
      });
      const data = await res.json();
      setIsSophieThinking(false);
      addMessage(sophieMsg(data.reply, 'pain_point', undefined, data.quickReplies || []));
      setDiscoveryConv([{ role: 'sophie', content: data.reply }]);
    } catch {
      setIsSophieThinking(false);
      const fallback = zh
        ? '有意思！你具体想了解什么？比如某个政策的公众反应，还是某个产品的市场接受度？'
        : "Interesting! What specifically would you like to explore? For example, public reaction to a policy, or market acceptance of a product?";
      addMessage(sophieMsg(fallback, 'pain_point'));
      setDiscoveryConv([{ role: 'sophie', content: fallback }]);
    }
  }, [zh, locale, session.scenario, addMessage, updatePhase, completeWidget]);

  // ─── Discovery: client message ──
  const handleDiscoveryMessage = useCallback(async (text: string) => {
    const newConv = [...discoveryConv, { role: 'client' as const, content: text }];
    setDiscoveryConv(newConv);
    setIsSophieThinking(true);

    try {
      const res = await fetch('/api/sophie', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'probe',
          scenarioId: session.scenario?.id || '',
          scenarioName: zh ? (session.scenario?.nameZh || '') : (session.scenario?.name || ''),
          industryId: session.industry?.id || 'other',
          conversation: newConv,
          locale,
        }),
      });
      const data = await res.json();

      if (data.ready) {
        const designMsg = zh
          ? '好的，我已经了解你的需求了。让我来设计问卷...'
          : "Got it, I have a clear picture now. Let me design the survey...";
        addMessage(sophieMsg(designMsg, 'objective'));

        const designRes = await fetch('/api/sophie', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'design_survey',
            scenarioId: session.scenario?.id || '',
            scenarioName: zh ? (session.scenario?.nameZh || '') : (session.scenario?.name || ''),
            industryId: session.industry?.id || 'other',
            conversation: newConv,
            locale,
          }),
        });
        const survey = await designRes.json();
        setIsSophieThinking(false);

        if (survey.error) {
          addMessage(sophieMsg(survey.error, 'objective'));
          return;
        }

        setSession((s) => ({
          ...s,
          question: survey.question,
          options: survey.options,
          context: survey.context,
          audience: { ...s.audience, ageMin: survey.audience?.ageMin ?? 21, ageMax: survey.audience?.ageMax ?? 64 },
        }));
        updatePhase('confirm');

        const rationale = survey.rationale
          ? `\n\n${zh ? '设计思路：' : 'Design rationale: '}${survey.rationale}`
          : '';
        addMessage(sophieMsg(
          (zh ? '问卷已设计好。你可以修改任何内容，或直接启动调研。' : "Here's the survey I've designed. Edit anything you'd like, or launch when ready.") + rationale,
          'confirm',
          { type: 'confirm_summary' }
        ));
      } else {
        setIsSophieThinking(false);
        addMessage(sophieMsg(data.reply, 'pain_point', undefined, data.quickReplies || []));
        setDiscoveryConv([...newConv, { role: 'sophie', content: data.reply }]);
      }
    } catch {
      setIsSophieThinking(false);
      addMessage(sophieMsg(
        zh ? '出了点问题，你能再说一下吗？' : 'Something went wrong. Could you say that again?',
        'pain_point'
      ));
    }
  }, [discoveryConv, session.scenario, session.industry?.id, zh, locale, addMessage, updatePhase]);

  // ─── Upload questionnaire ──
  const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = '';

    addMessage(clientMsg(zh ? `[上传文件] ${file.name}` : `[Uploaded] ${file.name}`, session.phase));
    setIsSophieThinking(true);

    let fileText = '';
    try {
      fileText = await file.text();
    } catch {
      setIsSophieThinking(false);
      addMessage(sophieMsg(
        zh ? '无法读取文件，请上传文本格式的文件（.txt, .csv, .md）。' : 'Could not read the file. Please upload a text file (.txt, .csv, .md).',
        session.phase
      ));
      return;
    }

    addMessage(sophieMsg(zh ? '正在分析你的问卷...' : 'Analyzing your questionnaire...', 'objective'));

    try {
      const res = await fetch('/api/sophie', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'parse_upload',
          scenarioId: session.scenario?.id || '',
          scenarioName: zh ? (session.scenario?.nameZh || '') : (session.scenario?.name || ''),
          industryId: session.industry?.id || 'other',
          fileText,
          locale,
        }),
      });
      const data = await res.json();
      setIsSophieThinking(false);

      if (data.error) {
        addMessage(sophieMsg(data.error, session.phase));
        return;
      }

      setSession((s) => ({
        ...s,
        painPoint: data.painPoint,
        question: data.question,
        options: data.options,
        context: data.context,
        audience: { ...s.audience, ageMin: data.audience?.ageMin ?? 21, ageMax: data.audience?.ageMax ?? 64 },
      }));
      updatePhase('confirm');

      const rationale = data.rationale
        ? `\n\n${zh ? '解析结果：' : 'Extracted: '}${data.rationale}`
        : '';
      addMessage(sophieMsg(
        (zh ? '我已从你的问卷中提取了调研问题和选项。你可以修改任何内容，或直接启动调研。'
          : "I've extracted the survey question and options from your questionnaire. Edit anything you'd like, or launch when ready.") + rationale,
        'confirm',
        { type: 'confirm_summary' }
      ));
    } catch {
      setIsSophieThinking(false);
      addMessage(sophieMsg(
        zh ? '解析出了问题，请重试或直接告诉我你的需求。' : 'Something went wrong parsing. Please retry or just tell me what you need.',
        session.phase
      ));
    }
  }, [zh, locale, session, addMessage, updatePhase]);

  // ─── Launch survey ──
  const handleLaunch = useCallback(async (
    question: string, options: string[], audience: AudienceConfig, sampleSize: number
  ) => {
    const isTest = sampleSize <= 20;
    const jobId = makeId();
    const phase: Phase = isTest ? 'test_run' : 'full_run';

    setSession((s) => ({ ...s, question, options, audience, sampleSize }));
    updatePhase(phase);

    addMessage(sophieMsg(
      isTest
        ? (zh ? '试跑中，20 个居民正在回答...' : 'Running test — 20 citizens responding...')
        : (zh ? `正式调研启动，${sampleSize.toLocaleString()} 个居民正在回答...` : `Survey launched — ${sampleSize.toLocaleString()} citizens responding...`),
      phase,
      { type: 'progress', jobId, isTest }
    ));

    await saveSurveyJob(session.sessionId, jobId, isTest ? 'test_run' : 'full_run', {
      question, options, sampleSize, audience,
    });

    try {
      const { job_id } = await submitSurvey({
        client_name: 'Sophie',
        question,
        options,
        context: session.context,
        sample_size: sampleSize,
        age_min: audience.ageMin,
        age_max: audience.ageMax,
        gender: audience.gender !== 'all' ? audience.gender : undefined,
        housing: audience.housing !== 'all' ? audience.housing : undefined,
        income_min: audience.incomeMin || undefined,
        income_max: audience.incomeMax || undefined,
        ethnicity: audience.ethnicity !== 'all' ? audience.ethnicity : undefined,
        marital: audience.marital !== 'all' ? audience.marital : undefined,
        education: audience.education !== 'all' ? audience.education : undefined,
        life_phase: audience.lifePhase !== 'all' ? audience.lifePhase : undefined,
      });

      setSession((s) => isTest ? { ...s, testJobId: job_id } : { ...s, fullJobId: job_id });
      setIsPolling(true);
      setPollProgress({ progress: 0, total: sampleSize, interim: {} });

      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = setInterval(async () => {
        try {
          const status = await getJobStatus(job_id);
          setPollProgress({
            progress: status.progress,
            total: status.total,
            interim: status.result?.overall.choice_distribution || {},
          });

          await updateSurveyJob(jobId, { status: status.status, progress: status.progress, total: status.total });

          if (status.status === 'done' && status.result) {
            clearInterval(pollRef.current);
            setIsPolling(false);

            const result = status.result;
            setSession((s) => isTest ? { ...s, testResult: result } : { ...s, fullResult: result });

            await saveSurveyResults(jobId, session.sessionId, result as unknown as Record<string, unknown>);
            await updateSurveyJob(jobId, { status: 'done', completed_at: new Date().toISOString(), quality_summary: result.quality });

            const resultsPhase: Phase = isTest ? 'test_analysis' : 'results';
            updatePhase(resultsPhase);

            addMessage(sophieMsg(
              isTest
                ? (zh
                    ? `试跑完成！${result.n_respondents} 个居民已回答。看看结果，满意的话可以扩大规模。`
                    : `Test done! ${result.n_respondents} citizens responded. Check the results — scale up when ready.`)
                : (zh
                    ? `调研完成！${result.n_respondents} 个居民已回答，费用 $${result.cost.total_cost_usd.toFixed(3)}。有什么问题尽管问我。`
                    : `Survey complete! ${result.n_respondents} citizens responded, cost $${result.cost.total_cost_usd.toFixed(3)}. Ask me anything about the results.`),
              resultsPhase,
              { type: 'results' }
            ));
          } else if (status.status === 'error') {
            clearInterval(pollRef.current);
            setIsPolling(false);
            logError(session.sessionId, 'api_error', 'critical', { error: status.error, jobId: job_id });
            addMessage(sophieMsg(zh ? `出错了：${status.error}` : `Error: ${status.error}`, phase));
          }
        } catch (e) {
          console.error('Poll error:', e);
        }
      }, 2000);
    } catch (e) {
      setIsPolling(false);
      logError(session.sessionId, 'api_error', 'critical', { error: String(e) });
      addMessage(sophieMsg(
        zh ? '连不上后端服务，请确认 API 在运行。' : "Can't reach the backend. Make sure the API server is running.",
        phase
      ));
    }
  }, [session, zh, addMessage, updatePhase]);

  const handleScaleUp = useCallback((n?: number) => {
    handleLaunch(session.question || '', session.options, session.audience, n || 2000);
  }, [session, handleLaunch]);

  const handleRerun = useCallback(() => {
    setDiscoveryConv([]);
    updatePhase('welcome');
    addMessage(sophieMsg(
      zh ? '好的，重新来。选个方向：' : "OK, let's start fresh. Pick a direction:",
      'welcome',
      { type: 'scenario_cards' }
    ));
  }, [zh, addMessage, updatePhase]);

  // ─── Send message (discovery + QA) ──
  const handleSendMessage = useCallback(async () => {
    const text = inputText.trim();
    if (!text || isSophieThinking) return;
    setInputText('');

    addMessage(clientMsg(text, session.phase));

    if (session.phase === 'pain_point' || session.phase === 'objective') {
      await handleDiscoveryMessage(text);
      return;
    }

    if (session.phase === 'test_analysis') {
      const lower = text.toLowerCase();
      if (lower.includes('full') || lower.includes('正式') || lower.includes('扩大') || lower.includes('scale') || lower.includes('2000') || lower.includes('go')) {
        handleScaleUp();
        return;
      }
    }

    if (session.fullResult || session.testResult) {
      const result = session.fullResult || session.testResult!;
      const sorted = Object.entries(result.overall.choice_distribution).sort(([, a], [, b]) => b - a);
      const top = sorted[0];
      const second = sorted[1];

      addMessage(sophieMsg(
        zh
          ? `最多人选了「${top[0]}」（${Math.round((top[1] / result.n_respondents) * 100)}%），其次是「${second?.[0] || '—'}」（${second ? Math.round((second[1] / result.n_respondents) * 100) : 0}%）。\n\n你还想了解什么？`
          : `Top choice: "${top[0]}" (${Math.round((top[1] / result.n_respondents) * 100)}%), followed by "${second?.[0] || '—'}" (${second ? Math.round((second[1] / result.n_respondents) * 100) : 0}%).\n\nWhat else would you like to know?`,
        'qa'
      ));
    }
  }, [inputText, isSophieThinking, session, zh, addMessage, handleDiscoveryMessage, handleScaleUp]);

  // Quick reply handler
  const handleQuickReply = useCallback((qr: string, msgId: string) => {
    const isOther = qr === '其他' || qr.toLowerCase() === 'other';
    setCompletedWidgets((prev) => new Set(prev).add(`qr-${msgId}`));
    if (!isOther) {
      addMessage(clientMsg(qr, session.phase));
      handleDiscoveryMessage(qr);
    }
    return isOther; // caller should focus input if true
  }, [addMessage, session.phase, handleDiscoveryMessage]);

  const inputActive = ['pain_point', 'objective', 'test_analysis', 'results', 'qa'].includes(session.phase);

  return {
    messages,
    session,
    inputText,
    setInputText,
    isPolling,
    isSophieThinking,
    pollProgress,
    completedWidgets,
    inputActive,
    handleScenarioSelect,
    handleIndustrySelect,
    handleLaunch,
    handleScaleUp,
    handleRerun,
    handleSendMessage,
    handleFileUpload,
    handleQuickReply,
  };
}
