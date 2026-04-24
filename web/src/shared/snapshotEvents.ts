import type { SnapshotResponse } from "./api";

export const SNAPSHOT_REFRESHED_EVENT = "tradebrain:snapshot-refreshed";

export interface SnapshotRefreshedEventDetail {
  response: SnapshotResponse;
}

export function dispatchSnapshotRefreshed(response: SnapshotResponse) {
  window.dispatchEvent(
    new CustomEvent<SnapshotRefreshedEventDetail>(SNAPSHOT_REFRESHED_EVENT, {
      detail: { response },
    }),
  );
}
