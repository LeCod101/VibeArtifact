/**
 * 全权委托 feature 统一导出
 *
 * 导出所有组件、hooks 和 API 函数，
 * 外部通过 @/features/delegation 统一引入。
 */

/* ============ API 层 ============ */
export {
  createDelegatedRun,
  getDelegatedRun,
  getDownloadUrl,
} from "./api";
export type {
  CreateDelegatedRunParams,
  CreateDelegatedRunResponse,
  DelegatedStepData,
  DelegatedRunData,
  SSEEventData,
} from "./api";

/* ============ Hooks ============ */
export { useSSE } from "./hooks/use-sse";
export {
  useCreateDelegatedRun,
  useDelegatedRun,
  useDownloadZip,
} from "./hooks/use-delegated";

/* ============ 组件 ============ */
export { DelegatedTrigger } from "./components/delegated-trigger";
export { DagProgress } from "./components/dag-progress";
export { DownloadPanel } from "./components/download-panel";
