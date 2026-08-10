import { FileText, Trash2 } from "lucide-react";
import type { DocumentMetadata } from "../lib/types";

interface Props {
  documents: DocumentMetadata[];
  loading: boolean;
  onDelete: (id: string) => void;
  onDeleteAll: () => void;
}

export function DocumentList({ documents, loading, onDelete, onDeleteAll }: Props) {
  if (!loading && documents.length === 0) {
    return <p className="px-0.5 text-xs text-paper-500">No documents indexed yet.</p>;
  }

  return (
    <div className="space-y-1.5">
      <ul className="space-y-1">
        {documents.map((doc) => (
          <li
            key={doc.id}
            className="group flex items-center gap-2.5 rounded-lg border border-transparent px-2 py-1.5 transition-colors hover:border-ink-700 hover:bg-ink-850"
          >
            <FileText className="h-3.5 w-3.5 shrink-0 text-paper-500" />
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-medium text-paper-200">{doc.title}</div>
              <div className="text-[0.68rem] text-paper-500">{doc.chunk_count ?? 0} chunks</div>
            </div>
            <button
              onClick={() => onDelete(doc.id)}
              className="shrink-0 text-paper-500 opacity-0 transition-opacity hover:text-rust-400 group-hover:opacity-100"
              title="Delete document"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </li>
        ))}
      </ul>

      {documents.length > 0 && (
        <button
          onClick={onDeleteAll}
          className="w-full rounded-lg border border-ink-700 px-2.5 py-1.5 text-[0.68rem] text-paper-500 transition-colors hover:border-rust-500/40 hover:text-rust-400"
        >
          Clear all documents
        </button>
      )}
    </div>
  );
}
