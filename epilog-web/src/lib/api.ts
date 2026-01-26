"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";

const API_BASE_URL = "http://localhost:8000/api/v1/traces";

export interface TraceSession {
    id: string;
    name: string;
    created_at: string;
    metadata: any;
}

export interface TraceEvent {
    id: number;
    run_id: string;
    event_type: string;
    timestamp: string;
    event_data: any;
    has_screenshot: boolean;
}

export function useSessions() {
    return useQuery<TraceSession[]>({
        queryKey: ["sessions"],
        queryFn: async () => {
            const res = await fetch(`${API_BASE_URL}/sessions`);
            if (!res.ok) throw new Error("Failed to fetch sessions");
            return res.json();
        },
    });
}

export function useTraceStream(sessionId: string | null) {
    const [events, setEvents] = useState<TraceEvent[]>([]);
    const queryClient = useQueryClient();

    useEffect(() => {
        if (!sessionId) {
            setEvents([]);
            return;
        }

        // Reset events when session changes
        setEvents([]);

        const eventSource = new EventSource(`${API_BASE_URL}/sessions/${sessionId}/events/stream`);

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.error) {
                    console.error("SSE Error:", data.error);
                    return;
                }
                setEvents((prev) => {
                    // Prevent duplicates if SSE reconnects
                    if (prev.some((e) => e.id === data.id)) return prev;
                    return [...prev, data].sort((a, b) => a.id - b.id);
                });
            } catch (err) {
                console.error("Failed to parse SSE message:", err);
            }
        };

        eventSource.onerror = (err) => {
            console.error("EventSource failed:", err);
            eventSource.close();
        };

        return () => {
            eventSource.close();
        };
    }, [sessionId]);

    return { events };
}

export interface DiagnosisReport {
    incident_summary: string;
    visual_mismatch_identified: boolean;
    explanation: string;
    suggested_fix_logic: string;
}

export interface DiagnosisResponse {
    diagnosis: DiagnosisReport;
    patch: string | null;
}

export function useDiagnose() {
    return useMutation({
        mutationFn: async (eventId: number): Promise<DiagnosisResponse> => {
            const res = await fetch(`${API_BASE_URL}/events/${eventId}/diagnose`, {
                method: "POST",
            });
            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || "Diagnosis failed");
            }
            return res.json();
        },
    });
}

export function useApplyPatch() {
    return useMutation({
        mutationFn: async (data: { file_path: string; diff_content: string }) => {
            const res = await fetch(`${API_BASE_URL}/apply-patch`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            });
            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || "Failed to apply patch");
            }
            return res.json();
        },
    });
}
