/**
 * 移动端顶栏 - 汉堡菜单触发侧边栏 Sheet
 *
 * 仅在 lg 以下断点显示。
 */
"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Menu, LayoutDashboard, LogOut, Languages } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, labelKey: "sidebarDashboard" as const },
];

export function TopBar() {
  const { locale, toggleLocale } = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();

  function handleLogout() {
    logout();
    router.push("/login");
  }

  const initials = user?.display_name
    ? user.display_name.charAt(0).toUpperCase()
    : user?.email?.charAt(0).toUpperCase() ?? "U";

  return (
    <header className="lg:hidden flex items-center justify-between h-14 px-4 border-b border-border bg-background sticky top-0 z-50">
      <Sheet>
        <SheetTrigger render={<Button variant="ghost" size="icon" />}>
            <Menu size={20} />
        </SheetTrigger>
        <SheetContent side="left" className="w-[280px] p-0">
          <div className="flex flex-col h-full">
            {/* Logo */}
            <div className="p-6">
              <svg viewBox="0 0 300 250" className="h-10 w-auto text-foreground">
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
            </div>

            {/* 导航 */}
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

            <Separator />

            {/* 底部操作 */}
            <div className="p-4 space-y-2">
              <div className="flex items-center gap-3 px-3 py-2">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="text-xs">{initials}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {user?.display_name || user?.email}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                className="w-full justify-start gap-2"
                onClick={toggleLocale}
              >
                <Languages size={14} />
                {locale === "zh" ? "English" : "中文"}
              </Button>
              <Button
                variant="ghost"
                className="w-full justify-start gap-2 text-destructive"
                onClick={handleLogout}
              >
                <LogOut size={14} />
                {L(t.auth.logoutBtn, locale)}
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>

      {/* 标题 */}
      <span className="text-sm font-bold">VibeArtifact</span>

      {/* 占位 */}
      <div className="w-10" />
    </header>
  );
}
