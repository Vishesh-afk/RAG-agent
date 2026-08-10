import { useEffect, useRef, useState } from "react";
import { ArrowUp } from "lucide-react";

interface Props {
  disabled: boolean;
  onSend: (text: string) => void;
}

export function Composer({ disabled, onSend }: Props) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [value]);

  const submit = () => {
    if (disabled || !value.trim()) return;
    onSend(value);
    setValue("");
  };

  return (
    <div className="border-t border-ink-700 bg-ink-900/80 px-6 py-4 backdrop-blur">
      <div className="mx-auto flex max-w-3xl items-end gap-2.5 rounded-2xl border border-ink-600 bg-ink-850 px-3.5 py-2.5 shadow-panel transition-colors focus-within:border-ember-600/60">
        <textarea
          ref={ref}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          rows={1}
          placeholder="Ask about your documents…"
          className="max-h-[200px] flex-1 resize-none bg-transparent text-[0.95rem] leading-relaxed text-paper-100 placeholder:text-paper-500 focus:outline-none"
        />
        <button
          onClick={submit}
          disabled={disabled || !value.trim()}
          className="mb-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ember-500 text-ink-950 transition-all enabled:hover:bg-ember-400 disabled:cursor-not-allowed disabled:opacity-30"
        >
          <ArrowUp className="h-4 w-4" />
        </button>
      </div>
      <p className="mx-auto mt-2 max-w-3xl text-center text-[0.68rem] text-paper-500">
        Atlas answers strictly from your ingested documents and cites its sources.
      </p>
    </div>
  );
}
