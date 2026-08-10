import { Layers, Search } from "lucide-react";
import type { ToolCall } from "../lib/types";

const LABELS: Record<string, string> = {
  vector_search: "Vector search",
  hybrid_search: "Hybrid search",
  get_document: "Read document",
  list_documents: "Listed documents",
};

export function ToolChip({ tool }: { tool: ToolCall }) {
  const label = LABELS[tool.tool_name] ?? tool.tool_name;
  const query = typeof tool.args?.query === "string" ? (tool.args.query as string) : null;
  const Icon = tool.tool_name.includes("search") ? Search : Layers;

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full border border-ink-700 bg-ink-850 px-2.5 py-1 text-[0.7rem] text-paper-400"
      title={query ?? undefined}
    >
      <Icon className="h-3 w-3 text-ember-400" />
      {label}
      {query && <span className="max-w-[10rem] truncate text-paper-500">"{query}"</span>}
    </span>
  );
}
