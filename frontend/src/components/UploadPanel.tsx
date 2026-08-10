import { useCallback, useRef, useState } from "react";
import { CheckCircle2, FileUp, Loader2, TriangleAlert, X } from "lucide-react";
import { ingestDocument } from "../lib/api";

interface Props {
  onIngested: () => void;
}

type Status = "idle" | "uploading" | "success" | "error";

export function UploadPanel({ onIngested }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [clean, setClean] = useState(true);
  const [tables, setTables] = useState(false);
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const pick = useCallback((f: File | undefined | null) => {
    if (!f) return;
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setStatus("error");
      setMessage("Only PDF files are supported.");
      return;
    }
    setFile(f);
    setStatus("idle");
    setMessage(null);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      pick(e.dataTransfer.files?.[0]);
    },
    [pick]
  );

  const runIngest = useCallback(async () => {
    if (!file) return;
    setStatus("uploading");
    setMessage(null);
    try {
      const results = await ingestDocument(file, { clean, includeTables: tables, includeImages: tables });
      const chunks = results.reduce((sum, r) => sum + r.chunks_created, 0);
      setStatus("success");
      setMessage(`Indexed ${chunks} chunk${chunks === 1 ? "" : "s"} from "${file.name}"`);
      setFile(null);
      onIngested();
    } catch (err) {
      setStatus("error");
      setMessage(err instanceof Error ? err.message : "Ingestion failed.");
    }
  }, [file, clean, tables, onIngested]);

  return (
    <div className="space-y-3">
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => pick(e.target.files?.[0])}
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`group flex w-full flex-col items-center gap-2 rounded-xl border border-dashed px-4 py-6 text-center transition-colors ${
          dragging
            ? "border-ember-400 bg-ember-500/[0.06]"
            : "border-ink-600 bg-ink-850/60 hover:border-ink-500 hover:bg-ink-850"
        }`}
      >
        <FileUp className="h-5 w-5 text-paper-500 transition-colors group-hover:text-ember-400" />
        <div className="text-xs leading-snug text-paper-400">
          {file ? (
            <span className="font-medium text-paper-200">{file.name}</span>
          ) : (
            <>
              <span className="text-paper-200">Drop a PDF</span> or click to browse
            </>
          )}
        </div>
      </button>

      <div className="space-y-1.5 px-0.5 text-xs">
        <label className="flex cursor-pointer items-center gap-2 text-paper-400">
          <input
            type="checkbox"
            checked={clean}
            onChange={(e) => setClean(e.target.checked)}
            className="h-3.5 w-3.5 rounded-sm border-ink-500 bg-ink-800 accent-ember-500"
          />
          Replace existing documents
        </label>
        <label className="flex cursor-pointer items-center gap-2 text-paper-400">
          <input
            type="checkbox"
            checked={tables}
            onChange={(e) => setTables(e.target.checked)}
            className="h-3.5 w-3.5 rounded-sm border-ink-500 bg-ink-800 accent-ember-500"
          />
          Extract tables &amp; images
          <span className="text-paper-500">(slower)</span>
        </label>
      </div>

      {file && status !== "uploading" && (
        <button
          type="button"
          onClick={runIngest}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-ember-500 px-3 py-2 text-sm font-medium text-ink-950 transition-colors hover:bg-ember-400 active:bg-ember-600"
        >
          Ingest document
        </button>
      )}

      {status === "uploading" && (
        <div className="flex items-center gap-2 rounded-lg border border-ink-700 bg-ink-850 px-3 py-2 text-xs text-paper-300">
          <Loader2 className="h-3.5 w-3.5 animate-spin text-ember-400" />
          Extracting &amp; embedding…
        </div>
      )}

      {status !== "uploading" && message && (
        <div
          className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-xs ${
            status === "success"
              ? "border-sage-600/40 bg-sage-500/[0.08] text-sage-300"
              : "border-rust-500/40 bg-rust-500/[0.08] text-rust-400"
          }`}
        >
          {status === "success" ? (
            <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          ) : (
            <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          )}
          <span className="flex-1">{message}</span>
          <button onClick={() => setMessage(null)} className="text-paper-500 hover:text-paper-200">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
