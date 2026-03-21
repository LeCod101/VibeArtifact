/**
 * 404 页面 - 页面未找到
 *
 * 简洁的 404 错误页面，带大号数字和返回首页按钮。
 */
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      {/* 大号 404 数字 */}
      <h1 className="font-serif-display text-[120px] md:text-[160px] font-bold leading-none text-foreground/10 select-none">
        404
      </h1>

      {/* 标题 */}
      <h2 className="mt-2 text-xl md:text-2xl font-bold text-foreground">
        页面未找到
      </h2>

      {/* 描述文字 */}
      <p className="mt-2 text-sm text-muted-foreground text-center max-w-md">
        您访问的页面不存在或已被移除
      </p>

      {/* 返回首页按钮 */}
      <Link
        href="/dashboard"
        className="mt-8 inline-flex items-center justify-center rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
      >
        返回首页
      </Link>
    </div>
  );
}
