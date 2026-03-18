/**
 * 侧边栏组件 - Claude 风格 64px 纯图标深色侧栏
 *
 * 深色背景，仅显示图标，底部用户头像和下拉菜单。
 */
"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, LogOut, Languages } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useAuthStore } from "@/stores/auth-store";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 导航项定义 */
const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: { zh: "仪表盘", en: "Dashboard" } },
];

export function Sidebar() {
  const { locale, toggleLocale } = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  /** 获取用户首字母作为头像 */
  const initials = user?.display_name
    ? user.display_name.charAt(0).toUpperCase()
    : user?.email?.charAt(0).toUpperCase() ?? "U";

  return (
    <aside className="hidden lg:flex w-16 flex-col items-center bg-sidebar h-screen sticky top-0 py-4">
      {/* Logo 图标 */}
      <Link href="/dashboard" className="mb-6">
        <svg viewBox="60 30 180 110" className="h-7 w-7 text-sidebar-foreground">
          <g fill="currentColor">
            <polygon points="85,40 119,108 109,128 65,40" />
            <polygon points="165,40 185,40 235,140 215,140 175,60 125,160 115,140 165,40" />
            <polygon points="150.5,105 199.5,105 207,120 143,120" />
          </g>
        </svg>
      </Link>

      {/* 导航图标 */}
      <nav className="flex flex-col items-center gap-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              title={L(item.label, locale)}
              className={`flex items-center justify-center w-10 h-10 rounded-lg transition-colors ${
                isActive
                  ? "bg-sidebar-accent text-sidebar-primary"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              }`}
            >
              <Icon size={20} />
            </Link>
          );
        })}
      </nav>

      {/* 间隔 */}
      <div className="flex-1" />

      {/* 底部操作区 */}
      <div className="flex flex-col items-center gap-2">
        {/* 语言切换 */}
        <button
          onClick={toggleLocale}
          title={L(t.common.language, locale)}
          className="flex items-center justify-center w-10 h-10 rounded-lg text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
        >
          <Languages size={18} />
        </button>

        {/* 用户头像下拉菜单 */}
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center justify-center w-10 h-10 rounded-lg hover:bg-sidebar-accent transition-colors">
            <Avatar className="h-7 w-7">
              <AvatarFallback className="text-[10px] bg-sidebar-accent text-sidebar-accent-foreground">
                {initials}
              </AvatarFallback>
            </Avatar>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="right" align="end" className="w-48">
            {/* 用户信息 */}
            <div className="px-3 py-2">
              <p className="text-sm font-medium truncate">
                {user?.display_name || user?.email}
              </p>
              {user?.display_name && (
                <p className="text-xs text-muted-foreground truncate">
                  {user.email}
                </p>
              )}
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut size={14} className="mr-2" />
              {L(t.auth.logoutBtn, locale)}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </aside>
  );
}
