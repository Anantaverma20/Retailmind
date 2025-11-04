"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient, VoiceLog } from "@/lib/api";
import { Mic, MessageSquare } from "lucide-react";
import { format } from "date-fns";

export function VoiceLogsPanel() {
  const { data: logs = [], isLoading, error } = useQuery({
    queryKey: ["voice-logs"],
    queryFn: () => apiClient.getVoiceLogs(50),
    refetchInterval: 10000, // Refetch every 10 seconds for live updates
  });

  const recentLogs = (logs as VoiceLog[]).slice(0, 10);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="space-y-2">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-red-600">
          Error loading voice logs: {error instanceof Error ? error.message : "Unknown error"}
        </div>
      </div>
    );
  }

  const getIntentColor = (intent: string) => {
    switch (intent) {
      case "get_stock":
        return "bg-blue-100 text-blue-800";
      case "create_reorder":
        return "bg-green-100 text-green-800";
      case "get_sales_summary":
        return "bg-purple-100 text-purple-800";
      case "get_supplier_info":
        return "bg-yellow-100 text-yellow-800";
      case "get_delivery_status":
        return "bg-orange-100 text-orange-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Mic className="h-5 w-5" />
            Live Voice Logs
          </h2>
          <div className="flex items-center gap-2 px-3 py-1 bg-green-50 rounded-lg border border-green-200">
            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs font-medium text-green-700">Live</span>
          </div>
        </div>
      </div>

      <div className="p-6 max-h-96 overflow-y-auto">
        {recentLogs.length === 0 ? (
          <div className="text-center py-8">
            <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-3" />
            <p className="text-sm text-gray-500">No voice logs yet</p>
            <p className="text-xs text-gray-400 mt-1">
              Voice interactions will appear here in real-time
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {recentLogs.map((log) => (
              <div
                key={log.id}
                className="p-3 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded ${getIntentColor(log.intent)}`}
                  >
                    {log.intent.replace("_", " ").toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-400">
                    {format(new Date(log.created_at), "HH:mm:ss")}
                  </span>
                </div>
                <p className="text-sm text-gray-900 mb-1">
                  <span className="font-medium">Transcript:</span> {log.transcript}
                </p>
                {log.result && !log.result.error && (
                  <p className="text-xs text-gray-600 mt-1">
                    <span className="font-medium">Response:</span> {log.result.speech || "Processed successfully"}
                  </p>
                )}
                {log.result?.error && (
                  <p className="text-xs text-red-600 mt-1">
                    <span className="font-medium">Error:</span> {log.result.error}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

