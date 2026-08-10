export interface HealthStatus {
  status: "healthy" | "unhealthy";
  database: boolean;
  llm_connection: boolean;
  version: string;
  timestamp: string;
}

export interface DocumentMetadata {
  id: string;
  title: string;
  source: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  chunk_count: number | null;
}

export interface ToolCall {
  tool_name: string;
  args: Record<string, unknown>;
  tool_call_id: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  tools?: ToolCall[];
  pending?: boolean;
  error?: boolean;
}

export interface IngestionResult {
  document_id: string;
  title: string;
  chunks_created: number;
  processing_time_ms: number;
}

export type StreamEvent =
  | { type: "session"; session_id: string }
  | { type: "text"; content: string }
  | { type: "tools"; tools: ToolCall[] }
  | { type: "end" }
  | { type: "error"; content: string };
