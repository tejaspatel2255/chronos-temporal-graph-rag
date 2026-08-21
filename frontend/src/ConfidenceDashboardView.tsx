import { useState, useEffect } from 'react';
import { Activity, TrendingUp, RefreshCw, BarChart2, ShieldCheck, Zap } from 'lucide-react';

interface QueryLogEntry {
  timestamp: string;
  question: string;
  confidence_score: number;
  is_valid: boolean;
  retries: number;
}

interface AnalyticsData {
  total_queries: number;
  average_confidence: number;
  validation_rate: number;
  average_retries: number;
  history: QueryLogEntry[];
}

interface ConfidenceDashboardProps {
  apiBaseUrl: string;
}

export default function ConfidenceDashboardView({ apiBaseUrl }: ConfidenceDashboardProps) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBaseUrl}/api/analytics/confidence`);
      const result = await res.json();
      if (result.error) setError(result.error);
      else setData(result);
    } catch (e: any) {
      setError('Failed to load confidence analytics dashboard.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [apiBaseUrl]);

  const getBarColor = (score: number) => {
    if (score >= 70) return 'bg-emerald-500 hover:bg-emerald-400';
    if (score >= 40) return 'bg-amber-500 hover:bg-amber-400';
    return 'bg-rose-500 hover:bg-rose-400';
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100 overflow-y-auto p-8 space-y-8">
      {/* Header Bar */}
      <div className="flex items-center justify-between pb-6 border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Confidence Score & Reliability Dashboard</h2>
            <p className="text-xs text-slate-400">Real-time telemetry on query grounding metrics, validation success, and self-correction cycles</p>
          </div>
        </div>

        <button
          onClick={fetchAnalytics}
          disabled={isLoading}
          className="px-3.5 py-2 bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 rounded-lg text-xs font-semibold transition-all flex items-center space-x-2"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Dashboard</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400 text-xs">
          {error}
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-4 gap-4">
        {/* Total Queries */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold uppercase tracking-wider">
            <span>Total Evaluated Queries</span>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {data ? data.total_queries : '--'}
          </div>
          <p className="text-[11px] text-slate-500">Processed by LangGraph pipeline</p>
        </div>

        {/* Avg Confidence */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold uppercase tracking-wider">
            <span>Average System Confidence</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-amber-400">
            {data ? `${data.average_confidence}%` : '--'}
          </div>
          <p className="text-[11px] text-slate-500">Target benchmark threshold: 70%</p>
        </div>

        {/* Validation Pass Rate */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold uppercase tracking-wider">
            <span>Grounded Pass Rate</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400">
            {data ? `${data.validation_rate}%` : '--'}
          </div>
          <p className="text-[11px] text-slate-500">Queries meeting strict citation grounding</p>
        </div>

        {/* Avg Retries */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-slate-400 text-xs font-bold uppercase tracking-wider">
            <span>Avg Correction Cycles</span>
            <RefreshCw className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-3xl font-extrabold text-sky-400">
            {data ? `${data.average_retries} / query` : '--'}
          </div>
          <p className="text-[11px] text-slate-500">LangGraph self-correction iterations</p>
        </div>
      </div>

      {/* Visual Bar Chart: Recent Queries Confidence Scores */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <BarChart2 className="w-4 h-4 text-indigo-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Confidence Score Trend (Last 30 Queries)</h3>
          </div>
          <div className="flex items-center space-x-4 text-[10px]">
            <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded bg-emerald-500 inline-block" /><span>High (≥70%)</span></span>
            <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded bg-amber-500 inline-block" /><span>Moderate (40-69%)</span></span>
            <span className="flex items-center space-x-1.5"><span className="w-2.5 h-2.5 rounded bg-rose-500 inline-block" /><span>Low (&lt;40%)</span></span>
          </div>
        </div>

        {data && data.history.length > 0 ? (
          <div className="h-48 flex items-end justify-between space-x-1.5 pt-6 px-2 border-b border-slate-800">
            {data.history.map((e, idx) => (
              <div key={idx} className="flex-1 flex flex-col items-center h-full justify-end group relative">
                {/* Hover Tooltip */}
                <div className="absolute -top-12 z-20 hidden group-hover:flex flex-col items-center bg-slate-950 border border-slate-700 text-slate-200 text-[10px] p-2 rounded shadow-xl whitespace-nowrap">
                  <span className="font-bold">{e.question.slice(0, 30)}...</span>
                  <span className="text-slate-400">Score: {e.confidence_score}% | Valid: {e.is_valid ? 'Yes' : 'No'}</span>
                </div>

                {/* Bar */}
                <div
                  className={`w-full rounded-t transition-all ${getBarColor(e.confidence_score)}`}
                  style={{ height: `${Math.max(e.confidence_score, 6)}%` }}
                />
              </div>
            ))}
          </div>
        ) : (
          <div className="h-48 flex items-center justify-center text-xs text-slate-500">
            No query execution data logged yet. Run queries in the RAG view to populate confidence trends.
          </div>
        )}
      </div>

      {/* Query Telemetry Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 border-b border-slate-800 pb-3">
          Recent Query Grounding Audit Trail
        </h3>

        {data && data.history.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-500 text-[10px] uppercase font-bold tracking-wider">
                <tr>
                  <th className="py-2.5 px-3 rounded-l-lg">Timestamp</th>
                  <th className="py-2.5 px-3">Evaluated Question</th>
                  <th className="py-2.5 px-3 text-center">Confidence</th>
                  <th className="py-2.5 px-3 text-center">Grounding</th>
                  <th className="py-2.5 px-3 text-center rounded-r-lg">Retries</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {[...data.history].reverse().map((e, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-500">{new Date(e.timestamp).toLocaleTimeString()}</td>
                    <td className="py-2.5 px-3 font-medium text-slate-200">{e.question}</td>
                    <td className="py-2.5 px-3 text-center">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        e.confidence_score >= 70 ? 'text-emerald-400 bg-emerald-500/10' :
                        e.confidence_score >= 40 ? 'text-amber-400 bg-amber-500/10' : 'text-rose-400 bg-rose-500/10'
                      }`}>
                        {e.confidence_score}%
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${e.is_valid ? 'text-emerald-400 bg-emerald-500/10' : 'text-amber-400 bg-amber-500/10'}`}>
                        {e.is_valid ? 'Validated' : 'Unvalidated'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono text-[11px] text-slate-400">{e.retries}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-6 text-xs text-slate-500">No log items recorded.</div>
        )}
      </div>
    </div>
  );
}
