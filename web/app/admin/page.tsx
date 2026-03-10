'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useLocale } from '@/lib/locale-context';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3456';

interface ResultFile {
  filename: string;
  type: 'survey' | 'simulation' | 'abtest' | 'conjoint' | 'other';
  size_bytes: number;
  modified: string;
}

export default function AdminPage() {
  const { locale } = useLocale();
  const zh = locale === 'zh';

  const [authed, setAuthed] = useState(false);
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [loginError, setLoginError] = useState('');

  const [results, setResults] = useState<ResultFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [detail, setDetail] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');
  const [fetchError, setFetchError] = useState<string>('');

  // Check session
  useEffect(() => {
    if (typeof window !== 'undefined' && sessionStorage.getItem('admin_auth') === '1') {
      setAuthed(true);
    }
  }, []);

  const handleLogin = async () => {
    try {
      const res = await fetch('/api/admin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password: pass }),
      });
      if (res.ok) {
        setAuthed(true);
        setLoginError('');
        sessionStorage.setItem('admin_auth', '1');
      } else {
        setLoginError(zh ? '用户名或密码错误' : 'Invalid username or password');
      }
    } catch {
      setLoginError(zh ? '服务器连接失败' : 'Server connection failed');
    }
  };

  const handleLogout = () => {
    setAuthed(false);
    sessionStorage.removeItem('admin_auth');
  };

  const fetchResults = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/results`);
      if (res.ok) {
        const data = await res.json();
        setResults(data);
      }
    } catch (err) {
      console.error('Failed to fetch results:', err);
      setFetchError(zh ? 'API 连接失败，请确认后端服务是否运行' : 'API connection failed. Make sure the backend is running.');
    }
    setLoading(false);
  }, [zh]);

  useEffect(() => {
    if (authed) fetchResults();
  }, [authed, fetchResults]);

  const viewDetail = async (filename: string) => {
    setSelectedFile(filename);
    setDetailLoading(true);
    setDetail(null);
    try {
      const res = await fetch(`${API_BASE}/api/results/${filename}`);
      if (res.ok) {
        setDetail(await res.json());
      } else {
        setDetail({ error: `HTTP ${res.status}: ${res.statusText}` });
      }
    } catch (err) {
      console.error('Failed to load detail:', err);
      setDetail({ error: zh ? '加载失败' : 'Failed to load' });
    }
    setDetailLoading(false);
  };

  const filtered = filterType === 'all' ? results : results.filter(r => r.type === filterType);
  const typeColors: Record<string, string> = {
    survey: 'bg-blue-500/20 text-blue-400',
    simulation: 'bg-purple-500/20 text-purple-400',
    abtest: 'bg-orange-500/20 text-orange-400',
    conjoint: 'bg-green-500/20 text-green-400',
    other: 'bg-[#1e293b] text-[#94a3b8]',
  };

  // Login screen
  if (!authed) {
    return (
      <div className="min-h-screen bg-[#050810] flex items-center justify-center">
        <div className="w-full max-w-sm bg-[#111827] border border-[#1e293b] rounded-2xl p-8 space-y-5">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-lg font-bold mx-auto mb-3">A</div>
            <h1 className="text-xl font-bold text-[#e2e8f0]">{zh ? '管理后台' : 'Admin Panel'}</h1>
            <p className="text-xs text-[#64748b] mt-1">Digital Twin Studio</p>
          </div>
          {loginError && (
            <div className="text-sm text-red-400 text-center bg-red-500/10 rounded-lg py-2">{loginError}</div>
          )}
          <div>
            <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-1 block">{zh ? '用户名' : 'Username'}</label>
            <input value={user} onChange={e => setUser(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleLogin()}
              className="w-full bg-[#0d1117] border border-[#1e293b] rounded-xl px-4 py-3 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60" />
          </div>
          <div>
            <label className="text-xs text-[#94a3b8] font-semibold uppercase tracking-wider mb-1 block">{zh ? '密码' : 'Password'}</label>
            <input type="password" value={pass} onChange={e => setPass(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleLogin()}
              className="w-full bg-[#0d1117] border border-[#1e293b] rounded-xl px-4 py-3 text-sm text-[#e2e8f0] outline-none focus:border-blue-500/60" />
          </div>
          <button onClick={handleLogin}
            className="w-full py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-bold rounded-xl hover:shadow-lg hover:shadow-blue-500/25 transition-all">
            {zh ? '登录' : 'Login'}
          </button>
        </div>
      </div>
    );
  }

  // Detail view
  if (selectedFile && detail) {
    const d = detail;
    const isSimulation = selectedFile.startsWith('simulation_') || selectedFile.startsWith('sim_');
    const isSurvey = selectedFile.startsWith('survey_');

    return (
      <div className="min-h-screen bg-[#050810] text-[#e2e8f0]">
        <div className="max-w-5xl mx-auto px-6 py-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <button onClick={() => { setSelectedFile(null); setDetail(null); }}
              className="text-sm text-blue-400 hover:text-blue-300">
              &larr; {zh ? '返回列表' : 'Back to list'}
            </button>
            <span className="text-xs text-[#475569]">{selectedFile}</span>
          </div>

          {/* Title */}
          <h1 className="text-2xl font-bold mb-2">
            {d.event_name || d.question || selectedFile}
          </h1>
          <div className="flex gap-3 text-sm text-[#94a3b8] mb-6">
            {d.timestamp && <span>{String(d.timestamp).slice(0, 19)}</span>}
            {d.sample_size != null && <span>{String(d.n_respondents || d.sample_size)} {zh ? '受访者' : 'respondents'}</span>}
          </div>

          {/* Survey result */}
          {isSurvey && d.overall && (
            <div className="space-y-6">
              <div className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-5">
                <h3 className="text-sm font-bold mb-3">{zh ? '总体分布' : 'Overall Distribution'}</h3>
                <div className="space-y-2">
                  {Object.entries(d.overall.choice_distribution as Record<string, number>)
                    .sort(([, a], [, b]) => b - a)
                    .map(([opt, cnt]) => {
                      const total = (d.n_respondents as number) || 1;
                      const pct = Math.round((cnt / total) * 100);
                      return (
                        <div key={opt}>
                          <div className="flex justify-between mb-0.5">
                            <span className="text-xs text-[#94a3b8]">{opt}</span>
                            <span className="text-xs font-mono text-[#94a3b8]">{pct}% ({cnt})</span>
                          </div>
                          <div className="h-2.5 bg-[#111827] rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500 rounded-full" style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>

              {/* Quality */}
              {d.quality?.available && (
                <div className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-5">
                  <h3 className="text-sm font-bold mb-2">{zh ? '质量评分' : 'Quality Scores'}</h3>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-lg font-bold text-green-400">{d.quality.high_quality_pct}%</div>
                      <div className="text-xs text-[#64748b]">{zh ? '高质量' : 'High Quality'}</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-yellow-400">{d.quality.acceptable_pct}%</div>
                      <div className="text-xs text-[#64748b]">{zh ? '可接受' : 'Acceptable'}</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-red-400">{d.quality.low_quality_pct}%</div>
                      <div className="text-xs text-[#64748b]">{zh ? '低质量' : 'Low Quality'}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Cost */}
              {d.cost && (
                <div className="text-xs text-[#475569]">
                  {zh ? '费用' : 'Cost'}: ${d.cost.total_cost_usd} ({d.cost.total_tokens} tokens)
                </div>
              )}
            </div>
          )}

          {/* Simulation result */}
          {isSimulation && d.summary && (
            <div className="space-y-6">
              {/* Summary cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: zh ? 'D1 支持率' : 'D1 Support', value: `${d.summary.day1_support_pct}%` },
                  { label: zh ? 'D7 支持率' : 'D7 Support', value: `${d.summary.day7_support_pct}%` },
                  { label: zh ? '意见变化' : 'Changed', value: `${d.summary.opinion_changed_pct}%` },
                  { label: zh ? '极化' : 'Polarization', value: `${d.summary.polarization_d7?.toFixed(2)}` },
                ].map(c => (
                  <div key={c.label} className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-4">
                    <div className="text-xs text-[#64748b]">{c.label}</div>
                    <div className="text-xl font-bold font-mono text-[#e2e8f0]">{c.value}</div>
                  </div>
                ))}
              </div>

              {/* Round distributions */}
              {d.rounds && (['day1', 'day4', 'day7'] as const).map(round => {
                const roundData = d.rounds[round];
                if (!roundData?.distribution) return null;
                const dist = roundData.distribution as Record<string, number>;
                const total = Object.values(dist).reduce((s: number, v: number) => s + v, 0);
                const labels: Record<string, string> = { day1: 'Day 1', day4: 'Day 4', day7: 'Day 7' };
                return (
                  <div key={round} className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-5">
                    <h3 className="text-sm font-bold mb-3">{labels[round]}</h3>
                    <div className="space-y-2">
                      {Object.entries(dist).sort(([, a], [, b]) => b - a).map(([opt, cnt]) => {
                        const pct = total > 0 ? Math.round((cnt / total) * 100) : 0;
                        return (
                          <div key={opt}>
                            <div className="flex justify-between mb-0.5">
                              <span className="text-xs text-[#94a3b8]">{opt}</span>
                              <span className="text-xs font-mono text-[#94a3b8]">{pct}% ({cnt})</span>
                            </div>
                            <div className="h-2.5 bg-[#111827] rounded-full overflow-hidden">
                              <div className="h-full bg-purple-500 rounded-full" style={{ width: `${pct}%` }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Raw JSON fallback for other types */}
          {!isSurvey && !isSimulation && (
            <pre className="bg-[#0d1117] border border-[#1e293b] rounded-xl p-5 text-xs text-[#94a3b8] overflow-auto max-h-[600px]">
              {JSON.stringify(detail, null, 2)}
            </pre>
          )}

          {/* Raw JSON toggle */}
          <details className="mt-6">
            <summary className="text-xs text-[#475569] cursor-pointer hover:text-[#94a3b8]">
              {zh ? '查看原始 JSON' : 'View Raw JSON'}
            </summary>
            <pre className="mt-2 bg-[#0d1117] border border-[#1e293b] rounded-xl p-5 text-xs text-[#94a3b8] overflow-auto max-h-[400px]">
              {JSON.stringify(detail, null, 2)}
            </pre>
          </details>
        </div>
      </div>
    );
  }

  // Results list
  return (
    <div className="min-h-screen bg-[#050810] text-[#e2e8f0]">
      <div className="max-w-4xl mx-auto px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold">{zh ? '管理后台' : 'Admin Panel'}</h1>
            <p className="text-sm text-[#64748b]">Digital Twin Studio — {zh ? '结果管理' : 'Results Management'}</p>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/" className="text-xs text-blue-400 hover:text-blue-300">{zh ? '回到首页' : 'Home'}</Link>
            <button onClick={fetchResults} className="text-xs text-blue-400 hover:text-blue-300">
              {zh ? '刷新' : 'Refresh'}
            </button>
            <button onClick={handleLogout} className="text-xs text-red-400 hover:text-red-300">
              {zh ? '退出' : 'Logout'}
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          {[
            { type: 'all', label: zh ? '全部' : 'All', count: results.length },
            { type: 'survey', label: zh ? '调研' : 'Survey', count: results.filter(r => r.type === 'survey').length },
            { type: 'simulation', label: zh ? '模拟' : 'Simulation', count: results.filter(r => r.type === 'simulation').length },
            { type: 'abtest', label: 'A/B Test', count: results.filter(r => r.type === 'abtest').length },
          ].map(s => (
            <button key={s.type} onClick={() => setFilterType(s.type)}
              className={`rounded-xl p-3 border text-center transition-all ${
                filterType === s.type
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-[#1e293b] bg-[#0d1117] hover:border-blue-500/40'
              }`}>
              <div className="text-xl font-bold">{s.count}</div>
              <div className="text-xs text-[#64748b]">{s.label}</div>
            </button>
          ))}
        </div>

        {/* Error state */}
        {fetchError && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-5 py-4 mb-6 text-sm text-red-400">
            {fetchError}
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="text-center py-12 text-[#64748b]">{zh ? '加载中...' : 'Loading...'}</div>
        )}

        {/* Detail loading */}
        {detailLoading && (
          <div className="text-center py-12 text-[#64748b]">{zh ? '加载详情...' : 'Loading detail...'}</div>
        )}

        {/* Results list */}
        {!loading && filtered.length === 0 && (
          <div className="text-center py-16">
            <div className="text-[#475569] text-sm">{zh ? '暂无结果数据' : 'No results yet'}</div>
            <p className="text-xs text-[#334155] mt-2">{zh ? '运行调研或模拟后，结果会自动保存在这里' : 'Results will appear here after running surveys or simulations'}</p>
          </div>
        )}

        <div className="space-y-2">
          {filtered.map(r => (
            <button key={r.filename} onClick={() => viewDetail(r.filename)}
              className="w-full flex items-center gap-4 bg-[#0d1117] border border-[#1e293b] rounded-xl px-5 py-4 hover:border-blue-500/40 transition-all text-left">
              <span className={`text-[10px] uppercase font-bold px-2 py-1 rounded-lg ${typeColors[r.type] || typeColors.other}`}>
                {r.type}
              </span>
              <div className="flex-1 min-w-0">
                <div className="text-sm text-[#e2e8f0] font-medium truncate">{r.filename}</div>
                <div className="text-xs text-[#475569]">{r.modified.slice(0, 19).replace('T', ' ')}</div>
              </div>
              <span className="text-xs text-[#475569]">{(r.size_bytes / 1024).toFixed(0)} KB</span>
              <span className="text-xs text-[#475569]">&rarr;</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
