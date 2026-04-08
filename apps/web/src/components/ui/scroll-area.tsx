"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

/**
 * 可滚动区域：侧边栏列表等场景使用，避免引入 Radix 依赖
 */
function ScrollArea({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="scroll-area"
      className={cn("relative overflow-auto", className)}
      {...props}
    >
      {children}
    </div>
  )
}

export { ScrollArea }
