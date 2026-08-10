import { useEffect, useRef, useState } from "react";
import { getHealth } from "../lib/api";
import type { HealthStatus } from "../lib/types";

const POLL_MS = 20_000;

export function useHealth() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [online, setOnline] = useState<boolean | null>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();

    async function check() {
      try {
        const h = await getHealth(controller.signal);
        if (cancelled) return;
        setHealth(h);
        setOnline(h.status === "healthy");
      } catch {
        if (cancelled) return;
        setOnline(false);
        setHealth(null);
      }
    }

    check();
    timer.current = window.setInterval(check, POLL_MS);

    return () => {
      cancelled = true;
      controller.abort();
      if (timer.current) window.clearInterval(timer.current);
    };
  }, []);

  return { health, online };
}
