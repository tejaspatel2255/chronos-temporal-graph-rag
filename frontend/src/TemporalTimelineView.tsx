import { useState, useEffect } from 'react';
import { Calendar, Clock, RefreshCw, Layers, ArrowRight, Info, Filter } from 'lucide-react';

interface TemporalEvent {
  source: string;
  source_type: string;
  target: string;
  target_type: string;
  rel_type: string;
  date: string;
  quarter?: string;
  description: string;
}

interface TemporalTimelineViewProps {
  apiBaseUrl: string;
}

const TYPE_COLORS: Record<string, string> = {
  Company: '#6366f1',
  Person: '#10b981',
  Product: '#f59e0b',
  Event: '#ef4444',
  Metric: '#8b5cf6',
  Entity: '#64748b',
};

function getBadgeColor(type: string): string {
  for (const k of Object.keys(TYPE_COLORS)) {
    if (type?.toLowerCase().includes(k.toLowerCase())) return TYPE_COLORS[k];
  }
  return TYPE_COLORS.Entity;
}

export default function TemporalTimelineView({ apiBaseUrl }: TemporalTimelineViewProps) {
  const [events, setEvents] = useState<TemporalEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<TemporalEvent | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');

  const fetchTimeline = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBaseUrl}/api/timeline`);
      const data = await res.json();
      if (data.error) setError(data.error);
      setEvents(data.events || []);
      if (data.events && data.events.length > 0) {
        setSelectedEvent(data.events[0]);
      }
    } catch (e: any) {
      setError('Failed to fetch timeline events.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline();
  }, [apiBaseUrl]);

  const filteredEvents = events.filter(ev => {
    if (filterType === 'ALL') return true;
    return (
      ev.source_type.toLowerCase().includes(filterType.toLowerCase()) ||
      ev.target_type.toLowerCase().includes(filterType.toLowerCase())
    );
  });

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden">
      {/* Top Bar */}
      <div className="px-6 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-900/40 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Clock className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Temporal Event Timeline</h2>
            <p className="text-[11px] text-slate-500">
              {filteredEvents.length} chronological events extracted across document timeframes
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Type Filter */}
          <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={filterType}
              onChange={e => setFilterType(e.target.value)}
              className="bg-transparent text-xs text-slate-300 outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-slate-900">All Entity Types</option>
              <option value="Company" className="bg-slate-900">Companies</option>
              <option value="Person" className="bg-slate-900">People</option>
              <option value="Product" className="bg-slate-900">Products</option>
              <option value="Event" className="bg-slate-900">Events</option>
              <option value="Metric" className="bg-slate-900">Metrics</option>
            </select>
          </div>

          <button
            onClick={fetchTimeline}
            disabled={isLoading}
            className="px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 rounded-lg text-xs font-semibold transition-all flex items-center space-x-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Main View Grid */}
      <div className="flex flex-1 min-h-0">
        {/* Timeline Events List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {isLoading && (
            <div className="flex flex-col items-center justify-center h-64 space-y-3">
              <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-xs text-slate-400">Loading temporal timeline...</span>
            </div>
          )}

          {!isLoading && filteredEvents.length === 0 && (
            <div className="flex flex-col items-center justify-center h-64 space-y-3 text-center">
              <div className="w-12 h-12 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-2xl">⏳</div>
              <div>
                <h3 className="text-xs font-semibold text-slate-300">No dated temporal events found</h3>
                <p className="text-[11px] text-slate-500 mt-1 max-w-sm">
                  {error ? error : 'Upload documents with date or quarter references (e.g. Q2 2024, May 2023) to populate the timeline.'}
                </p>
              </div>
            </div>
          )}

          {!isLoading && filteredEvents.length > 0 && (
            <div className="relative border-l-2 border-slate-800 ml-4 pl-6 space-y-6">
              {filteredEvents.map((ev, idx) => {
                const isSelected = selectedEvent === ev;
                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedEvent(ev)}
                    className={`relative p-4 rounded-xl border transition-all cursor-pointer group ${
                      isSelected
                        ? 'bg-slate-900 border-indigo-500/60 shadow-lg shadow-indigo-500/10'
                        : 'bg-slate-900/40 border-slate-800 hover:border-slate-700 hover:bg-slate-900/70'
                    }`}
                  >
                    {/* Time Marker Pin */}
                    <div className={`absolute -left-[31px] top-5 w-4 h-4 rounded-full border-2 transition-all ${
                      isSelected
                        ? 'bg-indigo-500 border-slate-950 ring-4 ring-indigo-500/20'
                        : 'bg-slate-800 border-slate-700 group-hover:border-indigo-400'
                    }`} />

                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 flex items-center space-x-1">
                          <Calendar className="w-3 h-3" />
                          <span>{ev.date}</span>
                        </span>
                        {ev.quarter && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-400">
                            {ev.quarter}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                        {ev.rel_type}
                      </span>
                    </div>

                    <p className="text-xs text-slate-200 font-medium leading-relaxed mb-3">
                      {ev.description}
                    </p>

                    <div className="flex items-center space-x-2 text-[11px]">
                      <span className="px-2 py-0.5 rounded-full font-semibold text-white" style={{ backgroundColor: getBadgeColor(ev.source_type) }}>
                        {ev.source}
                      </span>
                      <ArrowRight className="w-3 h-3 text-slate-600 shrink-0" />
                      <span className="px-2 py-0.5 rounded-full font-semibold text-white" style={{ backgroundColor: getBadgeColor(ev.target_type) }}>
                        {ev.target}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Event Inspector Panel */}
        <div className="w-72 border-l border-slate-800 bg-slate-900/40 p-5 flex flex-col shrink-0">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center space-x-1.5">
            <Info className="w-3.5 h-3.5 text-indigo-400" />
            <span>Event Detail Inspector</span>
          </h3>

          {selectedEvent ? (
            <div className="space-y-4">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                <span className="text-[10px] font-bold uppercase text-indigo-400 tracking-wider">Timeline Anchor</span>
                <div className="text-sm font-bold text-slate-100 flex items-center space-x-2">
                  <Calendar className="w-4 h-4 text-indigo-400" />
                  <span>{selectedEvent.date}</span>
                </div>
              </div>

              <div className="space-y-2 text-xs">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Source Entity</span>
                  <div className="mt-1 font-semibold text-slate-200 flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: getBadgeColor(selectedEvent.source_type) }} />
                    <span>{selectedEvent.source} ({selectedEvent.source_type})</span>
                  </div>
                </div>

                <div className="pt-2">
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Relationship</span>
                  <div className="mt-1 text-indigo-300 font-mono font-semibold bg-indigo-950/40 border border-indigo-500/20 px-2.5 py-1 rounded">
                    {selectedEvent.rel_type}
                  </div>
                </div>

                <div className="pt-2">
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Target Entity</span>
                  <div className="mt-1 font-semibold text-slate-200 flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: getBadgeColor(selectedEvent.target_type) }} />
                    <span>{selectedEvent.target} ({selectedEvent.target_type})</span>
                  </div>
                </div>

                <div className="pt-2">
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Narrative Summary</span>
                  <p className="mt-1 text-slate-400 leading-relaxed text-[11px] bg-slate-950 p-2.5 rounded border border-slate-800">
                    {selectedEvent.description}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center text-slate-500 space-y-2">
              <Layers className="w-8 h-8 text-slate-700" />
              <p className="text-[11px]">Select an event on the timeline to inspect detailed relationship attributes.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
