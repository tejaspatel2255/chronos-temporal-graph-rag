import { useEffect, useRef, useState, useCallback } from 'react';
import { RefreshCw, ZoomIn, ZoomOut, Maximize2, Info } from 'lucide-react';

interface GraphNode {
  id: string;
  name: string;
  type: string;
  labels: string[];
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  rel_type: string;
  date?: string;
  quarter?: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  error?: string;
}

interface KnowledgeGraphViewProps {
  apiBaseUrl: string;
}

// Entity type → color mapping
const TYPE_COLORS: Record<string, string> = {
  Company:    '#6366f1',
  Companies:  '#6366f1',
  Person:     '#10b981',
  People:     '#10b981',
  Product:    '#f59e0b',
  Products:   '#f59e0b',
  Event:      '#ef4444',
  Events:     '#ef4444',
  Metric:     '#8b5cf6',
  Metrics:    '#8b5cf6',
  Unknown:    '#64748b',
};

const TYPE_LABELS: Record<string, string> = {
  Company:    'Company',
  Companies:  'Company',
  Person:     'Person',
  People:     'Person',
  Product:    'Product',
  Products:   'Product',
  Event:      'Event',
  Events:     'Event',
  Metric:     'Metric',
  Metrics:    'Metric',
  Unknown:    'Entity',
};

function getNodeColor(type: string): string {
  for (const key of Object.keys(TYPE_COLORS)) {
    if (type?.toLowerCase().includes(key.toLowerCase())) return TYPE_COLORS[key];
  }
  return TYPE_COLORS.Unknown;
}

