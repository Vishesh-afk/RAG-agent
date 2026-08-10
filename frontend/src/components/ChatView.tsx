import { useEffect, useRef } from "react";
import { Mark } from "./Logo";
import { MessageBubble } from "./MessageBubble";
import { Composer } from "./Composer";
import type { ChatMessage } from "../lib/types";

const PROMPTS = [
  "Summarize the key findings across these documents",
  "What data sources or methods are referenced?",
  "List the main recommendations, with sources",
];

interface Props {
  messages: ChatMessage[];
  sending: boolean;
  hasDocuments: boolean;
  onSend: (text: string) => void;
}

export function ChatView({ messages, sending, hasDocuments, onSend }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex h-full min-w-0 flex-1 flex-col">
      <div ref={scrollRef} className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center px-6 text-center">
            <Mark className="h-12 w-12" />
            <h1 className="mt-5 font-display text-3xl font-medium text-paper-100">
              Ask your documents anything
            </h1>
            <p className="mt-2 max-w-md text-sm text-paper-400">
              {hasDocuments
                ? "Atlas searches your knowledge base and answers with cited sources."
                : "Ingest a PDF from the sidebar, then ask a question here."}
            </p>
            {hasDocuments && (
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {PROMPTS.map((p) => (
                  <button
                    key={p}
                    onClick={() => onSend(p)}
                    className="rounded-full border border-ink-700 bg-ink-850 px-3.5 py-1.5 text-xs text-paper-300 transition-colors hover:border-ember-600/50 hover:text-paper-100"
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-7 px-6 py-8">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
          </div>
        )}
      </div>
      <Composer disabled={sending} onSend={onSend} />
    </div>
  );
}
