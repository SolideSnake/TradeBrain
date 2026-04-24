import { useCallback, useEffect, useState } from "react";

import { type CanonicalSnapshot, type SnapshotResponse, getSnapshot } from "../shared/api";
import { SNAPSHOT_REFRESHED_EVENT, type SnapshotRefreshedEventDetail } from "../shared/snapshotEvents";

interface UseSnapshotResourceOptions {
  loadErrorMessage: string;
}

export function useSnapshotResource(options: UseSnapshotResourceOptions) {
  const [snapshot, setSnapshot] = useState<CanonicalSnapshot | null>(null);
  const [snapshotResponse, setSnapshotResponse] = useState<SnapshotResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const applySnapshotResponse = useCallback((response: SnapshotResponse) => {
    setSnapshotResponse(response);
    if (response.snapshot) {
      setSnapshot(response.snapshot);
    }
    setError(response.last_error || null);
    setLoading(false);
  }, []);

  const loadSnapshot = useCallback(async () => {
    setLoading(true);
    try {
      const nextSnapshot = await getSnapshot();
      applySnapshotResponse(nextSnapshot);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : options.loadErrorMessage);
      setLoading(false);
    }
  }, [applySnapshotResponse, options.loadErrorMessage]);

  useEffect(() => {
    void loadSnapshot();
  }, [loadSnapshot]);

  useEffect(() => {
    function handleSnapshotRefreshed(event: Event) {
      const detail = (event as CustomEvent<SnapshotRefreshedEventDetail>).detail;
      if (!detail?.response) {
        return;
      }

      applySnapshotResponse(detail.response);
    }

    window.addEventListener(SNAPSHOT_REFRESHED_EVENT, handleSnapshotRefreshed);
    return () => window.removeEventListener(SNAPSHOT_REFRESHED_EVENT, handleSnapshotRefreshed);
  }, [applySnapshotResponse]);

  return {
    snapshot,
    snapshotResponse,
    loading,
    error,
    setError,
    loadSnapshot,
    applySnapshotResponse,
  };
}
