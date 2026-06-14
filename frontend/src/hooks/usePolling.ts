import { useEffect, useState } from "react";

export function usePolling<T>(loader: () => Promise<T>, intervalMs = 30000) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;

    async function run() {
      try {
        setError(false);
        const nextData = await loader();
        if (active) setData(nextData);
      } catch {
        if (active) setError(true);
      } finally {
        if (active) setLoading(false);
      }
    }

    run();
    const id = window.setInterval(run, intervalMs);
    return () => {
      active = false;
      window.clearInterval(id);
    };
  }, [loader, intervalMs]);

  return { data, loading, error };
}
