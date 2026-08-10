import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Mark } from "./Logo";
import { ToolChip } from "./ToolChip";
import type { ChatMessage } from "../lib/types";

export function MessageBubble({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <div className="flex animate-fade-up justify-end">
        <div className="max-w-[42rem] rounded-2xl rounded-tr-sm bg-ember-500/[0.12] px-4 py-2.5 text-[0.95rem] leading-relaxed text-paper-100">
          {message.content}
        </div>
      </div>
    );
  }

  const showCaret = message.pending && message.content.length === 0;

  return (
    <div className="flex animate-fade-up gap-3">
      <div className="mt-0.5 shrink-0">
        <Mark className="h-6 w-6" />
      </div>
      <div className="min-w-0 flex-1 space-y-2.5 border-l border-ink-700 pl-4">
        {message.tools && message.tools.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.tools.map((t, i) => (
              <ToolChip key={t.tool_call_id ?? i} tool={t} />
            ))}
          </div>
        )}

        {showCaret ? (
          <span className="inline-block h-4 w-1.5 caret bg-paper-400" />
        ) : message.error ? (
          <p className="text-sm text-rust-400">{message.content}</p>
        ) : (
          <div className="prose-atlas">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
            {message.pending && <span className="caret ml-0.5 inline-block h-3.5 w-1.5 translate-y-0.5 bg-paper-400" />}
          </div>
        )}
      </div>
    </div>
  );
}
