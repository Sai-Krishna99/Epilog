"use client";

import { useState, useMemo, useEffect, Component, ReactNode } from "react";
import {
  Terminal,
  Search,
  Settings,
  PlayCircle,
  AlertCircle,
  MessageSquare,
  Wrench,
  ChevronRight,
  Loader2,
  History,
  Layers,
  Zap,
  Check,
  FileCode,
  X,
  RefreshCw,
  Camera,
  Maximize2,
  Minimize2,
  ChevronDown,
  ChevronUp
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Slider } from "@/components/ui/slider";
import { Card } from "@/components/ui/card";
import {
  useSessions,
  useTraceStream,
  TraceEvent,
  useDiagnose,
  useApplyPatch,
  DiagnosisResponse
} from "@/lib/api";

// Error Boundary Component
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-screen bg-black text-white flex items-center justify-center">
          <div className="text-center space-y-4 max-w-md">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
            <h1 className="text-lg font-bold uppercase tracking-wider">Something went wrong</h1>
            <p className="text-sm text-slate-400 font-mono">{this.state.error?.message}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 border border-white text-xs font-bold uppercase tracking-wider hover:bg-white hover:text-black transition-colors"
            >
              <RefreshCw className="w-3 h-3 inline mr-2" />
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// Skeleton Loader for Sessions (deterministic widths to avoid hydration mismatch)
const SKELETON_WIDTHS = [65, 80, 70, 85, 75];

function SessionSkeleton() {
  return (
    <div className="space-y-1 py-2 animate-pulse">
      {SKELETON_WIDTHS.map((width, i) => (
        <div key={i} className="px-3 py-2 flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-slate-800" />
          <div className="h-4 bg-slate-800 rounded flex-1" style={{ width: `${width}%` }} />
        </div>
      ))}
    </div>
  );
}