export default function KnowledgeGraphView({ apiBaseUrl }: KnowledgeGraphViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const animFrameRef = useRef<number>(0);
  const simulationRef = useRef<ReturnType<typeof createSimulation> | null>(null);

  const fetchGraph = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBaseUrl}/api/graph?limit=150`);
      const data: GraphData = await res.json();
      if (data.error && data.nodes.length === 0) {
        setError(data.error);
      }
      setGraphData(data);
    } catch (e: any) {
      setError('Failed to load graph data. Is Neo4j running?');
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  // Simple force simulation in pure JS
  function createSimulation(nodes: GraphNode[], links: GraphLink[]) {
    const strength = -300;
    const linkDistance = 100;

    // Initialize positions
    nodes.forEach((n, i) => {
      if (!n.x) n.x = Math.cos((i / nodes.length) * 2 * Math.PI) * 250;
      if (!n.y) n.y = Math.sin((i / nodes.length) * 2 * Math.PI) * 250;
      n.vx = 0;
      n.vy = 0;
    });

    let running = true;
    function tick() {
      if (!running) return;

      // Repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = (nodes[j].x ?? 0) - (nodes[i].x ?? 0);
          const dy = (nodes[j].y ?? 0) - (nodes[i].y ?? 0);
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = strength / (dist * dist);
          nodes[i].vx = (nodes[i].vx ?? 0) + (dx / dist) * force;
          nodes[i].vy = (nodes[i].vy ?? 0) + (dy / dist) * force;
          nodes[j].vx = (nodes[j].vx ?? 0) - (dx / dist) * force;
          nodes[j].vy = (nodes[j].vy ?? 0) - (dy / dist) * force;
        }
      }

      // Link attraction
      links.forEach(link => {
        const s = nodes.find(n => n.id === (typeof link.source === 'object' ? link.source.id : link.source));
        const t = nodes.find(n => n.id === (typeof link.target === 'object' ? link.target.id : link.target));
        if (!s || !t) return;
        const dx = (t.x ?? 0) - (s.x ?? 0);
        const dy = (t.y ?? 0) - (s.y ?? 0);
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - linkDistance) * 0.05;
        s.vx = (s.vx ?? 0) + (dx / dist) * force;
        s.vy = (s.vy ?? 0) + (dy / dist) * force;
        t.vx = (t.vx ?? 0) - (dx / dist) * force;
        t.vy = (t.vy ?? 0) - (dy / dist) * force;
      });

      // Center gravity
      nodes.forEach(n => {
        n.vx = ((n.vx ?? 0) - (n.x ?? 0) * 0.005) * 0.9;
        n.vy = ((n.vy ?? 0) - (n.y ?? 0) * 0.005) * 0.9;
        if (n.fx == null) n.x = (n.x ?? 0) + (n.vx ?? 0);
        if (n.fy == null) n.y = (n.y ?? 0) + (n.vy ?? 0);
      });
    }

    return { tick, stop: () => { running = false; } };
  }

  useEffect(() => {
    if (graphData.nodes.length === 0) return;
    if (simulationRef.current) simulationRef.current.stop();

    const nodes = graphData.nodes.map(n => ({ ...n }));
    const links = graphData.links;
    simulationRef.current = createSimulation(nodes, links);

    let ticks = 0;
    const MAX_TICKS = 200;

    function animate() {
      if (ticks < MAX_TICKS && simulationRef.current) {
        simulationRef.current.tick();
        ticks++;
      }
      drawGraph(nodes, links);
      animFrameRef.current = requestAnimationFrame(animate);
    }

    animFrameRef.current = requestAnimationFrame(animate);
    return () => {
      cancelAnimationFrame(animFrameRef.current);
      if (simulationRef.current) simulationRef.current.stop();
    };
  }, [graphData, zoom, pan, selectedNode, hoveredNode]);

  function drawGraph(nodes: GraphNode[], links: GraphLink[]) {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    ctx.save();
    ctx.translate(w / 2 + pan.x, h / 2 + pan.y);
    ctx.scale(zoom, zoom);

    // Draw links
    links.forEach(link => {
      const s = nodes.find(n => n.id === (typeof link.source === 'object' ? link.source.id : link.source));
      const t = nodes.find(n => n.id === (typeof link.target === 'object' ? link.target.id : link.target));
      if (!s || !t) return;

      ctx.beginPath();
      ctx.moveTo(s.x ?? 0, s.y ?? 0);
      ctx.lineTo(t.x ?? 0, t.y ?? 0);
      ctx.strokeStyle = 'rgba(99,102,241,0.25)';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Draw arrow
      const angle = Math.atan2((t.y ?? 0) - (s.y ?? 0), (t.x ?? 0) - (s.x ?? 0));
      const arrowX = (t.x ?? 0) - Math.cos(angle) * 18;
      const arrowY = (t.y ?? 0) - Math.sin(angle) * 18;
      ctx.beginPath();
      ctx.moveTo(arrowX, arrowY);
      ctx.lineTo(arrowX - Math.cos(angle - 0.4) * 8, arrowY - Math.sin(angle - 0.4) * 8);
      ctx.lineTo(arrowX - Math.cos(angle + 0.4) * 8, arrowY - Math.sin(angle + 0.4) * 8);
      ctx.closePath();
      ctx.fillStyle = 'rgba(99,102,241,0.4)';
      ctx.fill();

      // Relationship label
      if (zoom > 0.7) {
        const mx = ((s.x ?? 0) + (t.x ?? 0)) / 2;
        const my = ((s.y ?? 0) + (t.y ?? 0)) / 2;
        ctx.font = `${10 / zoom}px sans-serif`;
        ctx.fillStyle = 'rgba(148,163,184,0.8)';
        ctx.textAlign = 'center';
        ctx.fillText(link.rel_type, mx, my - 4);
      }
    });

    // Draw nodes
    nodes.forEach(n => {
      const x = n.x ?? 0;
      const y = n.y ?? 0;
      const r = n.id === selectedNode?.id ? 18 : n.id === hoveredNode?.id ? 16 : 13;
      const color = getNodeColor(n.type);

      // Glow for selected
      if (n.id === selectedNode?.id) {
        ctx.beginPath();
        ctx.arc(x, y, r + 6, 0, Math.PI * 2);
        ctx.fillStyle = color + '33';
        ctx.fill();
      }

      // Node circle
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = n.id === selectedNode?.id ? '#fff' : color + 'aa';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Node label
      if (zoom > 0.5) {
        ctx.font = `bold ${11 / zoom}px Inter, sans-serif`;
        ctx.fillStyle = '#e2e8f0';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const maxLen = 14;
        const label = n.name.length > maxLen ? n.name.substring(0, maxLen) + '…' : n.name;
        ctx.fillText(label, x, y + r + 10 / zoom);
      }
    });

    ctx.restore();
  }

  function getNodeAtPoint(x: number, y: number, nodes: GraphNode[]): GraphNode | null {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const w = canvas.width;
    const h = canvas.height;
    const gx = (x - w / 2 - pan.x) / zoom;
    const gy = (y - h / 2 - pan.y) / zoom;

    for (const n of nodes) {
      const dx = (n.x ?? 0) - gx;
      const dy = (n.y ?? 0) - gy;
      if (Math.sqrt(dx * dx + dy * dy) < 18) return n;
    }
    return null;
  }

  function handleCanvasClick(e: React.MouseEvent<HTMLCanvasElement>) {
    const rect = canvasRef.current!.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const hit = getNodeAtPoint(x, y, graphData.nodes);
    setSelectedNode(hit);
  }

  function handleMouseMove(e: React.MouseEvent<HTMLCanvasElement>) {
    if (isPanning) {
      setPan(prev => ({ x: prev.x + e.movementX, y: prev.y + e.movementY }));
      return;
    }
    const rect = canvasRef.current!.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const hit = getNodeAtPoint(x, y, graphData.nodes);
    setHoveredNode(hit);
    if (canvasRef.current) {
      canvasRef.current.style.cursor = hit ? 'pointer' : 'grab';
    }
  }

  function handleWheel(e: React.WheelEvent<HTMLCanvasElement>) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(prev => Math.min(3, Math.max(0.2, prev * delta)));
  }

  const selectedNodeLinks = graphData.links.filter(l =>
    (typeof l.source === 'object' ? l.source.id : l.source) === selectedNode?.id ||
    (typeof l.target === 'object' ? l.target.id : l.target) === selectedNode?.id
  );

  return (
    <div className="flex flex-col h-full bg-slate-950 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-3 border-b border-slate-800 flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-sm font-bold text-slate-200">Knowledge Graph Explorer</h2>
          <p className="text-[11px] text-slate-500">
            {graphData.nodes.length} entities · {graphData.links.length} relationships
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button onClick={() => setZoom(z => Math.min(3, z * 1.2))} className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors">
            <ZoomIn className="w-4 h-4" />
          </button>
          <button onClick={() => setZoom(z => Math.max(0.2, z * 0.8))} className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors">
            <ZoomOut className="w-4 h-4" />
          </button>
          <button onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }} className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors">
            <Maximize2 className="w-4 h-4" />
          </button>
          <button onClick={fetchGraph} disabled={isLoading} className="px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-300 rounded text-xs font-semibold transition-all flex items-center space-x-1.5">
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* Canvas */}
        <div className="flex-1 relative min-h-0">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-950/70 z-10">
              <div className="flex flex-col items-center space-y-3">
                <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                <span className="text-xs text-slate-400">Loading graph from Neo4j...</span>
              </div>
            </div>
          )}

          {!isLoading && graphData.nodes.length === 0 && (
            <div className="absolute inset-0 flex flex-col items-center justify-center space-y-4 text-center p-8">
              <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-3xl">🕸️</div>
              <div>
                <h3 className="text-sm font-semibold text-slate-300">No graph entities yet</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-xs">
                  {error
                    ? `Neo4j connection error: ${error}`
                    : 'Upload a document first to extract entities and build the knowledge graph.'}
                </p>
              </div>
            </div>
          )}

          <canvas
            ref={canvasRef}
            width={800}
            height={600}
            className="w-full h-full"
            style={{ display: graphData.nodes.length > 0 ? 'block' : 'none' }}
            onClick={handleCanvasClick}
            onMouseMove={handleMouseMove}
            onMouseDown={() => setIsPanning(true)}
            onMouseUp={() => setIsPanning(false)}
            onMouseLeave={() => setIsPanning(false)}
            onWheel={handleWheel}
          />
        </div>

        {/* Right Panel */}
        <div className="w-64 border-l border-slate-800 flex flex-col bg-slate-900/50 shrink-0 overflow-hidden">
          {/* Legend */}
          <div className="p-4 border-b border-slate-800">
            <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Entity Types</h4>
            <div className="space-y-1.5">
              {Object.entries(TYPE_COLORS).filter(([k]) => !['Unknown', 'Companies', 'People', 'Products', 'Events', 'Metrics'].includes(k)).map(([type, color]) => (
                <div key={type} className="flex items-center space-x-2 text-xs text-slate-300">
                  <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: color }} />
                  <span>{TYPE_LABELS[type] || type}</span>
                  <span className="ml-auto text-slate-500 text-[10px]">
                    {graphData.nodes.filter(n => n.type?.toLowerCase().includes(type.toLowerCase())).length}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Selected node details */}
          <div className="flex-1 overflow-y-auto p-4">
            {selectedNode ? (
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: getNodeColor(selectedNode.type) }} />
                  <h4 className="text-xs font-bold text-slate-200 truncate">{selectedNode.name}</h4>
                </div>
                <div className="space-y-1 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Type</span>
                    <span className="text-indigo-400 font-semibold">{selectedNode.type || 'Unknown'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Labels</span>
                    <span className="text-slate-300">{selectedNode.labels.join(', ') || '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Connections</span>
                    <span className="text-emerald-400 font-semibold">{selectedNodeLinks.length}</span>
                  </div>
                </div>

                {selectedNodeLinks.length > 0 && (
                  <div>
                    <h5 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Relationships</h5>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto">
                      {selectedNodeLinks.map((link, i) => {
                        const srcId = typeof link.source === 'object' ? link.source.id : link.source;
                        const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
                        const isOutgoing = srcId === selectedNode.id;
                        return (
                          <div key={i} className="p-2 rounded bg-slate-950/60 border border-slate-800 text-[10px]">
                            <div className="font-semibold text-indigo-400">{link.rel_type}</div>
                            <div className="text-slate-400 mt-0.5 truncate">
                              {isOutgoing ? '→ ' : '← '}
                              <span className="text-slate-300">{isOutgoing ? tgtId : srcId}</span>
                            </div>
                            {(link.date || link.quarter) && (
                              <div className="text-slate-600 mt-0.5">{link.quarter || link.date}</div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-center py-8 space-y-2">
                <Info className="w-8 h-8 text-slate-700" />
                <p className="text-[11px] text-slate-500">Click a node to inspect its entity details and relationships</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
