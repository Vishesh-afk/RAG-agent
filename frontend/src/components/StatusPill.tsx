interface Props {
  online: boolean | null;
}

export function StatusPill({ online }: Props) {
  const label = online === null ? "Checking…" : online ? "Online" : "Offline";
  const dot = online === null ? "bg-paper-400" : online ? "bg-sage-400" : "bg-rust-400";
  const ring = online === null ? "" : online ? "shadow-[0_0_0_3px_rgba(143,191,168,0.15)]" : "shadow-[0_0_0_3px_rgba(226,137,122,0.15)]";

  return (
    <div className="flex items-center gap-2 rounded-full border border-ink-700 bg-ink-850 px-3 py-1.5 text-xs text-paper-300">
      <span className={`relative h-1.5 w-1.5 rounded-full ${dot} ${ring}`}>
        {online && <span className="absolute inset-0 rounded-full bg-sage-400 animate-ping opacity-60" />}
      </span>
      <span className="font-mono tracking-tight">{label}</span>
    </div>
  );
}
