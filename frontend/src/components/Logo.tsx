export function Mark({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} fill="none">
      <rect width="32" height="32" rx="7" fill="#1c1a17" />
      <path
        d="M9 22.5 16 8l7 14.5"
        stroke="#e2884a"
        strokeWidth="2.1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="16" cy="17.4" r="1.6" fill="#8fbfa8" />
    </svg>
  );
}

export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <Mark className="h-7 w-7 shrink-0" />
      <div className="leading-none">
        <div className="font-display text-[1.2rem] font-medium tracking-tight text-paper-100">Atlas</div>
        <div className="text-[0.65rem] uppercase tracking-[0.16em] text-paper-500">Document Intelligence</div>
      </div>
    </div>
  );
}
