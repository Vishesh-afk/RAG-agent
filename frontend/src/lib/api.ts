import type { DocumentMetadata, HealthStatus, IngestionResult, StreamEvent } from "./types";

export const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8058";

class ApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.status = status;
  }
}

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response wasn't JSON, keep statusText
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

export async function getHealth(signal?: AbortSignal): Promise<HealthStatus> {
  const res = await fetch(`${API_URL}/health`, { signal });
  return asJson<HealthStatus>(res);
}

export async function listDocuments(): Promise<DocumentMetadata[]> {
  const res = await fetch(`${API_URL}/documents?limit=100`);
  const data = await asJson<{ documents: DocumentMetadata[] }>(res);
  return data.documents;
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/documents/${id}`, { method: "DELETE" });
  await asJson(res);
}

export async function deleteAllDocuments(): Promise<void> {
  const res = await fetch(`${API_URL}/documents`, { method: "DELETE" });
  await asJson(res);
}

export interface IngestOptions {
  clean: boolean;
  includeTables: boolean;
  includeImages: boolean;
}

export async function ingestDocument(file: File, opts: IngestOptions): Promise<IngestionResult[]> {
  const form = new FormData();
  form.append("file", file, file.name);
  form.append("clean", String(opts.clean));
  form.append("include_tables", String(opts.includeTables));
  form.append("include_images", String(opts.includeImages));

  const res = await fetch(`${API_URL}/ingest`, { method: "POST", body: form });
  return asJson<IngestionResult[]>(res);
}

/**
 * Opens the SSE chat stream and invokes `onEvent` for every parsed event.
 * Returns an abort function the caller can use to cancel mid-stream.
 */
export function streamChat(
  message: string,
  sessionId: string | null,
  onEvent: (event: StreamEvent) => void,
  onDone: () => void,
  onError: (err: Error) => void
): () => void {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          session_id: sessionId,
          user_id: "web-user",
          search_type: "hybrid",
        }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        throw new ApiError(`Chat stream failed (${res.status})`, res.status);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const payload = trimmed.slice(5).trim();
          if (!payload) continue;
          try {
            onEvent(JSON.parse(payload) as StreamEvent);
          } catch {
            // skip malformed SSE frame
          }
        }
      }
      onDone();
    } catch (err) {
      if ((err as { name?: string }).name === "AbortError") return;
      onError(err instanceof Error ? err : new Error(String(err)));
    }
  })();

  return () => controller.abort();
}
