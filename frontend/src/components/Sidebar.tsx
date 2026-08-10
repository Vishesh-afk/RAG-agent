import { RotateCcw } from "lucide-react";
import { Wordmark } from "./Logo";
import { StatusPill } from "./StatusPill";
import { UploadPanel } from "./UploadPanel";
import { DocumentList } from "./DocumentList";
import type { DocumentMetadata } from "../lib/types";

interface Props {
  online: boolean | null;
  documents: DocumentMetadata[];
  documentsLoading: boolean;
  onIngested: () => void;
  onDelete: (id: string) => void;
  onDeleteAll: () => void;
  onNewChat: () => void;
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <div className="mb-2.5 font-mono text-[0.65rem] uppercase tracking-[0.14em] text-paper-500">{children}</div>;
}

export function Sidebar({ online, documents, documentsLoading, onIngested, onDelete, onDeleteAll, onNewChat }: Props) {
  return (
    <aside className="flex h-full w-[19rem] shrink-0 flex-col border-r border-ink-700 bg-ink-900">
      <div className="flex items-center justify-between border-b border-ink-700 px-5 py-4">
        <Wordmark />
      </div>

      <div className="flex items-center justify-between px-5 py-3">
        <StatusPill online={online} />
        <button
          onClick={onNewChat}
          className="flex items-center gap-1.5 rounded-full border border-ink-700 px-3 py-1.5 text-xs text-paper-400 transition-colors hover:border-ink-500 hover:text-paper-100"
        >
          <RotateCcw className="h-3 w-3" />
          New chat
        </button>
      </div>

      <div className="flex-1 space-y-6 overflow-y-auto px-5 py-3">
        <section>
          <SectionLabel>Ingest a document</SectionLabel>
          <UploadPanel onIngested={onIngested} />
        </section>

        <section>
          <SectionLabel>
            Knowledge base{documents.length > 0 ? ` · ${documents.length}` : ""}
          </SectionLabel>
          <DocumentList documents={documents} loading={documentsLoading} onDelete={onDelete} onDeleteAll={onDeleteAll} />
        </section>
      </div>

      <div className="border-t border-ink-700 px-5 py-3 text-[0.65rem] text-paper-500">
        Pydantic&nbsp;AI · pgvector · Docling
      </div>
    </aside>
  );
}
