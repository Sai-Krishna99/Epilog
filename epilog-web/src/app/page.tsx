"use client";

import { useState, useMemo, useEffect } from "react";
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
  Layers
} from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Slider } from "@/components/ui/slider";
import { Card } from "@/components/ui/card";
import { useSessions, useTraceStream, TraceEvent } from "@/lib/api";

export default function Dashboard() {
  const { data: sessions, isLoading: sessionsLoading } = useSessions();
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  const { events } = useTraceStream(selectedSessionId);
  const [scrubberValue, setScrubberValue] = useState([0]);

  const activeSession = useMemo(() =>
    sessions?.find(s => s.id === selectedSessionId),
    [sessions, selectedSessionId]
  );

  // Sync scrubber to 100% when new events arrive and it was already at 100%
  useEffect(() => {
    if (scrubberValue[0] === 100 || events.length === 1) {
      setScrubberValue([100]);
    }
  }, [events.length]);

  // Determine the current event based on the scrubber
  const currentEventIndex = events.length === 0 ? -1 : Math.min(
    Math.floor((scrubberValue[0] / 100) * (events.length - 1)),
    events.length - 1
  );

  const currentEvent = currentEventIndex >= 0 ? events[currentEventIndex] : null;

  const screenshotUrl = currentEvent?.has_screenshot
    ? `http://localhost:8000/api/v1/traces/events/${currentEvent.id}/screenshot`
    : null;

  return (
    <div className="flex h-screen bg-black text-white font-sans overflow-hidden">
      {/* Sidebar: Navigation & Sessions */}
      <aside className="w-64 border-r border-slate-900 flex flex-col bg-black">
        <div className="p-4 flex items-center gap-2 border-b border-slate-900">
          <Terminal className="w-5 h-5 text-white" />
          <span className="font-bold tracking-tight text-lg uppercase tracking-tighter">EPILOG</span>
        </div>

        <div className="p-2">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-slate-500" />
            <input
              placeholder="Filter sessions..."
              className="w-full bg-slate-950 border border-slate-900 rounded-none py-1.5 pl-8 text-sm focus:outline-none focus:border-white/50 transition-colors"
            />
          </div>
        </div>

        <ScrollArea className="flex-1 px-2">
          <div className="space-y-1 py-2">
            {sessionsLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-4 h-4 animate-spin text-slate-700" />
              </div>
            ) : sessions?.map((session) => (
              <button
                key={session.id}
                onClick={() => {
                  setSelectedSessionId(session.id);
                  setScrubberValue([100]);
                }}
                className={`w-full text-left px-3 py-2 text-sm flex items-center justify-between group transition-colors ${selectedSessionId === session.id ? "bg-slate-900 text-white" : "text-slate-500 hover:text-white hover:bg-slate-950"
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
          <div className="w-1/2 border-r border-slate-900 flex flex-col bg-black overflow-hidden">
            <ScrollArea className="flex-1">
              <div className="p-6 max-w-2xl mx-auto space-y-8 pb-32">
                {events.length === 0 ? (
                  <div className="h-64 flex flex-col items-center justify-center text-slate-800 text-sm font-mono border border-dashed border-slate-900">
                    <History className="w-8 h-8 mb-2 opacity-20" />
                    Waiting for events...
                  </div>
                ) : events.map((event, idx) => (
                  <StepCard
                    key={event.id}
                    active={idx === currentEventIndex}
                    event={event}
                  />
                ))}
              </div>
            </ScrollArea>
          </div>

          {/* Screenshot Preview */}
          <div className="w-1/2 bg-black p-8 flex flex-col items-center justify-center relative group">
            <div className="absolute top-4 left-4 text-[10px] font-mono text-slate-700 uppercase tracking-widest">Visual State</div>

            <div className="relative w-full max-w-2xl">
              <Card className="w-full aspect-video bg-black border-slate-800 rounded-none overflow-hidden flex items-center justify-center relative shadow-none">
                {screenshotUrl ? (
                  <img src={screenshotUrl} alt="Visual State" className="w-full h-full object-contain" />
                ) : (
                  <div className="text-slate-800 font-mono text-sm uppercase tracking-tighter">
                    {events.length > 0 ? "[ NO VISUAL_DATA ]" : "[ STANDBY ]"}
                  </div>
                )}
                <div className="absolute top-2 right-2 px-2 py-1 bg-black/80 border border-slate-800 text-[9px] font-mono text-white">
                  {currentEvent?.timestamp ? new Date(currentEvent.timestamp).toLocaleTimeString() : "--:--:--"}
                </div>
              </Card>
              <div className="absolute -top-1 -left-1 w-4 h-4 border-t border-l border-white/20" />
              <div className="absolute -bottom-1 -right-1 w-4 h-4 border-b border-r border-white/20" />
            </div>

            <div className="mt-8 max-w-lg w-full">
              <div className="flex items-center gap-4 text-[10px] font-mono text-slate-500 uppercase tracking-widest mb-2 border-b border-slate-900 pb-2">
                <span>Metadata</span>
                <span className="text-white ml-auto font-mono">
                  {currentEvent?.run_id ? `run: ${currentEvent.run_id.slice(0, 8)}` : "no active run"}
                </span>
              </div>
              <pre className="text-[10px] text-slate-500 font-mono overflow-auto max-h-32 scrollbar-hide">
                {JSON.stringify(currentEvent?.event_data || {}, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function StepCard({ event, active }: { event: TraceEvent, active: boolean }) {
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
    if (data.action_input) return `Input: ${typeof data.action_input === 'object' ? JSON.stringify(data.action_input) : data.action_input}`;
    if (data.content) return data.content;
    if (data.output) return data.output;
    return JSON.stringify(data);
  };

  return (
    <div className={`group relative pl-8 border-l transition-all duration-200 ${active ? "border-white opacity-100" : "border-slate-800 opacity-70 hover:opacity-100"
      }`}>
      <div className={`absolute -left-2 top-0 p-1 translate-y-[-2px] transition-all ${active ? "bg-black scale-110" : "bg-black"
        }`}>
        {getIcon(event.event_type)}
      </div>
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <h4 className={`text-[10px] font-bold tracking-widest transition-colors ${active ? "text-white/90" : "text-slate-400"}`}>
            {getTitle(event)}
          </h4>
          <span className={`text-[9px] font-mono ${active ? "text-slate-400" : "text-slate-600"}`}>
            {new Date(event.timestamp).toLocaleTimeString([], { hour12: false })}
          </span>
        </div>
        <div className={`p-3 border font-mono text-xs leading-relaxed transition-all ${active ? "border-white/20 bg-white/5 text-slate-100" : "border-slate-900/50 bg-slate-950/20 text-slate-300"
          } ${event.event_type.toLowerCase().includes('error') ? 'border-red-900/30 text-red-400' : ''}`}>
          {getContent(event)}
        </div>
      </div>
    </div>
  );
}
