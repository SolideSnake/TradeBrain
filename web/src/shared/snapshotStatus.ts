import type { SnapshotResponse } from "./api";

export function formatSnapshotCacheStatus(response: SnapshotResponse | null) {
  if (!response) {
    return "--";
  }

  switch (response.cache_status) {
    case "success":
      return response.from_cache ? "缓存快照" : "刚刚刷新";
    case "failed":
      return "刷新失败，显示旧快照";
    case "refreshing":
      return "刷新中";
    case "empty":
      return "暂无快照";
    case "idle":
    default:
      return "空闲";
  }
}
