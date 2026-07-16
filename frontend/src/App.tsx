import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  Search, 
  Database, 
  Globe, 
  FileText, 
  AlertTriangle, 
  CheckCircle, 
  ChevronDown, 
  ChevronUp, 
  Clock, 
  RefreshCw, 
  ArrowRight, 
  HelpCircle,
  BookOpen,
  History,
  Activity,
  Layers,
  Cpu
} from 'lucide-react';

interface Citation {
  source: string;
  chunk_id: string;
}

interface ContextUsed {
  id?: string;
  source: string;
  text: string;
}

interface AttemptLog {
  retry_index: number;
  query_used: string;
  confidence: number;
  reasoning: string;
}

interface QueryResponse {
  answer: string;
  confidence_score: number;
  is_valid: boolean;
  retries: number;
  citations: Citation[];
  context_used: ContextUsed[];
  attempts_log: AttemptLog[];
}


interface HealthStatus {
  status: string;
  neo4j_connected: boolean;
  chroma_document_count: number;
}

interface HistoryItem {
  timestamp: string;
  question: string;
  confidence_score: number;
  is_valid: boolean;
  retries: number;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const LOADING_STEPS = [
  "Classifying query intent and extracting temporal parameters...",
  "Querying vector database and structured tables concurrently...",
  "Applying temporal weighting to retrieve chronological context...",
  "Reranking candidate chunks using Cross-Encoder models...",
  "Drafting initial response synthesis with inline citations...",
  "Evaluating factuality and grounding against retrieved sources...",
  "Low confidence detected: Initiating self-correction rewrite...",
  "Retrying generation with refined search parameters...",
  "Local knowledge exhausted: Routing to DuckDuckGo search...",
  "Synthesizing final verified response from web fallback..."
];

export default function App() {
  // App States
  const [question, setQuestion] = useState('');
  const [forceFallback, setForceFallback] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  
  // Results State
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [activeQuestion, setActiveQuestion] = useState<string | null>(null);
  const [expandedContext, setExpandedContext] = useState(false);
  const [expandedAttempts, setExpandedAttempts] = useState(false);

  // Health and History
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthErr, setHealthErr] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  
  // Local session cache for full results (allows instant viewing of session queries)
  const [sessionCache, setSessionCache] = useState<Record<string, QueryResponse>>({});

  const loadingIntervalRef = useRef<number | null>(null);