function DashboardContent() {
  const { data: sessions, isLoading: sessionsLoading, error: sessionsError, refetch: refetchSessions } = useSessions();
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const { events } = useTraceStream(selectedSessionId);
  const [scrubberValue, setScrubberValue] = useState([0]);

  // AI Diagnosis State
  const [activeDiagnosis, setActiveDiagnosis] = useState<DiagnosisResponse | null>(null);
  const [diagnosingEventId, setDiagnosingEventId] = useState<number | null>(null);

  const { mutate: runDiagnose, isPending: isDiagnosing, error: diagnoseError, reset: resetDiagnoseError } = useDiagnose();
  const [diagnoseErrorMsg, setDiagnoseErrorMsg] = useState<string | null>(null);
  const { mutate: applyPatch, isPending: isApplyingPatch, isSuccess: patchApplied } = useApplyPatch();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showRawMetadata, setShowRawMetadata] = useState(false);

  // ESC key to close fullscreen
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsFullscreen(false);
    };
    if (isFullscreen) {
      window.addEventListener('keydown', handleEsc);
      return () => window.removeEventListener('keydown', handleEsc);
    }
  }, [isFullscreen]);

  const filteredSessions = useMemo(() => {
    if (!sessions) return [];
    if (!searchQuery.trim()) return sessions;
    const query = searchQuery.toLowerCase();
    return sessions.filter(s =>
      (s.name || "").toLowerCase().includes(query)
    );
  }, [sessions, searchQuery]);

  const activeSession = useMemo(() =>
    sessions?.find(s => s.id === selectedSessionId),
    [sessions, selectedSessionId]
  );

  useEffect(() => {
    if (scrubberValue[0] === 100 || events.length === 1) {
      setScrubberValue([100]);
    }
  }, [events.length]);

  const currentEventIndex = events.length === 0 ? -1 : Math.min(
    Math.round((scrubberValue[0] / 100) * (events.length - 1)),
    events.length - 1
  );

  const currentEvent = currentEventIndex >= 0 ? events[currentEventIndex] : null;

  const screenshotUrl = currentEvent?.has_screenshot
    ? `${API_BASE_URL}/api/v1/traces/events/${currentEvent.id}/screenshot`
    : null;

  // Count events with screenshots for UI hint
  const eventsWithScreenshots = useMemo(() =>
    events.filter(e => e.has_screenshot).map(e => events.indexOf(e) + 1),
    [events]
  );

  const handleDiagnose = (eventId: number) => {
    setDiagnosingEventId(eventId);
    setDiagnoseErrorMsg(null);
    runDiagnose(eventId, {
      onSuccess: (data) => {
        setActiveDiagnosis(data);
        setDiagnosingEventId(null);
      },
      onError: (error) => {
        setDiagnoseErrorMsg(error instanceof Error ? error.message : "Diagnosis failed");
        setDiagnosingEventId(null);
      }
    });
  };

  const handleApplyPatch = () => {
    if (!activeDiagnosis?.patch) return;

    // For demo, we assume agent.py if not specified
    // In real app, AI would provide the file path
    applyPatch({
      file_path: "agent.py",
      diff_content: activeDiagnosis.patch
    });
  };

  return (
    <div className="flex h-screen bg-black text-white font-sans overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-900 flex flex-col bg-black">
        <div className="p-4 flex items-center gap-2 border-b border-slate-900">
          <Terminal className="w-5 h-5 text-white" />
          <span className="font-bold tracking-tight text-lg uppercase tracking-tighter text-white">EPILOG</span>
        </div>

        <div className="p-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-slate-400" />
            <input
              placeholder="Filter sessions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-900 rounded-none py-1.5 pl-8 text-sm focus:outline-none focus:border-white/50 transition-colors"
            />
          </div>
        </div>

        <ScrollArea className="flex-1 px-2">
          <div className="space-y-1 py-2">
            {sessionsLoading ? (
              <SessionSkeleton />
            ) : sessionsError ? (
              <div className="text-center py-8 space-y-3">
                <AlertCircle className="w-6 h-6 text-red-500 mx-auto" />
                <p className="text-slate-500 text-xs font-mono">Failed to load sessions</p>
                <button
                  onClick={() => refetchSessions()}
                  className="px-3 py-1 border border-slate-700 text-[10px] font-bold uppercase tracking-wider hover:border-white hover:text-white transition-colors"
                >
                  Retry
                </button>
              </div>
            ) : filteredSessions.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-sm font-mono">
                {searchQuery ? "No matching sessions" : "No sessions yet"}
              </div>
            ) : filteredSessions.map((session) => (
              <button
                key={session.id}
                onClick={() => {
                  setSelectedSessionId(session.id);
                  setScrubberValue([100]);
                  setActiveDiagnosis(null);
                }}
                className={`w-full text-left px-3 py-2 text-sm flex items-center justify-between group transition-colors border-l-2 ${selectedSessionId === session.id ? "bg-slate-900 text-white border-white" : "text-slate-400 hover:text-white hover:bg-slate-950 border-transparent hover:border-slate-700"
                  }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <div className={`w-1.5 h-1.5 rounded-full ${selectedSessionId === session.id ? "bg-white" : "bg-slate-800"}`} />
                  <span className="truncate">{session.name || "Untitled Session"}</span>
                </div>
                <ChevronRight className={`w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity ${selectedSessionId === session.id ? "opacity-100" : ""}`} />
              </button>
            ))}
          </div>
        </ScrollArea>

        <div className="p-4 border-t border-slate-900 flex items-center justify-between text-slate-500 font-mono">
          <Settings className="w-4 h-4 cursor-pointer hover:text-white transition-colors" />
          <span className="text-[10px] lowercase italic">v0.1.0-alpha</span>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Diagnosis Error Toast */}
        {diagnoseErrorMsg && (
          <div className="absolute top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 bg-red-950 border border-red-800 text-red-400 text-xs font-mono animate-in slide-in-from-top-2">
            <AlertCircle className="w-4 h-4" />
            <span>{diagnoseErrorMsg}</span>
            <button
              onClick={() => setDiagnoseErrorMsg(null)}
              className="p-1 hover:text-white transition-colors"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        )}
        {/* Scrubber Area */}
        <header className="h-20 border-b border-slate-900 flex flex-col justify-center px-6 bg-black z-10 shrink-0">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-sm font-mono text-slate-400 tracking-wider uppercase truncate max-w-md">
              {activeSession ? activeSession.name : "Select a session"}
            </h2>
            {events.length > 0 && (
              <span className="text-xs text-white font-mono uppercase">
                EVENT {Math.max(1, currentEventIndex + 1)} OF {events.length}
              </span>
            )}
          </div>
          <Slider
            defaultValue={[0]}
            max={100}
            step={1}
            value={scrubberValue}
            onValueChange={setScrubberValue}
            disabled={events.length === 0}
            className="cursor-pointer"
          />
        </header>

        {/* Workspace: Feed & Preview */}
        <div className="flex-1 flex overflow-hidden">
          {/* Trace Feed */}
          <div className={`border-r border-slate-900 flex flex-col bg-black overflow-hidden transition-all duration-300 ${activeDiagnosis ? 'w-1/3' : 'w-1/2'}`}>
            <ScrollArea className="flex-1">
              <div className="p-6 max-w-2xl mx-auto space-y-8 pb-32">
                {events.length === 0 ? (
                  <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-sm font-mono border border-dashed border-slate-700">
                    <History className="w-8 h-8 mb-2 opacity-40" />
                    Waiting for events...
                  </div>
                ) : events.map((event, idx) => (
                  <StepCard
                    key={event.id}
                    active={idx === currentEventIndex}
                    event={event}
                    onDiagnose={() => handleDiagnose(event.id)}
                    isDiagnosing={diagnosingEventId === event.id}
                    onSelect={() => {
                      // Jump scrubber to this event
                      const newValue = events.length <= 1 ? 100 : Math.round((idx / (events.length - 1)) * 100);
                      setScrubberValue([newValue]);
                    }}
                  />
                ))}
              </div>
            </ScrollArea>
          </div>

          {/* Screenshot Preview / Surgery Room */}
          <div className={`bg-black transition-all duration-300 ${activeDiagnosis ? 'w-2/3 flex flex-row' : 'w-1/2'}`}>
            {/* Visual State (always visible, but shrinks when diagnosing) */}
            <div className={`p-8 flex flex-col items-center justify-center relative group ${activeDiagnosis ? 'w-1/2 border-r border-slate-900' : 'w-full'}`}>
              <div className="absolute top-4 left-4 text-[10px] font-mono text-slate-400 uppercase tracking-widest">Visual State</div>

              <div className="relative w-full max-w-2xl">
                <Card className="w-full aspect-video bg-black border-slate-700 rounded-none overflow-hidden flex flex-col items-center justify-center relative shadow-none">
                  {screenshotUrl ? (
                    <>
                      <img
                        src={screenshotUrl}
                        alt="Visual State"
                        className="w-full h-full object-contain cursor-pointer"
                        onClick={() => setIsFullscreen(true)}
                      />
                      <button
                        onClick={() => setIsFullscreen(true)}
                        className="absolute bottom-2 right-2 p-1.5 bg-black/80 border border-slate-700 text-slate-400 hover:text-white hover:border-white transition-colors"
                      >
                        <Maximize2 className="w-4 h-4" />
                      </button>
                    </>
                  ) : (
                    <div className="text-center">
                      <div className="text-slate-500 font-mono text-sm uppercase tracking-tighter">
                        {events.length > 0 ? "[ NO VISUAL FOR THIS EVENT ]" : "[ STANDBY ]"}
                      </div>
                      {eventsWithScreenshots.length > 0 && (
                        <div className="mt-3 text-slate-600 text-xs font-mono">
                          <Camera className="w-3 h-3 inline mr-1" />
                          Screenshots on events: {eventsWithScreenshots.join(", ")}
                        </div>
                      )}
                    </div>
                  )}
                  <div className="absolute top-2 right-2 px-2 py-1 bg-black/80 border border-slate-700 text-[9px] font-mono text-white">
                    {currentEvent?.timestamp ? (() => {
                      const d = new Date(currentEvent.timestamp);
                      return isNaN(d.getTime()) ? "--:--:--" : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                    })() : "--:--:--"}
                  </div>
                </Card>
                <div className="absolute -top-1 -left-1 w-4 h-4 border-t border-l border-white/30" />
                <div className="absolute -bottom-1 -right-1 w-4 h-4 border-b border-r border-white/30" />
              </div>

              {!activeDiagnosis && (
                <div className="mt-8 max-w-lg w-full">
                  <div className="flex items-center gap-4 text-[10px] font-mono text-slate-400 uppercase tracking-widest mb-2 border-b border-slate-800 pb-2">
                    <span>Metadata</span>
                    <span className="text-white ml-auto font-mono">
                      {currentEvent?.run_id ? `run: ${currentEvent.run_id.slice(0, 8)}` : "no active run"}
                    </span>
                  </div>
                  <MetadataDisplay
                    data={currentEvent?.event_data || {}}
                    showRaw={showRawMetadata}
                    onToggleRaw={() => setShowRawMetadata(!showRawMetadata)}
                  />
                </div>
              )}
            </div>

            {/* AI Surgery Room Panel */}
            {activeDiagnosis && (
              <div className="w-1/2 flex flex-col bg-slate-950/20 overflow-hidden relative">
                <div className="p-4 border-b border-slate-900 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-white" />
                    <span className="text-xs font-bold tracking-widest uppercase">Surgery Room</span>
                  </div>
                  <button
                    onClick={() => setActiveDiagnosis(null)}
                    className="p-1 hover:bg-slate-900 text-slate-500 hover:text-white transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <ScrollArea className="flex-1 p-6">
                  <div className="space-y-6 max-w-xl mx-auto">
                    {/* Diagnosis Report */}
                    <div>
                      <h5 className="text-[10px] font-mono text-slate-400 uppercase tracking-widest mb-3">Diagnosis Report</h5>
                      <div className="p-4 border border-slate-700 bg-black space-y-4">
                        <div className="flex items-start gap-3">
                          <AlertCircle className="w-4 h-4 text-white mt-0.5 shrink-0" />
                          <div>
                            <div className="text-xs font-bold text-white mb-1 uppercase tracking-tight">{activeDiagnosis.diagnosis.incident_summary}</div>
                            <p className="text-xs text-slate-300 font-mono leading-relaxed">{activeDiagnosis.diagnosis.explanation}</p>
                          </div>
                        </div>
                        {activeDiagnosis.diagnosis.visual_mismatch_identified && (
                          <div className="px-2 py-1 bg-amber-500/10 border border-amber-500/30 text-[9px] font-mono text-amber-400 inline-block">
                            VISUAL MISMATCH DETECTED
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Patch View */}
                    {activeDiagnosis.patch && (
                      <div className="space-y-3">
                        <h5 className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">Proposed Fix</h5>
                        <div className="relative group">
                          <div className="absolute top-2 right-2 flex items-center gap-2">
                            <span className="text-[9px] font-mono text-slate-400 bg-slate-900 px-1 border border-slate-700">agent.py</span>
                          </div>
                          <pre className="p-4 bg-black border border-slate-700 text-[11px] font-mono text-slate-300 overflow-auto max-h-[400px] scrollbar-hide whitespace-pre">
                            {activeDiagnosis.patch.split('\n').map((line: string, i: number) => (
                              <div key={i} className={line.startsWith('+') ? 'text-green-400 bg-green-500/10' : line.startsWith('-') ? 'text-red-400 bg-red-500/10' : ''}>
                                {line}
                              </div>
                            ))}
                          </pre>
                        </div>

                        <button
                          onClick={handleApplyPatch}
                          disabled={isApplyingPatch || patchApplied}
                          className={`w-full py-2 flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-widest transition-all ${patchApplied
                            ? "bg-white text-black cursor-default"
                            : "border border-white hover:bg-white hover:text-black disabled:opacity-50"
                            }`}
                        >
                          {isApplyingPatch ? (
                            <>
                              <Loader2 className="w-3 h-3 animate-spin" />
                              Applying...
                            </>
                          ) : patchApplied ? (
                            <>
                              <Check className="w-3 h-3" />
                              Patch Applied
                            </>
                          ) : (
                            <>
                              <FileCode className="w-3 h-3" />
                              Apply Patch
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Fullscreen Screenshot Modal */}
      {isFullscreen && screenshotUrl && (
        <div
          className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-4"
          onClick={() => setIsFullscreen(false)}
        >
          <button
            onClick={() => setIsFullscreen(false)}
            className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
          <div className="absolute top-4 left-4 text-xs font-mono text-slate-400">
            Click anywhere or press ESC to close
          </div>
          <img
            src={screenshotUrl}
            alt="Visual State (Fullscreen)"
            className="max-w-full max-h-full object-contain"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}

// Main export with Error Boundary wrapper
export default function Dashboard() {
  return (
    <ErrorBoundary>
      <DashboardContent />
    </ErrorBoundary>
  );
}

function MetadataDisplay({
  data,
  showRaw,
  onToggleRaw
}: {
  data: Record<string, unknown>,
  showRaw: boolean,
  onToggleRaw: () => void
}) {
  const formatValue = (value: unknown): string => {
    if (value === null || value === undefined) return "-";
    if (typeof value === "string") return value;
    if (typeof value === "number" || typeof value === "boolean") return String(value);
    if (typeof value === "object") {
      // For nested objects, show a summary
      const keys = Object.keys(value as object);
      if (keys.length === 0) return "{}";
      if (keys.length <= 2) {
        // Try to show small objects inline
        const str = JSON.stringify(value);
        return str.length <= 50 ? str : `{${keys.length} fields}`;
      }
      return `{${keys.length} fields}`;
    }
    return String(value);
  };

  const getKeyValuePairs = (obj: Record<string, unknown>): Array<{ key: string; value: string }> => {
    const commonKeys = ["tool", "name", "input", "output", "error", "message", "content", "url", "selector"];
    const pairs: Array<{ key: string; value: string }> = [];

    // First add common keys if they exist
    for (const key of commonKeys) {
      if (key in obj && obj[key] !== undefined) {
        pairs.push({ key, value: formatValue(obj[key]) });
      }
    }

    // Then add remaining keys
    for (const key of Object.keys(obj)) {
      if (!commonKeys.includes(key) && obj[key] !== undefined) {
        pairs.push({ key, value: formatValue(obj[key]) });
      }
    }

    return pairs;
  };

  const pairs = getKeyValuePairs(data);
  const isEmpty = pairs.length === 0;

  return (
    <div className="space-y-2">
      {!isEmpty && !showRaw && (
        <div className="space-y-1.5">
          {pairs.slice(0, 6).map(({ key, value }) => (
            <div key={key} className="flex items-start gap-3 text-[10px] font-mono">
              <span className="text-slate-500 min-w-[60px] uppercase">{key}</span>
              <span className="text-slate-300 break-all">{value}</span>
            </div>
          ))}
          {pairs.length > 6 && (
            <div className="text-[10px] font-mono text-slate-500 italic">
              +{pairs.length - 6} more fields
            </div>
          )}
        </div>
      )}

      {showRaw && (
        <pre className="text-[10px] text-slate-400 font-mono overflow-auto max-h-32 scrollbar-hide bg-slate-950/50 p-2 border border-slate-800">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}

      {isEmpty && !showRaw && (
        <div className="text-[10px] text-slate-500 font-mono italic">No metadata</div>
      )}

      <button
        onClick={onToggleRaw}
        className="flex items-center gap-1 text-[9px] font-mono text-slate-500 hover:text-slate-300 transition-colors uppercase tracking-wider"
      >
        {showRaw ? (
          <>
            <ChevronUp className="w-3 h-3" />
            Hide raw JSON
          </>
        ) : (
          <>
            <ChevronDown className="w-3 h-3" />
            Show raw JSON
          </>
        )}
      </button>
    </div>
  );
}

function StepCard({
  event,
  active,
  onDiagnose,
  isDiagnosing,
  onSelect
}: {
  event: TraceEvent,
  active: boolean,
  onDiagnose: () => void,
  isDiagnosing: boolean,
  onSelect: () => void
}) {
  const getIcon = (type: string) => {
    const t = type.toLowerCase();
    if (t.includes('tool')) return <Wrench className={`w-4 h-4 ${active ? 'text-white' : 'text-slate-500'}`} />;
    if (t.includes('error')) return <AlertCircle className="w-4 h-4 text-red-500" />;
    if (t.includes('llm') || t.includes('thought')) return <MessageSquare className={`w-4 h-4 ${active ? 'text-white' : 'text-slate-500'}`} />;
    return <Layers className={`w-4 h-4 ${active ? 'text-white' : 'text-slate-500'}`} />;
  };

  const getTitle = (event: TraceEvent) => {
    return event.event_type.replace(/_/g, ' ').toUpperCase();
  };

  const getContent = (event: TraceEvent) => {
    const data = event.event_data;
    if (typeof data === 'string') return data;

    // Format based on event type for human readability
    const type = event.event_type.toLowerCase();

    if (type.includes('chain_start')) {
      const name = data.name || 'Chain';
      const task = data.inputs?.task || data.inputs?.input || '';
      return task ? `${name}: "${task}"` : name;
    }

    if (type.includes('tool_start')) {
      const tool = data.tool || data.name || 'Tool';
      const input = data.input || data.action_input || '';
      return input ? `${tool}: ${input}` : tool;
    }

    if (type.includes('tool_end')) {
      return data.output || data.content || 'Completed';
    }

    if (type.includes('error')) {
      return data.error || data.message || JSON.stringify(data);
    }

    // Fallback: try common fields, then JSON
    if (data.output) return data.output;
    if (data.content) return data.content;
    if (data.message) return data.message;

    return JSON.stringify(data, null, 2);
  };

  const isError = event.event_type.toLowerCase().includes('error');
  const isToolEnd = event.event_type.toLowerCase() === 'tool_end';
  const isChainStart = event.event_type.toLowerCase() === 'chain_start';

  // Color coding for border based on event type
  const getBorderColor = () => {
    if (active) return "border-white";
    if (isError) return "border-red-800";
    if (isToolEnd && event.has_screenshot) return "border-blue-800";
    if (isChainStart) return "border-emerald-800";
    return "border-slate-700";
  };

  return (
    <div
      className={`group relative pl-8 border-l-2 transition-all duration-200 cursor-pointer ${getBorderColor()} ${active ? "opacity-100" : "opacity-80 hover:opacity-100"}`}
      onClick={onSelect}
    >
      <div className={`absolute -left-2.5 top-0 p-1 translate-y-[-2px] transition-all ${active ? "bg-black scale-110" : "bg-black"
        }`}>
        {getIcon(event.event_type)}
      </div>
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h4 className={`text-[10px] font-bold tracking-widest transition-colors ${active ? "text-white" : "text-slate-300"}`}>
              {getTitle(event)}
            </h4>
            {event.has_screenshot && (
              <Camera className="w-3 h-3 text-blue-400" />
            )}
          </div>
          <span className={`text-[10px] font-mono ${active ? "text-slate-200" : "text-slate-400"}`}>
            {(() => {
              const d = new Date(event.timestamp);
              return isNaN(d.getTime()) ? "Invalid" : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
            })()}
          </span>
        </div>
        <div className={`group/card relative p-3 border font-mono text-xs leading-relaxed transition-all ${active ? "border-white/30 bg-white/5 text-slate-100" : "border-slate-700 bg-slate-950/30 text-slate-300"
          } ${isError ? 'border-red-800/50 text-red-400' : ''}`}>
          {getContent(event)}

          {/* Action Footer */}
          <div className="mt-3 pt-2 border-t border-slate-800 flex items-center justify-end opacity-0 group-hover/card:opacity-100 transition-opacity">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDiagnose();
              }}
              disabled={isDiagnosing}
              className="px-2 py-0.5 border border-white/30 text-[9px] font-bold uppercase transition-all hover:bg-white hover:text-black flex items-center gap-1.5 disabled:opacity-50"
            >
              {isDiagnosing ? (
                <>
                  <Loader2 className="w-2.5 h-2.5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Zap className="w-2.5 h-2.5" />
                  Diagnose
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
