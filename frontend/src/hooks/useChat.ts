import { useCallback, useEffect, useRef, useState } from "react";
import { streamChat } from "../lib/api";
import type { ChatMessage, StreamEvent } from "../lib/types";

const SESSION_KEY = "atlas.session_id";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sending, setSending] = useState(false);
  const sessionId = useRef<string | null>(sessionStorage.getItem(SESSION_KEY));
  const abortRef = useRef<(() => void) | null>(null);

  useEffect(() => () => abortRef.current?.(), []);

  const send = useCallback((text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const userMsg: ChatMessage = { id: uid(), role: "user", content: trimmed };
    const assistantId = uid();
    const assistantMsg: ChatMessage = { id: assistantId, role: "assistant", content: "", pending: true };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setSending(true);

    const patchAssistant = (patch: Partial<ChatMessage>) => {
      setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, ...patch } : m)));
    };

    const onEvent = (event: StreamEvent) => {
      switch (event.type) {
        case "session":
          sessionId.current = event.session_id;
          sessionStorage.setItem(SESSION_KEY, event.session_id);
          break;
        case "text":
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + event.content } : m))
          );
          break;
        case "tools":
          patchAssistant({ tools: event.tools });
          break;
        case "error":
          patchAssistant({ error: true, pending: false, content: event.content || "Something went wrong." });
          break;
        case "end":
          patchAssistant({ pending: false });
          break;
      }
    };

    abortRef.current = streamChat(
      trimmed,
      sessionId.current,
      onEvent,
      () => setSending(false),
      (err) => {
        patchAssistant({ error: true, pending: false, content: `Connection error: ${err.message}` });
        setSending(false);
      }
    );
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.();
    setMessages([]);
    setSending(false);
    sessionId.current = null;
    sessionStorage.removeItem(SESSION_KEY);
  }, []);

  return { messages, sending, send, reset };
}