  // Poll API Health
  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/health`);
      if (!res.ok) throw new Error('API unstable');
      const data = await res.json();
      setHealth(data);
      setHealthErr(false);
    } catch (e) {
      setHealth(null);
      setHealthErr(true);
    }
  };

  // Fetch Query History
  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/history?limit=15`);
      if (res.ok) {
        const data = await res.json();
        // Sort newest first
        setHistory(data.reverse());
      }
    } catch (e) {
      console.error('Failed to load history', e);
    }
  };

  useEffect(() => {
    checkHealth();
    fetchHistory();

    // Poll health every 30 seconds
    const healthTimer = setInterval(checkHealth, 30000);
    return () => clearInterval(healthTimer);
  }, []);

  // Loading indicator step rotation animation
  useEffect(() => {
    if (isLoading) {
      setLoadingStep(0);
      loadingIntervalRef.current = window.setInterval(() => {
        setLoadingStep((prev) => (prev + 1) % LOADING_STEPS.length);
      }, 4000);
    } else {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
      }
    }
    return () => {
      if (loadingIntervalRef.current) clearInterval(loadingIntervalRef.current);
    };
  }, [isLoading]);

  // Handle query submission
  const handleSubmit = async (qText: string, forceWeb: boolean = false) => {
    if (!qText.trim()) return;
    setIsLoading(true);
    setError(null);
    setResult(null);
    setExpandedContext(false);
    setExpandedAttempts(false);
    setActiveQuestion(qText);

    try {
      const response = await fetch(`${API_BASE_URL}/api/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: qText,
          force_fallback: forceWeb
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const data: QueryResponse = await response.json();
      setResult(data);
      
      // Store in session cache
      setSessionCache(prev => ({
        ...prev,
        [qText.toLowerCase().trim()]: data
      }));

      // Refresh query log history
      fetchHistory();
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred. Please check the backend connection.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleHistoryItemClick = (item: HistoryItem) => {
    const cached = sessionCache[item.question.toLowerCase().trim()];
    if (cached) {
      setResult(cached);
      setActiveQuestion(item.question);
      setError(null);
    } else {
      // populate input and rerun
      setQuestion(item.question);
      handleSubmit(item.question);
    }
  };

  // Status indicator colors
  const getStatusDetails = () => {
    if (healthErr) {
      return { color: 'bg-red-500', text: 'Backend Offline', ping: 'animate-ping bg-red-400' };
    }
    if (health && !health.neo4j_connected) {
      return { color: 'bg-yellow-500', text: 'Graph Database Offline', ping: 'animate-ping bg-yellow-400' };
    }
    if (health && health.neo4j_connected) {
      return { color: 'bg-emerald-500', text: 'All Systems Operational', ping: 'bg-emerald-400' };
    }
    return { color: 'bg-slate-500', text: 'Connecting...', ping: 'bg-slate-400' };
  };

  const status = getStatusDetails();

  // Color helpers
  const getConfidenceColor = (score: number) => {
    if (score >= 70) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    if (score >= 40) return 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    return 'text-rose-400 bg-rose-500/10 border-rose-500/30';
  };

  const isWebResult = result?.context_used.some(c => c.source === 'duckduckgo_web_search');

  return (
    <div className="flex h-screen bg-slate-950 font-sans overflow-hidden">
      
      {/* Sidebar - History & Logs */}
      <aside className="w-80 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0">
        <div className="flex flex-col grow overflow-hidden">
          
          {/* Brand Logo */}
          <div className="p-5 border-b border-slate-800 flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <span className="text-xl font-bold text-white">⏳</span>
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white">Project Chronos</h1>
              <p className="text-xs text-slate-400">Self-Correcting Temporal RAG</p>
            </div>
          </div>

          {/* Health Stats */}
          <div className="p-4 mx-4 mt-4 bg-slate-950/60 rounded-lg border border-slate-800/80">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-400 flex items-center">
                <Activity className="w-3.5 h-3.5 mr-1.5 text-indigo-400" /> System Health
              </span>
              <button 
                onClick={checkHealth}
                className="text-xs text-slate-500 hover:text-slate-300 transition-colors p-1"
                title="Refresh Status"
              >
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>
            
            <div className="flex items-center space-x-2.5 mb-3">
              <div className="relative flex h-2 w-2">
                <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${status.ping}`}></span>
                <span className={`relative inline-flex rounded-full h-2 w-2 ${status.color}`}></span>
              </div>
              <span className="text-xs font-medium text-slate-200">{status.text}</span>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/50 text-[11px] text-slate-400">
              <div>
                <span className="block text-slate-500">Vector Index Count:</span>
                <span className="font-semibold text-slate-300">{health ? health.chroma_document_count : '--'} docs</span>
              </div>
              <div>
                <span className="block text-slate-500">Neo4j Driver:</span>
                <span className={`font-semibold ${health?.neo4j_connected ? 'text-emerald-400' : 'text-slate-500'}`}>
                  {health?.neo4j_connected ? 'Connected' : 'Offline'}
                </span>
              </div>
            </div>
          </div>

          {/* History Section */}
          <div className="mt-6 flex-1 flex flex-col min-h-0">
            <div className="px-5 mb-2 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-slate-400 tracking-wider uppercase flex items-center">
                <History className="w-3.5 h-3.5 mr-1.5" /> Recent Queries
              </h2>
              <button 
                onClick={fetchHistory}
                className="text-[10px] text-indigo-400 hover:text-indigo-300 transition-colors"
              >
                Refresh
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
              {history.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">
                  No query logs found. Try asking a question!
                </div>
              ) : (
                history.map((item, idx) => {
                  const hasCache = !!sessionCache[item.question.toLowerCase().trim()];
                  return (
                    <button
                      key={idx}
                      onClick={() => handleHistoryItemClick(item)}
                      className="w-full text-left p-3 rounded-lg bg-slate-950/30 hover:bg-slate-800 border border-slate-800/60 transition-all group flex flex-col space-y-1.5"
                    >
                      <span className="text-xs font-medium text-slate-200 group-hover:text-indigo-400 transition-colors line-clamp-2">
                        {item.question}
                      </span>
                      <div className="flex items-center justify-between w-full text-[10px] text-slate-500">
                        <span className="flex items-center">
                          <Clock className="w-2.5 h-2.5 mr-1" />
                          {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                        <div className="flex items-center space-x-1.5">
                          {hasCache && (
                            <span className="px-1 text-[9px] bg-indigo-500/10 text-indigo-400 rounded-sm border border-indigo-500/20">
                              Cached
                            </span>
                          )}
                          <span className={`font-semibold ${item.confidence_score >= 70 ? 'text-emerald-400' : item.confidence_score >= 40 ? 'text-amber-400' : 'text-rose-400'}`}>
                            Conf: {item.confidence_score}%
                          </span>
                        </div>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="p-4 border-t border-slate-800 text-[10px] text-slate-500 bg-slate-900/60">
          <p>Chronos Enterprise Analyser v1.2</p>
          <p className="mt-0.5">LangGraph Grounded Verification Loop</p>
        </div>
      </aside>

      {/* Main Panel */}
      <main className="flex-1 flex flex-col bg-slate-950 overflow-hidden">
        
        {/* Header alert for Backend offline */}
        {healthErr && (
          <div className="bg-rose-500/10 border-b border-rose-500/20 px-6 py-3 flex items-center justify-between text-xs text-rose-400">
            <span className="flex items-center">
              <AlertTriangle className="w-4 h-4 mr-2 shrink-0 text-rose-500 animate-pulse" />
              <strong>Connection Error:</strong> Cannot connect to the FastAPI backend. Check if the terminal is running <code>python run_api.py</code> on port 8000.
            </span>
            <button 
              onClick={checkHealth}
              className="px-2.5 py-1 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 font-semibold rounded transition-colors flex items-center"
            >
              <RefreshCw className="w-3 h-3 mr-1" /> Reconnect
            </button>
          </div>
        )}

        {/* Header alert for Graph DB offline */}
        {health && !health.neo4j_connected && (
          <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2.5 flex items-center text-xs text-amber-400">
            <AlertTriangle className="w-4 h-4 mr-2 shrink-0 text-amber-500" />
            <span>
              <strong>Graph Index Offline:</strong> Local Neo4j instance at <code>localhost:7687</code> is unreachable. The RAG pipeline will fallback to hybrid vector + lexical search.
            </span>
          </div>
        )}

        {/* Search Panel */}
        <div className="p-6 border-b border-slate-900 bg-slate-900/20 flex flex-col space-y-4 shrink-0">
          <form 
            onSubmit={(e) => {
              e.preventDefault();
              handleSubmit(question, forceFallback);
            }}
            className="w-full flex space-x-3 items-stretch"
          >
            <div className="relative flex-1">
              <input
                type="text"
                placeholder="Ask Chronos about corporate memos, financial records, or timelines (e.g. Q2 2024 objectives)..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={isLoading}
                className="w-full h-12 pl-11 pr-4 bg-slate-900 hover:bg-slate-900/80 focus:bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-lg text-sm text-slate-100 placeholder-slate-500 outline-none transition-all shadow-inner focus:shadow-[0_0_15px_rgba(99,102,241,0.1)]"
              />
              <Search className="absolute left-4 top-3.5 w-5 h-5 text-slate-500" />
            </div>
            
            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="px-6 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white text-sm font-semibold rounded-lg transition-all flex items-center shadow-lg shadow-indigo-600/10 hover:shadow-indigo-600/20 shrink-0"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  Analyze
                  <ArrowRight className="w-4 h-4 ml-2" />
                </>
              )}
            </button>
          </form>

          {/* Toggle flags */}
          <div className="flex items-center space-x-6 text-xs text-slate-400">
            <label className="flex items-center space-x-2 cursor-pointer select-none hover:text-slate-200 transition-colors">
              <input
                type="checkbox"
                checked={forceFallback}
                onChange={(e) => setForceFallback(e.target.checked)}
                disabled={isLoading}
                className="rounded border-slate-800 bg-slate-900 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-slate-950 w-4 h-4"
              />
              <span>Force Live Web Search Fallback</span>
            </label>

            <span className="text-slate-600">|</span>
            
            <div className="flex items-center space-x-1">
              <HelpCircle className="w-3.5 h-3.5 text-slate-500" />
              <span>Pipeline uses local Vector Store (ChromaDB) + Relationship Store (Neo4j).</span>
            </div>
          </div>
        </div>

        {/* Content Panel */}
        <div className="flex-1 overflow-y-auto p-8">
          
          {/* Initial State / Help Instructions */}
          {!isLoading && !result && !error && (
            <div className="max-w-2xl mx-auto py-16 flex flex-col items-center text-center space-y-6">
              <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-3xl">
                🔮
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-200">How to Query Chronos</h3>
                <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">
                  Type an analytical query to evaluate corporate temporal knowledge. If the system fails to verify claims locally, it corrects itself or falls back to live web search.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 w-full mt-4">
                <button
                  onClick={() => {
                    const q = "What is the capital allocation for Project Chronos in the year 2026?";
                    setQuestion(q);
                    handleSubmit(q, false);
                  }}
                  className="p-4 rounded-xl bg-slate-900/40 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 text-left text-xs transition-all flex flex-col space-y-2 group"
                >
                  <span className="font-semibold text-indigo-400 flex items-center">
                    <Globe className="w-3.5 h-3.5 mr-1" /> Web Fallback Query
                  </span>
                  <span className="text-slate-400 group-hover:text-slate-300">
                    "What is the capital allocation for Project Chronos in the year 2026?"
                  </span>
                </button>

                <button
                  onClick={() => {
                    const q = "What are the key findings in Q2 2024 strategic reports?";
                    setQuestion(q);
                    handleSubmit(q, false);
                  }}
                  className="p-4 rounded-xl bg-slate-900/40 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 text-left text-xs transition-all flex flex-col space-y-2 group"
                >
                  <span className="font-semibold text-indigo-400 flex items-center">
                    <BookOpen className="w-3.5 h-3.5 mr-1" /> Internal Memo Query
                  </span>
                  <span className="text-slate-400 group-hover:text-slate-300">
                    "What are the key findings in Q2 2024 strategic reports?"
                  </span>
                </button>
              </div>
            </div>
          )}

          {/* Loading Animation Card */}
          {isLoading && (
            <div className="max-w-3xl mx-auto py-16 flex flex-col items-center justify-center space-y-8 bg-slate-900/20 border border-slate-900/60 rounded-2xl p-8 shadow-2xl backdrop-blur-sm">
              <div className="relative w-20 h-20">
                {/* Outermost spinning ring */}
                <div className="absolute inset-0 rounded-full border-4 border-slate-800 border-t-indigo-500 animate-spin"></div>
                {/* Innermost ring */}
                <div className="absolute inset-3 rounded-full border-4 border-slate-800 border-b-sky-400 animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
                {/* Center dot */}
                <div className="absolute inset-7 rounded-full bg-slate-950 flex items-center justify-center text-xl">
                  ⏳
                </div>
              </div>
              
              <div className="text-center space-y-2">
                <h4 className="text-sm font-semibold text-indigo-400 uppercase tracking-widest animate-pulse">Running Self-Correcting Loop</h4>
                <p className="text-base text-slate-200 transition-all font-medium duration-500 max-w-lg">
                  "{LOADING_STEPS[loadingStep]}"
                </p>
                <p className="text-xs text-slate-500">This can take up to 40 seconds if query classification requires validation retries or web search fallback.</p>
              </div>
            </div>
          )}

          {/* Error Message Card */}
          {error && (
            <div className="max-w-3xl mx-auto bg-rose-500/10 border border-rose-500/25 rounded-2xl p-6 flex items-start space-x-4">
              <AlertTriangle className="w-6 h-6 text-rose-500 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-rose-400">Query Analysis Failed</h4>
                <p className="text-xs text-slate-300 leading-relaxed">{error}</p>
                <div className="pt-3 flex space-x-3">
                  <button 
                    onClick={() => activeQuestion && handleSubmit(activeQuestion, forceFallback)}
                    className="px-3 py-1.5 bg-rose-500/25 hover:bg-rose-500/40 text-rose-200 text-xs font-semibold rounded transition-colors"
                  >
                    Try Again
                  </button>
                  <button 
                    onClick={() => setError(null)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded transition-colors"
                  >
                    Clear Error
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Results Render Panel */}
          {!isLoading && result && (
            <div className="max-w-4xl mx-auto space-y-6">
              
              {/* Query & Badges Header */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                <div className="flex flex-col space-y-2">
                  <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">Question Analyzed</span>
                  <h2 className="text-lg font-bold text-white leading-snug">
                    {activeQuestion || "Enterprise RAG Query"}
                  </h2>
                </div>

                <div className="flex flex-wrap gap-2.5 pt-2 border-t border-slate-800/60">
                  {/* Confidence Badge */}
                  <div className={`px-3 py-1 rounded-full border text-xs font-semibold flex items-center ${getConfidenceColor(result.confidence_score)}`}>
                    <Cpu className="w-3.5 h-3.5 mr-1.5" />
                    Confidence: {result.confidence_score}%
                  </div>

                  {/* Validity Badge */}
                  <div className={`px-3 py-1 rounded-full border text-xs font-semibold flex items-center ${result.is_valid ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' : 'text-amber-400 bg-amber-500/10 border-amber-500/30'}`}>
                    {result.is_valid ? (
                      <>
                        <CheckCircle className="w-3.5 h-3.5 mr-1.5" />
                        Grounded & Validated
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-3.5 h-3.5 mr-1.5 text-amber-500" />
                        Low-Grounding Warning
                      </>
                    )}
                  </div>

                  {/* Web Fallback Run Badge */}
                  {isWebResult && (
                    <div className="px-3 py-1 rounded-full border border-sky-500/30 bg-sky-500/10 text-sky-400 text-xs font-semibold flex items-center">
                      <Globe className="w-3.5 h-3.5 mr-1.5 text-sky-400 animate-pulse" />
                      Includes Live Web Search Results
                    </div>
                  )}

                  {/* Retries count */}
                  <span className="text-xs text-slate-500 py-1 px-2 self-center bg-slate-950/40 rounded border border-slate-800">
                    {result.retries === 0 
                      ? "Answered immediately" 
                      : `Answered after ${result.retries} self-correction rewrite cycle${result.retries > 1 ? 's' : ''}`
                    }
                  </span>
                </div>

                {/* Grounding/Validation failure callout */}
                {!result.is_valid && (
                  <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/25 rounded-lg flex items-start text-xs text-amber-400 leading-normal">
                    <AlertTriangle className="w-4 h-4 mr-2 shrink-0 text-amber-500 mt-0.5" />
                    <span>
                      <strong>Disclaimer:</strong> This response failed target grounding validation metrics (either low source correspondence or low confidence). Please evaluate citations and context carefully below.
                    </span>
                  </div>
                )}
              </div>

              {/* Synthesized Answer Box */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl">
                <div className="flex items-center space-x-2.5 mb-4 border-b border-slate-800 pb-3">
                  <BookOpen className="w-5 h-5 text-indigo-400" />
                  <h3 className="text-sm font-bold tracking-wider text-slate-300 uppercase">Chronos Synthesized Report</h3>
                </div>
                
                <div className="prose max-w-none">
                  <ReactMarkdown>{result.answer}</ReactMarkdown>
                </div>
              </div>

              {/* Citations list */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
                <div className="flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">Sources & Citations Used</h4>
                </div>
                
                {result.citations.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No formal source citations referenced in generated output.</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                    {result.citations.map((citation, idx) => {
                      const isWeb = citation.source === 'duckduckgo_web_search';
                      return (
                        <div 
                          key={idx}
                          className={`p-3 rounded-lg border flex items-center space-x-3 text-xs ${isWeb ? 'bg-sky-500/5 border-sky-500/20 text-sky-300' : 'bg-slate-950/60 border-slate-800 text-slate-200'}`}
                        >
                          {isWeb ? (
                            <Globe className="w-4 h-4 text-sky-400 shrink-0" />
                          ) : (
                            <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                          )}
                          <div className="overflow-hidden">
                            <span className="block font-medium truncate">{citation.source}</span>
                            <span className="block text-[10px] text-slate-500 truncate">Chunk ID: {citation.chunk_id}</span>
                          </div>
                          <span className={`ml-auto px-1.5 py-0.5 rounded text-[10px] font-semibold tracking-wide ${isWeb ? 'bg-sky-500/10 text-sky-400' : 'bg-indigo-500/10 text-indigo-400'}`}>
                            {isWeb ? 'External' : 'Internal'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Accordion: Context Used */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
                <button
                  onClick={() => setExpandedContext(!expandedContext)}
                  className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-800/40 transition-colors"
                >
                  <div className="flex items-center space-x-2.5">
                    <Database className="w-4.5 h-4.5 text-indigo-400" />
                    <span className="text-sm font-semibold text-slate-200">Retrieved Context Payload ({result.context_used.length} blocks)</span>
                  </div>
                  {expandedContext ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                </button>

                {expandedContext && (
                  <div className="border-t border-slate-800 p-6 space-y-4 bg-slate-900/40 max-h-96 overflow-y-auto">
                    {result.context_used.map((ctx, idx) => {
                      const isWeb = ctx.source === 'duckduckgo_web_search';
                      return (
                        <div key={idx} className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2.5">
                          <div className="flex items-center justify-between text-xs border-b border-slate-900 pb-2">
                            <span className="flex items-center font-semibold text-indigo-400">
                              {isWeb ? <Globe className="w-3.5 h-3.5 mr-1.5 text-sky-400" /> : <FileText className="w-3.5 h-3.5 mr-1.5" />}
                              Source: {ctx.source}
                            </span>
                            <span className="text-[10px] text-slate-500">Chunk ID: {ctx.id || 'N/A'}</span>
                          </div>
                          <p className="text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap">{ctx.text}</p>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Accordion: Attempts Log */}
              {result.attempts_log.length > 0 && (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
                  <button
                    onClick={() => setExpandedAttempts(!expandedAttempts)}
                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-800/40 transition-colors"
                  >
                    <div className="flex items-center space-x-2.5">
                      <RefreshCw className="w-4.5 h-4.5 text-indigo-400" />
                      <span className="text-sm font-semibold text-slate-200">Correction & Rewrite Attempts Log</span>
                    </div>
                    {expandedAttempts ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                  </button>

                  {expandedAttempts && (
                    <div className="border-t border-slate-800 p-6 space-y-3 bg-slate-900/40">
                      {result.attempts_log.map((log, idx) => (
                        <div key={idx} className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800 flex flex-col space-y-2 text-xs">
                          <div className="flex items-center justify-between font-semibold border-b border-slate-900 pb-1.5">
                            <span className="text-indigo-400">Attempt #{log.retry_index + 1}</span>
                            <span className={`px-1.5 py-0.5 rounded text-[10px] ${log.confidence >= 70 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                              Confidence: {log.confidence}%
                            </span>
                          </div>
                          <div>
                            <span className="block text-[10px] text-slate-500 uppercase tracking-wider font-bold">Query Rewritten:</span>
                            <code className="text-slate-300 font-mono text-[11px] bg-slate-900 px-1 py-0.5 rounded block mt-0.5">{log.query_used}</code>
                          </div>
                          <div>
                            <span className="block text-[10px] text-slate-500 uppercase tracking-wider font-bold">Failure Reasoning:</span>
                            <p className="text-slate-400 mt-0.5 italic">"{log.reasoning}"</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
