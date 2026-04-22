import { useEffect } from "react";
import { useAppStore } from "../store/useAppStore";

const DATA_URL = "/data/features.json";

export function useFeatureData(): { loading: boolean; error: string | null } {
  const setPayload = useAppStore((s) => s.setPayload);
  const payload = useAppStore((s) => s.payload);

  useEffect(() => {
    if (payload) return;
    fetch(DATA_URL)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => setPayload(data))
      .catch(console.error);
  }, [payload, setPayload]);

  return { loading: payload === null, error: null };
}
