/**
 * 侧边栏组件 - 固定宽度 280px
 *
 * 包含 Logo、导航链接、底部用户信息和下拉菜单。
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
  { href: "/dashboard", icon: LayoutDashboard, labelKey: "sidebarDashboard" as const },
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
    <aside className="hidden lg:flex w-[280px] flex-col border-r border-border bg-sidebar h-screen sticky top-0">
      {/* Logo */}
      <div className="p-6">
        <Link href="/dashboard" className="block">
          <svg viewBox="0 0 300 250" className="h-12 w-auto text-foreground">
            <g fill="currentColor">
              <polygon points="85,40 119,108 109,128 65,40" />
              <polygon points="165,40 185,40 235,140 215,140 175,60 125,160 115,140 165,40" />
              <polygon points="150.5,105 199.5,105 207,120 143,120" />
            </g>
            <text
              x="150" y="215"
              fontFamily="'Inter', sans-serif"
              fontSize="32" fontWeight="600"
              letterSpacing="-0.02em"
              textAnchor="middle"
              fill="currentColor"
            >
              VibeArtifact
            </text>
          </svg>
        </Link>
      </div>

      {/* 导航链接 */}
      <nav className="flex-1 px-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
              }`}
            >
              <Icon size={18} />
              {L(t.dashboard[item.labelKey], locale)}
            </Link>
          );
        })}
      </nav>

      {/* 底部用户信息 */}
      <div className="p-4 border-t border-border">
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center gap-3 w-full px-3 py-2 rounded-lg hover:bg-accent/50 transition-colors text-left">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="text-xs">{initials}</AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {user?.display_name || user?.email}
              </p>
              {user?.display_name && (
                <p className="text-xs text-muted-foreground truncate">
                  {user.email}
                </p>
              )}
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            <DropdownMenuItem onClick={toggleLocale}>
              <Languages size={14} className="mr-2" />
              {locale === "zh" ? "English" : "中文"}
            </DropdownMenuItem>
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
