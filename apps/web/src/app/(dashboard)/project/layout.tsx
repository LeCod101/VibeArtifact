/**
 * 项目工作区路由组布局
 *
 * 抵消 dashboard 主区域的 p-6，使工作区可占满可用高度并自行管理内部滚动。
 */
import type { ReactNode } from "react";

export default function ProjectRoutesLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="flex flex-1 flex-col min-h-0 -m-6">{children}</div>
  );
}
